#!/usr/bin/env python3
"""Check deterministic fixtures and scripts; does not run Claude Code or an LLM."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from new_case import LAB_ROOT, VARIANTS, create_case

def run_tests(root):
    return subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=root, text=True, capture_output=True)

with tempfile.TemporaryDirectory(prefix="s07-lab-verify-") as tmp:
    tmp = Path(tmp)
    roots = {}
    for case in ("baseline", "empty-list", "lost-update"):
        root = create_case(tmp / case, "inline", case)
        roots[case] = root
        result = run_tests(root)
        assert (result.returncode == 0) == (case == "baseline"), (case, result.stderr)
        if case == "empty-list":
            assert "IndexError" in result.stderr
        if case == "lost-update":
            assert "1 != 2" in result.stderr
        print("fixture:", case, "expected result confirmed")

    for variant in VARIANTS:
        root = create_case(tmp / ("variant-" + variant), variant, "baseline")
        assert run_tests(root).returncode == 0, variant
        if variant in ("preload", "worktree"):
            assert (root / ".claude/agents/review-worker.md").exists()
        if variant == "worktree":
            assert "isolation: worktree" in (root / ".claude/agents/review-worker.md").read_text()
        try:
            create_case(root)
            raise AssertionError("Existing destination was overwritten")
        except ValueError:
            pass
    print("variants: all fresh projects created without overwriting an existing path")

    root = roots["empty-list"]
    hook = root / ".claude/hooks/skill-hook.py"
    for mode, event, tool in (("guard", "PreToolUse", "Write"),
                             ("guard", "PreToolUse", "Read"),
                             ("once", "PostToolUse", "Read")):
        result = subprocess.run([sys.executable, str(hook), mode],
            input=json.dumps({"hook_event_name": event, "tool_name": tool,
                              "session_id": "offline-check"}),
            text=True, capture_output=True, check=True)
        reply = json.loads(result.stdout)
        if tool == "Write":
            assert reply["hookSpecificOutput"]["permissionDecision"] == "deny"
        if mode == "once":
            assert "additionalContext" in reply["hookSpecificOutput"]
    assert len((root / ".s07-trace/events.jsonl").read_text().splitlines()) == 3
    print("hooks: JSON contract and trace verified; host-managed once is not simulated")

    trace = subprocess.run([sys.executable, str(LAB_ROOT / "tools/trace_inline.py"),
                            str(root), "--caller", "model"],
                           text=True, capture_output=True, check=True)
    phases = [json.loads(line)["phase"] for line in trace.stdout.splitlines()]
    assert phases.index("catalog") < phases.index("body-delivered") < phases.index("resource-read")
    assert phases[-1] == "ready-for-next-model"
    literal_argument = 'src "!' + chr(96) + 'git status --short' + chr(96) + ' $0"'
    literal = subprocess.run([sys.executable, str(LAB_ROOT / "tools/trace_inline.py"),
                              str(root), "--arguments", literal_argument],
                             text=True, capture_output=True, check=True)
    literal_events = [json.loads(line) for line in literal.stdout.splitlines()]
    assert sum(event["phase"] == "render-command" for event in literal_events) == 2
    assert literal_events[0]["application_has_read_file"]
    assert not literal_events[0]["body_visible_to_model"]
    failed = subprocess.run([sys.executable, str(LAB_ROOT / "tools/trace_inline.py"),
                             str(tmp / "variant-render-failure")],
                            text=True, capture_output=True)
    assert failed.returncode != 0
    assert '"phase": "body-delivered"' not in failed.stdout
    print("trace: metadata/body/resources ordering and render failure verified")

print("PASS: local deterministic checks only; model triggering and Claude lifecycle need client observation.")
