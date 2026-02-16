# Mac One-Command AGI Installer (Consent-Based)

This kit installs a local AGI node on **one Mac** with explicit user consent.

## What it does

- Creates isolated workspace and Python venv
- Installs runtime dependencies
- Copies core app files (`boot.py`, `emotion_engine.py`, `soul.py`, `codex_gateway.py`)
- Writes `.env` configuration
- Creates launcher command: `jarvis-node`
- Optionally installs a launchd auto-start service
- Optionally registers node with your hive coordinator by API key

## What it does NOT do

- No autonomous propagation
- No hidden persistence
- No privilege escalation

## Quick start

```bash
cd /Users/aydenzosche/.openclaw/workspace/jarvis_local
chmod +x mac_agi/install.sh mac_agi/uninstall.sh
./mac_agi/install.sh
```

Then run:

```bash
~/.jarvis_local_node/bin/jarvis-node up
```

Check status:

```bash
~/.jarvis_local_node/bin/jarvis-node status
```

Operator ask:

```bash
export JARVIS_OPERATOR_KEY="change_me"
~/.jarvis_local_node/.venv/bin/python ~/.jarvis_local_node/app/codex_gateway.py ask "status"
```

## Optional one-liner pattern

Host this repo and use:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/<you>/<repo>/main/mac_agi/install_remote.sh) \
  --repo-base-url https://raw.githubusercontent.com/<you>/<repo>/main \
  --yes \
  --workspace "$HOME/.jarvis_local_node" \
  --operator-key "change_me" \
  --install-service
```

Only do this over trusted HTTPS with integrity checks.

With coordinator registration:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/<you>/<repo>/main/mac_agi/install_remote.sh) \
  --repo-base-url https://raw.githubusercontent.com/<you>/<repo>/main \
  --yes \
  --workspace "$HOME/.jarvis_local_node" \
  --operator-key "change_me" \
  --install-service \
  --register \
  --coordinator-url "http://127.0.0.1:9000" \
  --coordinator-api-key "<REAL_API_KEY_VALUE>"
```

## Minimal Coordinator

A local coordinator scaffold is included at `mac_agi/coordinator`.

Start it:

```bash
cd /Users/aydenzosche/.openclaw/workspace/jarvis_local/mac_agi/coordinator
python3 generate_api_key.py
cp .env.example .env
# set HIVE_API_KEY in .env
./run.sh
```

Then use installer values:

- Coordinator URL: `http://127.0.0.1:9000`
- Coordinator API key: the `HIVE_API_KEY` from `.env`
