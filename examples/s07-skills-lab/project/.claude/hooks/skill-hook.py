#!/usr/bin/env python3
"""S07.6: command-hook protocol and trace; once is enforced by Claude Code."""
import json
import sys
from pathlib import Path

mode = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    event = json.load(sys.stdin)
    if not isinstance(event, dict):
        raise ValueError("hook input must be a JSON object")
except (ValueError, json.JSONDecodeError) as error:
    print(str(error), file=sys.stderr)
    raise SystemExit(2)

root = Path(__file__).resolve().parents[2]
trace_dir = root / ".s07-trace"
trace_dir.mkdir(exist_ok=True)
record = {
    "mode": mode,
    "event": event.get("hook_event_name"),
    "tool": event.get("tool_name"),
    "session_id": event.get("session_id", "unknown"),
}
with (trace_dir / "events.jsonl").open("a", encoding="utf-8") as output:
    output.write(json.dumps(record, ensure_ascii=False) + "\n")

if mode == "guard" and event.get("hook_event_name") == "PreToolUse":
    if event.get("tool_name") in ("Write", "Edit"):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "S07 lab: this review does not use Write/Edit.",
        }}))
    else:
        print("{}")
elif mode == "once" and event.get("hook_event_name") == "PostToolUse":
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "S07 lab: first successful matching Read observed. Use evidence in the report.",
    }}))
else:
    print("{}")
