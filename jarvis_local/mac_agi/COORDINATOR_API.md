# Hive Coordinator API (Node Enrollment)

## Register Node

`POST /api/v1/nodes/register`

Headers:
- `Authorization: Bearer <HIVE_API_KEY>`
- `Content-Type: application/json`

Request body:

```json
{
  "node_id": "mac-20260216103000",
  "node_label": "Aydens-MacBook-Air",
  "platform": "macOS",
  "workspace": "/Users/example/.jarvis_local_node",
  "capabilities": ["local-agi", "gateway", "operator"],
  "consent": {
    "installer_opt_in": true,
    "no_self_propagation": true,
    "timestamp": "2026-02-16T15:00:00Z"
  }
}
```

Response example:

```json
{
  "ok": true,
  "node": {
    "id": "node_abc123",
    "node_id": "mac-20260216103000",
    "status": "active"
  }
}
```
