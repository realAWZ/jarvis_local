#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-$HOME/.jarvis_local_node}"
PLIST="$HOME/Library/LaunchAgents/com.jarvis.local.node.plist"

echo "This will remove the local node workspace at: $WORKSPACE"
read -r -p "Type DELETE to confirm: " CONFIRM
if [[ "$CONFIRM" != "DELETE" ]]; then
  echo "Cancelled."
  exit 0
fi

launchctl unload "$PLIST" >/dev/null 2>&1 || true
rm -f "$PLIST"
pkill -f "boot.py" >/dev/null 2>&1 || true

rm -rf "$WORKSPACE"

echo "Uninstall complete."
