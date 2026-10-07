#!/usr/bin/env python3
"""S07.9 teaching trace. No LLM, SDK, permissions engine, or fork scheduler."""
import argparse
import json
import re
import shlex
import subprocess
from pathlib import Path

ALLOWED_INJECTIONS = (
    ("git", "status", "--short"),
    ("git", "diff", "HEAD"),
    ("git", "diff", "refs/heads/s07-missing"),
)

def emit(phase, **data):
    print(json.dumps({"simulation": True, "phase": phase, **data}, ensure_ascii=False))

def trace(root, arguments, caller, resource):
    root = Path(root).resolve()
    if not (root / ".s07-skill-lab").exists():
        raise ValueError("Not an S07 fixture.")
    skill_dir = root / ".claude/skills/review-diff"
    raw = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    _, header, body = raw.split("---", 2)
    if "context: fork" in header:
        raise ValueError("This trace demonstrates inline only; observe fork in Claude Code.")
    # Only extract two scalar fields from our fixed fixture, not a general YAML parser.
    catalog = {}
    for line in header.splitlines():
        key, separator, value = line.partition(":")
        if separator and key in ("name", "description"):
            catalog[key] = value.strip()
    emit("catalog", model_visible=catalog, body_visible_to_model=False,
         application_has_read_file=True)
    emit("invoke", caller=caller, name="review-diff", arguments=arguments)
    if caller == "model" and "disable-model-invocation: true" in header:
        emit("blocked", reason="Fixture marks the skill manual-only.")
        return
    if caller == "user" and "user-invocable: false" in header:
        emit("blocked", reason="Fixture marks the skill model-only.")
        return

    # Process only tokens in the source template; inserted data is not re-scanned.
    # This is the fixture's renderer, not every Claude Code substitution rule.
    values = shlex.split(arguments)

    def render_token(match):
        if match.group(1) is not None:
            command = tuple(shlex.split(match.group(1)))
            if command not in ALLOWED_INJECTIONS:
                raise ValueError("Trace only executes the fixture's fixed Git commands.")
            result = subprocess.run(command, cwd=root, text=True, capture_output=True)
            emit("render-command", command=list(command), exit_code=result.returncode)
            if result.returncode:
                raise ValueError("Rendering stopped; body was not delivered.")
            return result.stdout.rstrip()
        if match.group(2):
            return str(skill_dir if match.group(2) == "SKILL" else root)
        if match.group(0) == "$ARGUMENTS":
            return arguments
        index = int(match.group(3))
        return values[index] if index < len(values) else match.group(0)

    body = re.sub(
        r"!\x60([^\x60\n]+)\x60|\$\{CLAUDE_(SKILL|PROJECT)_DIR\}|\$ARGUMENTS|\$(\d+)",
        render_token, body,
    )
    messages = []
    if caller == "model":
        messages.append({"role": "assistant", "tool_use_id": "skill-1",
                         "tool": "Skill", "input": {"name": "review-diff"}})
        messages.append({"role": "user", "tool_result_for": "skill-1",
                         "content": "Skill loaded"})
    messages.append({"kind": "skill-instructions", "content": body})
    emit("body-delivered", instructions_once=True, messages=messages)

    reference = skill_dir / "references" / (
        "concurrency.md" if resource == "concurrency" else "input-boundaries.md")
    emit("resource-read", file=str(reference.relative_to(root)),
         content=reference.read_text(encoding="utf-8"))
    result = subprocess.run(["bash", str(skill_dir / "scripts/inspect-diff.sh")],
                            cwd=root, text=True, capture_output=True, check=True)
    emit("ordinary-tool-result", tool="Bash", content=result.stdout)
    emit("ready-for-next-model", generated_report=False,
         note="Role labels are explanatory; this is not the Claude Code message protocol.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--arguments", default="src empty-input")
    parser.add_argument("--caller", choices=("user", "model"), default="user")
    parser.add_argument("--resource", choices=("input", "concurrency"), default="input")
    args = parser.parse_args()
    try:
        trace(args.root, args.arguments, args.caller, args.resource)
    except (ValueError, subprocess.CalledProcessError) as error:
        emit("error", detail=str(error), generated_report=False)
        raise SystemExit(1)
