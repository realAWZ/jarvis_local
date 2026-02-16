#!/usr/bin/env python3
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

DB_PATH = os.environ.get("HIVE_DB_PATH", os.path.expanduser("~/.jarvis_hive/coordinator.db"))
API_KEY = os.environ.get("HIVE_API_KEY", "")
HOST = os.environ.get("HIVE_HOST", "0.0.0.0")
PORT = int(os.environ.get("HIVE_PORT", "9000"))

app = FastAPI(title="Jarvis Hive Coordinator", version="0.1.0")


class RegisterNodeRequest(BaseModel):
    node_id: str = Field(min_length=1)
    node_label: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    workspace: str = Field(min_length=1)
    capabilities: List[str] = Field(default_factory=list)
    consent: Dict[str, Any] = Field(default_factory=dict)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            node_id TEXT UNIQUE NOT NULL,
            node_label TEXT NOT NULL,
            platform TEXT NOT NULL,
            workspace TEXT NOT NULL,
            capabilities_json TEXT NOT NULL,
            consent_json TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _require_api_key(authorization: Optional[str]) -> None:
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Coordinator misconfigured: HIVE_API_KEY missing")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.on_event("startup")
def startup() -> None:
    _init_db()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": "hive-coordinator", "db_path": DB_PATH}


@app.post("/api/v1/nodes/register")
def register_node(item: RegisterNodeRequest, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _require_api_key(authorization)

    now = _utc_now()
    conn = _connect()
    row = conn.execute("SELECT id FROM nodes WHERE node_id = ?", (item.node_id,)).fetchone()
    if row:
        node_pk = row["id"]
        conn.execute(
            """
            UPDATE nodes
            SET node_label = ?, platform = ?, workspace = ?, capabilities_json = ?,
                consent_json = ?, status = ?, updated_at = ?, last_seen_at = ?
            WHERE node_id = ?
            """,
            (
                item.node_label,
                item.platform,
                item.workspace,
                str(item.capabilities),
                str(item.consent),
                "active",
                now,
                now,
                item.node_id,
            ),
        )
    else:
        node_pk = f"node_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO nodes (id, node_id, node_label, platform, workspace, capabilities_json,
                               consent_json, status, created_at, updated_at, last_seen_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_pk,
                item.node_id,
                item.node_label,
                item.platform,
                item.workspace,
                str(item.capabilities),
                str(item.consent),
                "active",
                now,
                now,
                now,
            ),
        )
    conn.commit()
    conn.close()

    return {
        "ok": True,
        "node": {
            "id": node_pk,
            "node_id": item.node_id,
            "status": "active",
            "updated_at": now,
        },
    }


@app.get("/api/v1/nodes")
def list_nodes(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _require_api_key(authorization)
    conn = _connect()
    rows = conn.execute(
        "SELECT id, node_id, node_label, platform, workspace, status, last_seen_at, updated_at FROM nodes ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return {"ok": True, "nodes": [dict(r) for r in rows]}


@app.post("/api/v1/nodes/{node_id}/heartbeat")
def heartbeat(node_id: str, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _require_api_key(authorization)
    now = _utc_now()
    conn = _connect()
    updated = conn.execute(
        "UPDATE nodes SET last_seen_at = ?, updated_at = ?, status = 'active' WHERE node_id = ?",
        (now, now, node_id),
    ).rowcount
    conn.commit()
    conn.close()
    if updated == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"ok": True, "node_id": node_id, "last_seen_at": now}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
