# Minimal Hive Coordinator (macOS/local)

This service provides a minimal coordinator for node enrollment.

## Features

- API-key protected node registration
- Node listing
- Heartbeat updates
- SQLite storage

## Quick start

```bash
cd /Users/aydenzosche/.openclaw/workspace/jarvis_local/mac_agi/coordinator
python3 generate_api_key.py
cp .env.example .env
# paste generated key into HIVE_API_KEY in .env
chmod +x run.sh
./run.sh
```

Coordinator URL to use in installer:

- `http://127.0.0.1:9000`

## Test

```bash
curl -s http://127.0.0.1:9000/health

curl -s http://127.0.0.1:9000/api/v1/nodes \
  -H "Authorization: Bearer <HIVE_API_KEY>"
```

## Installer integration

When running `mac_agi/install.sh`, enter:

- Coordinator URL: `http://127.0.0.1:9000`
- Coordinator API key: value from `.env` (`HIVE_API_KEY`)
