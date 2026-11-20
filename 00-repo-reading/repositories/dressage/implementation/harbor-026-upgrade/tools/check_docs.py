"""Verify upgrade navigation, versioned handoffs and quoted evidence."""

import argparse
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from textwrap import dedent
from urllib.parse import unquote, urlsplit

from check_usage import check_usage, usage_excerpts


@lru_cache(maxsize=None)
def tagged_source(checkout: Path, tag: str, path: str) -> str:
    return subprocess.check_output(["git", "-C", str(checkout), "show", f"{tag}:{path}"], text=True)


def check_fragment(content: str, fragment: str) -> str | None:
    lines = re.fullmatch(r"L(\d+)(?:-L(\d+))?", fragment)
    if lines:
        rows = content.splitlines()
        first = int(lines[1])
        last = int(lines[2] or first)
        if not 1 <= first <= last <= len(rows):
            raise ValueError(f"source line out of range: {fragment}")
        return dedent("\n".join(rows[first - 1:last]))
    if fragment and f'id="{fragment}"' not in content:
        raise ValueError(f"missing anchor: {fragment}")
    return None


def investigation_excerpts(content: str) -> dict[str, list[str]]:
    section = content.partition("## 两边的源码原文\n")[2].partition("## 处理与验收\n")[0]
    if not section:
        raise ValueError("missing investigation evidence section")
    excerpts: dict[str, list[str]] = {}
    for fence in re.finditer(r"^```[^\n]*\n(.*?)\n```$", section, re.MULTILINE | re.DOTALL):
        caption = section[:fence.start()].rstrip().split("\n")[-1]
        citation = re.search(r"\[[^\]\n]+\]\(([^)\n]+#L\d+(?:-L\d+)?)\)$", caption)
        if not citation:
            raise ValueError(f"excerpt needs its source line range: {caption}")
        excerpts.setdefault(citation[1], []).append(fence[1])
    return excerpts


def check(root: Path, harbor_repo: Path | None, dressage_repo: Path | None, slime_repo: Path | None = None) -> None:
    usage_pages = check_usage(root)
    index = (root / "README.md").read_text()
    investigations = sorted((root / "investigations").glob("*/README.md"))
    prs = sorted((root / "prs").glob("*/README.md"))
    if not investigations or not prs:
        raise ValueError("the index needs investigation and PR pages")
    for entry in investigations + prs:
        if f"({entry.relative_to(root).as_posix()})" not in index:
            raise ValueError(f"page not linked from index: {entry.relative_to(root)}")
    checked = 0
    verified_excerpts = {"local": 0, "git": 0}
    skipped_git_excerpts = 0
    repositories = {
        "harbor-framework/harbor": harbor_repo,
        "Accio-Lab/Dressage": dressage_repo,
        "THUDM/slime": slime_repo,
    }
    sources = {name: 0 for name in repositories}
    for page in sorted(root.rglob("*.md")):
        content = page.read_text()
        try:
            if page in investigations:
                excerpts = investigation_excerpts(content)
            elif page in usage_pages:
                excerpts = usage_excerpts(content)
            else:
                excerpts = {}
        except ValueError as exc:
            raise SystemExit(f"{page.relative_to(root)}: {exc}") from exc
        for link in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", content):
            url = urlsplit(link)
            try:
                selected = None
                quotes = excerpts.pop(link, [])
                if not url.scheme:
                    target = (page.parent / unquote(url.path)).resolve() if url.path else page
                    if not target.exists():
                        raise ValueError("missing local target")
                    if url.fragment:
                        selected = check_fragment(target.read_text(), url.fragment)
                    checked += 1
                    kind = "local"
                else:
                    source = re.fullmatch(r"/([^/]+/[^/]+)/(?:blob|tree)/([^/]+)/(.+)", url.path)
                    if url.netloc != "github.com" or not source or source[1] not in repositories:
                        if quotes:
                            raise ValueError("excerpt must cite a recorded file or source checkout")
                        continue
                    checkout = repositories[source[1]]
                    if checkout is None:
                        skipped_git_excerpts += len(quotes)
                        continue
                    selected = check_fragment(tagged_source(checkout, source[2], source[3]), url.fragment)
                    sources[source[1]] += 1
                    kind = "git"
                for quote in quotes:
                    if quote != selected:
                        raise ValueError("excerpt differs from its cited lines")
                    verified_excerpts[kind] += 1
            except (OSError, ValueError, subprocess.CalledProcessError) as exc:
                raise SystemExit(f"{page.relative_to(root)}: {link}: {exc}") from exc
    print(f"{len(investigations)} investigation folders and {len(prs)} PR folders indexed; {checked} local links checked")
    print(f"{len(investigations)} investigation folders have two-way links with the current usage tables")
    for name, checkout in repositories.items():
        if checkout:
            print(f"{sources[name]} pinned {name} source links checked")
    print(f"{verified_excerpts['local']} archived file excerpts and {verified_excerpts['git']} Git excerpts matched")
    if skipped_git_excerpts:
        print(f"{skipped_git_excerpts} Git excerpts not compared (supply the source checkouts)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harbor-repo", type=Path, help="Harbor checkout containing the release tags")
    parser.add_argument("--dressage-repo", type=Path, help="Dressage checkout containing the baseline commit")
    parser.add_argument("--slime-repo", type=Path, help="Slime checkout containing Dressage's submodule commit")
    args = parser.parse_args()
    check(Path(__file__).resolve().parents[1], args.harbor_repo, args.dressage_repo, args.slime_repo)
