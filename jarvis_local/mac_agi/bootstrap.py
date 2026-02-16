#!/usr/bin/env python3
import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

REQUIRED_APP_FILES = [
    "boot.py",
    "emotion_engine.py",
    "soul.py",
    "codex_gateway.py",
]


def run(cmd, check=True, capture=False):
    print(f"[bootstrap] $ {' '.join(cmd)}")
    if capture:
        return subprocess.run(cmd, check=check, text=True, capture_output=True)
    return subprocess.run(cmd, check=check)


def ensure_macos():
    if platform.system().lower() != "darwin":
        raise RuntimeError("This installer currently supports macOS only.")


def ensure_python():
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10+ is required.")


def copy_app_files(src_root: Path, app_dir: Path):
    app_dir.mkdir(parents=True, exist_ok=True)
    missing = []
    for fname in REQUIRED_APP_FILES:
        src = src_root / fname
        if not src.exists():
            missing.append(str(src))
            continue
        shutil.copy2(src, app_dir / fname)
    if missing:
        raise RuntimeError("Missing required files:\n" + "\n".join(missing))


def create_venv(workspace: Path):
    venv_dir = workspace / ".venv"
    if not venv_dir.exists():
        run([sys.executable, "-m", "venv", str(venv_dir)])
    pip = venv_dir / "bin" / "pip"
    py = venv_dir / "bin" / "python"
    run([str(py), "-m", "pip", "install", "--upgrade", "pip", "wheel", "setuptools"])
    return venv_dir, py, pip


def install_dependencies(pip_bin: Path, req_file: Path):
    run([str(pip_bin), "install", "-r", str(req_file)])


def write_env_file(workspace: Path, env_map: dict):
    env_path = workspace / ".env"
    lines = [f"{k}={v}" for k, v in env_map.items()]
    env_path.write_text("\n".join(lines) + "\n")
    return env_path


def load_env_file(path: Path):
    env = {}
    if not path.exists():
        return env
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def create_launcher(workspace: Path, app_dir: Path, venv_python: Path):
    bin_dir = workspace / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    script = bin_dir / "jarvis-node"
    content = f"""#!/usr/bin/env bash
set -euo pipefail
WS=\"{workspace}\"
APP=\"{app_dir}\"
PY=\"{venv_python}\"

if [[ $# -lt 1 ]]; then
  echo "Usage: jarvis-node <up|status|ask|trace|live|down> [args...]"
  exit 1
fi

CMD="$1"
shift || true

if [[ -f "$WS/.env" ]]; then
  set -a
  source "$WS/.env"
  set +a
fi

export JARVIS_WORKSPACE="${{JARVIS_WORKSPACE:-$WS/workspace}}"
mkdir -p "$JARVIS_WORKSPACE"

case "$CMD" in
  up)
    exec "$PY" "$APP/boot.py"
    ;;
  status)
    exec curl -s http://127.0.0.1:8000/status
    ;;
  ask)
    exec "$PY" "$APP/codex_gateway.py" ask "$@"
    ;;
  trace)
    exec "$PY" "$APP/codex_gateway.py" trace "$@"
    ;;
  live)
    exec "$PY" "$APP/codex_gateway.py" live "$@"
    ;;
  down)
    launchctl unload "$HOME/Library/LaunchAgents/com.jarvis.local.node.plist" || true
    pkill -f "boot.py" || true
    ;;
  *)
    echo "Unknown command: $CMD"
    exit 1
    ;;
esac
"""
    script.write_text(content)
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return script


def write_launch_agent(workspace: Path, launcher_path: Path):
    agents_dir = Path.home() / "Library" / "LaunchAgents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    plist_path = agents_dir / "com.jarvis.local.node.plist"
    log_dir = workspace / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    plist = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
  <key>Label</key>
  <string>com.jarvis.local.node</string>
  <key>ProgramArguments</key>
  <array>
    <string>{launcher_path}</string>
    <string>up</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>{log_dir / 'launchd.out.log'}</string>
  <key>StandardErrorPath</key>
  <string>{log_dir / 'launchd.err.log'}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
  </dict>
</dict>
</plist>
"""
    plist_path.write_text(plist)
    return plist_path


def coordinator_register(workspace: Path, env_map: dict):
    base = env_map.get("HIVE_COORDINATOR_URL", "").strip()
    key = env_map.get("HIVE_API_KEY", "").strip()
    if not base or not key:
        print("[bootstrap] Coordinator registration skipped (missing HIVE_COORDINATOR_URL/HIVE_API_KEY).")
        return

    node_id_file = workspace / "node_id.txt"
    if node_id_file.exists():
        node_id = node_id_file.read_text().strip()
    else:
        node_id = f"mac-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        node_id_file.write_text(node_id)

    payload = {
        "node_id": node_id,
        "node_label": env_map.get("NODE_LABEL", platform.node() or "mac-node"),
        "platform": "macOS",
        "workspace": str(workspace),
        "capabilities": ["local-agi", "gateway", "operator"],
        "consent": {
            "installer_opt_in": True,
            "no_self_propagation": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }
    url = base.rstrip("/") + "/api/v1/nodes/register"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    print(f"[bootstrap] Registering node with coordinator: {url}")
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code >= 300:
            raise RuntimeError(f"Coordinator registration failed: {resp.status_code} {resp.text[:300]}")
        (workspace / "coordinator_registration.json").write_text(json.dumps(resp.json(), indent=2))
        print("[bootstrap] Coordinator registration successful.")
    except Exception as exc:
        pending = {
            "url": url,
            "payload": payload,
            "error": str(exc),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        (workspace / "coordinator_registration_pending.json").write_text(json.dumps(pending, indent=2))
        print(f"[bootstrap] WARNING: coordinator registration skipped for now: {exc}")
        print("[bootstrap] Saved retry payload to coordinator_registration_pending.json")


def parse_args():
    parser = argparse.ArgumentParser(description="Consent-based macOS AGI bootstrap")
    parser.add_argument("--source", required=True, help="Source project directory containing boot.py")
    parser.add_argument("--workspace", default=str(Path.home() / ".jarvis_local_node"))
    parser.add_argument("--operator-key", default="change_me")
    parser.add_argument("--model", default="deepseek-r1:1.5b")
    parser.add_argument("--fallback-models", default="gemma3:4b,deepseek-r1:7b")
    parser.add_argument("--install-service", action="store_true")
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--skip-deps", action="store_true")
    parser.add_argument("--coordinator-url", default="")
    parser.add_argument("--coordinator-api-key", default="")
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_macos()
    ensure_python()

    src_root = Path(args.source).resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    app_dir = workspace / "app"
    workspace.mkdir(parents=True, exist_ok=True)

    copy_app_files(src_root, app_dir)

    venv_dir, py, pip = create_venv(workspace)
    if not args.skip_deps:
        install_dependencies(pip, src_root / "mac_agi" / "requirements-mac.txt")

    env_map = {
        "JARVIS_WORKSPACE": str(workspace / "workspace"),
        "JARVIS_MODEL": args.model,
        "JARVIS_FALLBACK_MODELS": args.fallback_models,
        "JARVIS_AUTONOMOUS_ENABLED": "false",
        "JARVIS_AUTONOMOUS_INTERVAL_SEC": "60",
        "JARVIS_OPERATOR_KEY": args.operator_key,
        "JARVIS_BASE_URL": "http://127.0.0.1:8000",
        "HIVE_COORDINATOR_URL": args.coordinator_url,
        "HIVE_API_KEY": args.coordinator_api_key,
        "NODE_LABEL": platform.node() or "mac-node",
    }

    env_path = write_env_file(workspace, env_map)
    launcher = create_launcher(workspace, app_dir, py)

    if args.install_service:
        plist = write_launch_agent(workspace, launcher)
        run(["launchctl", "bootout", f"gui/{os.getuid()}", str(plist)], check=False)
        run(["launchctl", "load", str(plist)])
        print(f"[bootstrap] launchd service installed: {plist}")

    if args.register:
        merged_env = load_env_file(env_path)
        coordinator_register(workspace, merged_env)

    print("\n[bootstrap] Complete.")
    print(f"Workspace: {workspace}")
    print(f"Launcher: {launcher}")
    print("Run locally:")
    print(f"  {launcher} up")
    print(f"  {launcher} status")
    print(f"  {launcher} ask \"status update\"")


if __name__ == "__main__":
    main()
