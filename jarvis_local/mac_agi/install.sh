#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BOOTSTRAP="$SCRIPT_DIR/bootstrap.py"
DEFAULT_WORKSPACE="$HOME/.jarvis_local_node"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[install] macOS is required."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[install] python3 not found. Install Python 3.10+ and retry."
  exit 1
fi

echo "This installer sets up a local AGI node on this Mac."
echo "It does NOT self-propagate and does NOT escalate privileges."
echo
read -r -p "Proceed with installation on this host? (yes/no): " CONSENT
if [[ "$CONSENT" != "yes" ]]; then
  echo "[install] Cancelled."
  exit 0
fi

read -r -p "Workspace directory [$DEFAULT_WORKSPACE]: " WORKSPACE_INPUT
WORKSPACE="${WORKSPACE_INPUT:-$DEFAULT_WORKSPACE}"
if [[ "$WORKSPACE" == "yes" || "$WORKSPACE" == "no" ]]; then
  echo "[install] '$WORKSPACE' looks like a yes/no response, not a path. Using default: $DEFAULT_WORKSPACE"
  WORKSPACE="$DEFAULT_WORKSPACE"
fi

read -r -p "Set operator key now? (leave blank for change_me): " OP_KEY
OP_KEY="${OP_KEY:-change_me}"

read -r -p "Install launchd service for auto-start? (yes/no): " SERVICE_CHOICE
SERVICE_FLAG=""
if [[ "$SERVICE_CHOICE" == "yes" ]]; then
  SERVICE_FLAG="--install-service"
fi

read -r -p "Register with hive coordinator now? (yes/no): " REGISTER_CHOICE
REGISTER_FLAG=""
COORD_ARGS=()
if [[ "$REGISTER_CHOICE" == "yes" ]]; then
  REGISTER_FLAG="--register"
  read -r -p "Coordinator URL (e.g. https://coord.example.com): " COORD_URL
  read -r -p "Coordinator API key: " COORD_KEY
  if [[ "$COORD_KEY" == "HIVE_API_KEY" ]]; then
    echo "[install] You entered the literal string 'HIVE_API_KEY'."
    echo "[install] Enter the actual token value from coordinator/.env instead."
    read -r -p "Coordinator API key (actual value): " COORD_KEY
  fi
  COORD_ARGS+=("--coordinator-url" "$COORD_URL" "--coordinator-api-key" "$COORD_KEY")
fi

python3 "$BOOTSTRAP" \
  --source "$PROJECT_ROOT" \
  --workspace "$WORKSPACE" \
  --operator-key "$OP_KEY" \
  $SERVICE_FLAG \
  $REGISTER_FLAG \
  "${COORD_ARGS[@]}"

echo
echo "[install] Done."
echo "Use: $WORKSPACE/bin/jarvis-node up"
echo "Use: $WORKSPACE/bin/jarvis-node live"
