#!/usr/bin/env python3
"""Create a fresh, disposable repo; never overwrite an existing directory."""
import argparse
import shutil
import subprocess
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("inline", "manual", "model-only", "fork-wait", "fork-background",
            "preload", "worktree", "render-failure")
CASES = ("baseline", "empty-list", "lost-update")

def create_case(destination, variant="inline", case="empty-list"):
    destination = Path(destination).expanduser().resolve()
    if destination.exists():
        raise ValueError("Destination already exists; choose a new directory.")
    if destination.is_relative_to(LAB_ROOT):
        raise ValueError("Create exercises outside the example source directory.")
    if variant not in VARIANTS or case not in CASES:
        raise ValueError("Unknown variant or fixture.")
    shutil.copytree(LAB_ROOT / "project", destination,
                    ignore=shutil.ignore_patterns("__pycache__", ".s07-trace"))
    skill = destination / ".claude/skills/review-diff/SKILL.md"
    if variant != "inline":
        source_variant = "preload" if variant == "worktree" else variant
        shutil.copyfile(LAB_ROOT / "variants" / source_variant / "SKILL.md", skill)
    if variant in ("preload", "worktree"):
        agents = destination / ".claude/agents"
        agents.mkdir(exist_ok=True)
        shutil.copyfile(LAB_ROOT / "variants" / variant / "review-worker.md",
                        agents / "review-worker.md")

    git = ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
           "-c", "user.name=S07 Skills Lab", "-c", "user.email=skills-lab@example.invalid"]
    for args in (["init", "-q", "-b", "main"], ["add", "--force", "."],
                 ["commit", "-qm", "S07 fixture baseline"]):
        subprocess.run(git + args, cwd=destination, check=True,
                       capture_output=True, text=True)

    if case == "empty-list":
        (destination / "src/normalize.py").write_text(
            'def normalize_first(items):\n'
            '    """Contract: an empty input returns an empty string."""\n'
            '    return items[0].strip()\n', encoding="utf-8")
    elif case == "lost-update":
        (destination / "src/counter.py").write_text(
            'import asyncio\n\n'
            'async def increment(state):\n'
            '    """Two completed increments must add two."""\n'
            '    old = state["count"]\n'
            '    await asyncio.sleep(0)\n'
            '    state["count"] = old + 1\n', encoding="utf-8")

    (destination / "untracked-note.txt").write_text(
        "Untracked fixture marker. git diff HEAD does not show this file's content.\n",
        encoding="utf-8")
    return destination

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--variant", choices=VARIANTS, default="inline")
    parser.add_argument("--case", choices=CASES, default="empty-list")
    args = parser.parse_args()
    try:
        root = create_case(args.destination, args.variant, args.case)
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + "\n")
    print(root)
    print("Next: cd into this directory, then start a fresh Claude Code session.")
