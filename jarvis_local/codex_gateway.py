import argparse
import json
import os
import sys
import time
from datetime import datetime

import requests


BASE_URL = os.environ.get("JARVIS_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
OPERATOR_KEY = os.environ.get("JARVIS_OPERATOR_KEY", "").strip()
DEFAULT_TIMEOUT = int(os.environ.get("JARVIS_OPERATOR_TIMEOUT", "45"))


def _headers():
    headers = {"Content-Type": "application/json"}
    if OPERATOR_KEY:
        headers["X-Operator-Key"] = OPERATOR_KEY
    return headers


def _get(path, params=None):
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, params=params or {}, headers=_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()


def _post(path, payload):
    url = f"{BASE_URL}{path}"
    resp = requests.post(url, json=payload, headers=_headers(), timeout=DEFAULT_TIMEOUT + 20)
    resp.raise_for_status()
    return resp.json()


def cmd_state(_args):
    print(json.dumps(_get("/operator/state"), indent=2))


def cmd_emotions(_args):
    print(json.dumps(_get("/operator/emotions"), indent=2))


def cmd_trace(args):
    payload = _get("/operator/trace", {"after_id": args.after_id, "limit": args.limit})
    print(json.dumps(payload, indent=2))


def cmd_thoughts(args):
    payload = _get("/operator/thoughts", {"after_id": args.after_id, "limit": args.limit})
    print(json.dumps(payload, indent=2))


def cmd_ask(args):
    payload = {
        "sender": "CODEX",
        "mode": args.mode,
        "message": args.message,
        "wait_for_reply": True,
        "timeout_sec": args.timeout,
    }
    print(json.dumps(_post("/operator/message", payload), indent=2))


def cmd_live(_args):
    print(json.dumps(_get("/operator/live"), indent=2))


def cmd_watch(args):
    trace_id = 0
    thought_id = 0
    msg_id = 0
    print(f"[{datetime.utcnow().isoformat()}Z] Watching {BASE_URL} ...")
    while True:
        payload = _get(
            "/operator/live",
            {
                "after_trace_id": trace_id,
                "after_thought_id": thought_id,
                "after_message_id": msg_id,
            },
        )
        state = payload.get("state", {})
        emotions = payload.get("emotions", {})
        if args.print_state:
            print(
                f"STATE mood={state.get('mood')} energy={state.get('energy')} "
                f"model={state.get('last_model_used')} queue={state.get('queue_depth')}"
            )
            print(f"EMOTION drives={emotions.get('drives', {})}")

        for item in payload.get("trace", []):
            trace_id = max(trace_id, item.get("id", 0))
            print(f"TRACE[{item.get('id')}] {item.get('event')}: {item.get('detail')}")

        for item in payload.get("thoughts", []):
            thought_id = max(thought_id, item.get("id", 0))
            preview = (item.get("raw") or "").replace("\n", " ")[:200]
            print(f"THOUGHT[{item.get('id')}] mode={item.get('mode')} model={item.get('model')}: {preview}")

        for item in payload.get("messages", []):
            msg_id = max(msg_id, item.get("id", 0))
            print(f"MSG[{item.get('id')}] {item.get('role')}: {item.get('text')}")

        sys.stdout.flush()
        time.sleep(args.interval)


def build_parser():
    parser = argparse.ArgumentParser(description="Codex operator gateway for JARVIS")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("state", help="Show operator state")
    p.set_defaults(func=cmd_state)

    p = sub.add_parser("emotions", help="Show full emotional state")
    p.set_defaults(func=cmd_emotions)

    p = sub.add_parser("trace", help="Get trace events")
    p.add_argument("--after-id", type=int, default=0)
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_trace)

    p = sub.add_parser("thoughts", help="Get thought stream")
    p.add_argument("--after-id", type=int, default=0)
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_thoughts)

    p = sub.add_parser("ask", help="Send operator message")
    p.add_argument("message", help="Message to send")
    p.add_argument("--mode", default="operator_assist")
    p.add_argument("--timeout", type=int, default=45)
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("live", help="One-shot live aggregate snapshot")
    p.set_defaults(func=cmd_live)

    p = sub.add_parser("watch", help="Continuously watch trace/thoughts/messages")
    p.add_argument("--interval", type=float, default=2.0)
    p.add_argument("--print-state", action="store_true")
    p.set_defaults(func=cmd_watch)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
