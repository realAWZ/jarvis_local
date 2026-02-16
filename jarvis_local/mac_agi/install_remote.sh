#!/usr/bin/env bash
set -euo pipefail

# One-line macOS installer entrypoint for remote distribution.
# Example:
# bash <(curl -fsSL https://raw.githubusercontent.com/<org>/<repo>/main/mac_agi/install_remote.sh) \
#   --repo-base-url https://raw.githubusercontent.com/<org>/<repo>/main \
#   --yes --workspace "$HOME/.jarvis_local_node" --operator-key "change_me" --install-service

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[remote-install] macOS is required."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[remote-install] python3 not found. Install Python 3.10+ and retry."
  exit 1
fi

REPO_BASE_URL=""
WORKSPACE="$HOME/.jarvis_local_node"
OPERATOR_KEY="change_me"
MODEL="deepseek-r1:1.5b"
FALLBACK_MODELS="gemma3:4b,deepseek-r1:7b"
INSTALL_SERVICE=false
REGISTER=false
YES=false
COORDINATOR_URL=""
COORDINATOR_API_KEY=""
SKIP_DEPS=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-base-url)
      REPO_BASE_URL="$2"; shift 2 ;;
    --workspace)
      WORKSPACE="$2"; shift 2 ;;
    --operator-key)
      OPERATOR_KEY="$2"; shift 2 ;;
    --model)
      MODEL="$2"; shift 2 ;;
    --fallback-models)
      FALLBACK_MODELS="$2"; shift 2 ;;
    --coordinator-url)
      COORDINATOR_URL="$2"; shift 2 ;;
    --coordinator-api-key)
      COORDINATOR_API_KEY="$2"; shift 2 ;;
    --install-service)
      INSTALL_SERVICE=true; shift ;;
    --register)
      REGISTER=true; shift ;;
    --skip-deps)
      SKIP_DEPS=true; shift ;;
    --yes)
      YES=true; shift ;;
    *)
      echo "[remote-install] Unknown arg: $1"
      exit 1 ;;
  esac
done

if [[ -z "$REPO_BASE_URL" ]]; then
  echo "[remote-install] Missing required --repo-base-url"
  exit 1
fi

if [[ "$YES" != "true" ]]; then
  echo "This installer will set up a local AGI node on this Mac."
  echo "It is consent-based and does not self-propagate."
  read -r -p "Proceed? (yes/no): " CONSENT
  if [[ "$CONSENT" != "yes" ]]; then
    echo "Cancelled."
    exit 0
  fi
fi

TMP_DIR="$(mktemp -d)"
SRC_DIR="$TMP_DIR/src"
mkdir -p "$SRC_DIR/mac_agi"
trap 'rm -rf "$TMP_DIR"' EXIT

fetch() {
  local rel="$1"
  local dst="$2"
  local url="$REPO_BASE_URL/$rel"
  echo "[remote-install] downloading $url"
  curl -fsSL "$url" -o "$dst"
}

# Core app files
fetch "boot.py" "$SRC_DIR/boot.py"
fetch "emotion_engine.py" "$SRC_DIR/emotion_engine.py"
fetch "soul.py" "$SRC_DIR/soul.py"
fetch "codex_gateway.py" "$SRC_DIR/codex_gateway.py"

# Installer support files
fetch "mac_agi/bootstrap.py" "$SRC_DIR/mac_agi/bootstrap.py"
fetch "mac_agi/requirements-mac.txt" "$SRC_DIR/mac_agi/requirements-mac.txt"

BOOTSTRAP_ARGS=(
  --source "$SRC_DIR"
  --workspace "$WORKSPACE"
  --operator-key "$OPERATOR_KEY"
  --model "$MODEL"
  --fallback-models "$FALLBACK_MODELS"
)

if [[ "$INSTALL_SERVICE" == "true" ]]; then
  BOOTSTRAP_ARGS+=(--install-service)
fi
if [[ "$REGISTER" == "true" ]]; then
  BOOTSTRAP_ARGS+=(--register --coordinator-url "$COORDINATOR_URL" --coordinator-api-key "$COORDINATOR_API_KEY")
fi
if [[ "$SKIP_DEPS" == "true" ]]; then
  BOOTSTRAP_ARGS+=(--skip-deps)
fi

python3 "$SRC_DIR/mac_agi/bootstrap.py" "${BOOTSTRAP_ARGS[@]}"

echo "[remote-install] complete"
echo "Use: $WORKSPACE/bin/jarvis-node up"
