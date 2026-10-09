# Repository Guidelines

## Project Structure & Module Organization

This repository is a Chinese-language learning website built with Hugo and the PaperMod theme.

- `content/`: Markdown articles, project chapters, and course notes; page bundles keep JSON metadata and diagrams beside their pages.
- `layouts/`: Hugo templates, partials, and shortcodes that extend the theme.
- `assets/css/extended/` and `assets/js/`: custom styles and browser interactions.
- `examples/` and `static/`: teaching examples, downloadable archives, and directly served resources.
- `tests/`: navigation, diagram, source-excerpt, and browser checks.
- `docs/`: writing rules, design discussions, specifications, and plans.
- `themes/PaperMod/`: Git submodule. Keep site customizations in root-level layouts and assets.

## Build, Test, and Development Commands

Use Hugo Extended **0.166.0**.

- `git submodule update --init --recursive`: initialize PaperMod after cloning.
- `hugo server -D`: preview locally at `http://localhost:1313`, including drafts.
- `hugo --gc --minify`: generate the production site in `public/`.
- `bash tests/test-project-navigation.sh`: build into a temporary directory and check navigation and rendered content.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: run Python checks.
- `python3 examples/s07-skills-lab/tools/verify_lab.py`: validate the Skills Lab.

## Coding Style & Naming Conventions

Match surrounding formatting: generally two spaces in JavaScript, CSS, and templates, and four spaces in conventionally formatted Python. No repository-wide formatter or linter is configured.

Use lowercase, hyphenated content paths and descriptive asset names. Use `_index.md` for section pages and `index.md` for leaf bundles. Keep chapter numbering, titles, navigation labels, and front matter weights consistent. Follow `docs/learn-claude-code-writing-rules.md` for Learn Claude Code content and diagrams; retain source attribution and version boundaries.

## Testing Guidelines

Tests use Bash assertions and Python's standard-library `unittest`; no coverage threshold is configured. Name Python checks `tests/test_<feature>.py`. Add focused regression checks for changed navigation, diagrams, or interactions. Browser checks require Chrome; some source checks require local teaching repositories and skip when unavailable. Review skipped tests and manually verify desktop, narrow-screen, and keyboard behavior for UI changes.

## Commit & Pull Request Guidelines

History uses prefixes such as `docs:`, `feat:`, and `chore:` followed by a concise description. Keep commits focused. PRs should explain the change, identify affected pages, link relevant issues or design records, report validation and skips, and include screenshots for visual changes.

## Generated Files & Publishing

Keep generated `public/`, `resources/_gen/`, and Hugo lock files out of commits. Treat `bash deploy.sh` as an explicit publishing action: it rebuilds the site and force-pushes `gh-pages`.
