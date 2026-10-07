#!/usr/bin/env bash
set -euo pipefail
# S07.5: execute this file; its source is not automatically injected.
git rev-parse --show-toplevel
git status --short
git diff HEAD
printf '\nUntracked paths (contents are not read automatically):\n'
git ls-files --others --exclude-standard
