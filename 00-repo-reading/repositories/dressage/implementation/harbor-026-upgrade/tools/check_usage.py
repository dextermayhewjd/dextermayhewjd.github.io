"""Check the handoff tables against the archived scan, without rescanning either repo."""

import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit


VERSION_COMMITS = {
    "0.18.0": "527d50deb63a5d279e8c20593c18a2cbc7f61f9e",
    "0.25.0": "fdba28fc411e47e8765420a1a063b4918fce3def",
    "0.26.0": "3cb627394b95d3ae605f31e0d694edf508cf4b7b",
}
DRESSAGE_LINK = r"https://github\.com/Accio-Lab/Dressage/blob/[0-9a-f]{40}/"
TABLE_HEADER = "| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |"


def compare_records(label: str, expected: set, records: list) -> None:
    counted = Counter(records)
    actual = set(counted)
    repeated = sorted(key for key, count in counted.items() if count > 1)
    if actual != expected or repeated:
        raise ValueError(
            f"{label}: missing {sorted(expected - actual)}, "
            f"unexpected {sorted(actual - expected)}, repeated {repeated}"
        )


def check_source_index(snapshot: str, mapping: str) -> tuple[int, int]:
    for label, anchor in re.findall(r"\[U(\d+)\]\([^)]+#u(\d+)\)", mapping):
        if label != anchor:
            raise ValueError(f"source index labels U{label} but points to U{anchor}")
    raw_lines, _, raw_files = snapshot.partition('<a id="files"></a>')
    expected_lines = {
        (path, int(line)) for path, line in
        re.findall(DRESSAGE_LINK + r"([^#)]+)#L(\d+)(?:-L\d+)?\)", raw_lines)
    }
    expected_files = set(re.findall(DRESSAGE_LINK + r"([^#)]+)\)", raw_files))
    if not expected_lines or not expected_files:
        raise ValueError("the archived discovery index is missing source rows")

    sources, _, files = mapping.partition('<a id="files"></a>')
    files = files.partition('<a id="follow-up"></a>')[0]
    lines = []
    for path, numbers, decision in re.findall(
        r"^\| `([^`]+)` \| (\d+(?:, \d+)*) \| (.+) \|$", sources, re.MULTILINE
    ):
        if not re.search(r"\[U\d+\]\([^)]+#u\d+\)", decision) and not decision.startswith("排除。"):
            raise ValueError(f"{path}:{numbers} needs a handoff or a reason for exclusion")
        lines.extend((path, int(number)) for number in numbers.split(", "))
    mapped_files = re.findall(r"^\| `([^`]+)` \| [^\n]+ \|$", files, re.MULTILINE)
    compare_records("discovered source positions", expected_lines, lines)
    compare_records("files in the discovery snapshot", expected_files, mapped_files)
    return len(lines), len(mapped_files)


def check_handoff(block: str, number: str) -> None:
    if not block.startswith(f"# U{number} · ") or block.count(TABLE_HEADER) != 1:
        raise ValueError(f"U{number}: missing heading or input/output table")
    if "**Dressage 原行**" not in block or "**接续**" not in block:
        raise ValueError(f"U{number}: missing source or next observation")
    if re.findall(r'<a id="u(\d+)"></a>', block) != [number]:
        raise ValueError(f"U{number}: expected one matching handoff anchor")
    for label in ("① 输入", "② 结果"):
        sites = [line for line in block.splitlines() if line.startswith(f"| {label}　")]
        if len(sites) != 1:
            raise ValueError(f"U{number}: expected one observation for {label}")
        site, observation = sites[0].removeprefix("| ").removesuffix(" |").split(" | ")
        if not re.search(r"/blob/[0-9a-f]{40}/[^)]+#L\d+", site) or not observation.strip():
            raise ValueError(f"U{number}: {label} needs a pinned location and a value to observe")
    if sum(map(len, usage_excerpts(block).values())) != 1:
        raise ValueError(f"U{number}: expected one cited Dressage source excerpt")
    observed = []
    for line in block.splitlines():
        if not line.startswith("| [0."):
            continue
        fields = re.split(r"(?<!\\)\|", line[1:-1])
        if len(fields) != 5 or not all(field.strip() for field in fields):
            raise ValueError(f"U{number}: incomplete input/output row")
        version = re.match(
            r"^\s*\[(0\.\d+\.\d+)\]\(https://github\.com/harbor-framework/harbor/"
            r"blob/([0-9a-f]{40})/[^)]+#L\d+", fields[0]
        )
        if not version or VERSION_COMMITS.get(version[1]) != version[2]:
            raise ValueError(f"U{number}: version row must cite its pinned Harbor source")
        observed.append(version[1])
    compare_records(f"U{number} versions", set(VERSION_COMMITS), observed)


def usage_excerpts(content: str) -> dict[str, list[str]]:
    excerpts: dict[str, list[str]] = {}
    for source, quote in re.findall(
        r"^\*\*Dressage 原行\*\*[^\n]*\]\(([^)]+#L\d+(?:-L\d+)?)\)\n\n```[^\n]*\n(.*?)\n```$",
        content, re.MULTILINE | re.DOTALL,
    ):
        excerpts.setdefault(source, []).append(quote)
    return excerpts


def indexed_numbers(ranges: str) -> set[str]:
    numbers = []
    for span in ranges.split("、"):
        match = re.fullmatch(r"U(\d+)(?:–U(\d+))?", span)
        if not match or int(match[2] or match[1]) < int(match[1]):
            raise ValueError(f"invalid handoff range {span}")
        numbers.extend(f"{n:02}" for n in range(int(match[1]), int(match[2] or match[1]) + 1))
    compare_records(f"usage range {ranges}", set(numbers), numbers)
    return set(numbers)


def linked_pages(page: Path, content: str, prefix: str) -> set[Path]:
    return {
        (page.parent / unquote(urlsplit(link).path)).resolve()
        for link in re.findall(r"\]\(([^)\n]+)\)", content)
        if link.startswith(prefix)
    }


def check_investigation_map(root: Path, pages: dict[Path, str]) -> None:
    folder = root / "investigations"
    investigations = set(folder.glob("*/README.md"))
    incoming = {investigation: set() for investigation in investigations}
    for page, content in pages.items():
        for investigation in linked_pages(page, content, "../../investigations/") & investigations:
            incoming[investigation].add(page)

    report = (folder / "original-test-audit.md").read_text()
    rows = re.findall(
        r'^\| <a id="i(\d+)"></a>\[[^\]]+\]\(([^)]+)\) \| ([^|]+) \| ([^|]+) \|',
        report, re.MULTILINE,
    )
    compare_records("investigation audit rows", investigations, [(folder / target).resolve() for _, target, _, _ in rows])
    cited_pages = set()
    for number, target, primary, related in rows:
        investigation = (folder / target).resolve()
        cited = linked_pages(investigation, investigation.read_text(), "../../usage/") & pages.keys()
        if not cited & incoming[investigation]:
            raise ValueError(f"{investigation.parent.name}: missing two-way link to a relevant handoff")
        cited_pages.update(cited)
        if not investigation.parent.name.startswith(number + "-"):
            raise ValueError(f"{target}: wrong investigation number in audit table")
        for column, expected in [(primary, cited), (related, incoming[investigation] - cited)]:
            numbers = re.findall(r"\[U(\d+)\]\([^)]+#u\1\)", column)
            compare_records(f"{target} referenced U IDs", {p.name.split("-")[0][1:] for p in expected}, numbers)
    print(f"{len(set().union(*incoming.values()))}/{len(pages)} handoffs link to an investigation; "
          f"{len(cited_pages)} are cited directly in investigation READMEs; "
          f"{len(pages.keys() - cited_pages)} are not cited there")


def check_usage(root: Path) -> set[Path]:
    folder = root / "usage"
    index = (folder / "README.md").read_text()
    snapshot = (folder / "harbor-call-sites.md").read_text()
    positions, files = check_source_index(snapshot, (folder / "source-index.md").read_text())
    groups = re.findall(r"^\| (U[\dU–、]+) \| \[[^\]]+\]\(([^)]+\.md)\)", index, re.MULTILINE)
    if not groups:
        raise ValueError("no usage topics indexed")
    topics = {page for page in folder.glob("*/README.md") if page.parent.name != "evidence"}
    compare_records("topic indexes", topics, [folder / unquote(target) for _, target in groups])
    pages = {}
    all_ids = []
    for ranges, target in groups:
        topic = folder / unquote(target)
        entries = re.findall(
            r"^\| \[U(\d+)\]\(([^)#]+\.md)#u\1\) \| (.+) \|$", topic.read_text(), re.MULTILINE
        )
        compare_records(topic.parent.name, indexed_numbers(ranges), [number for number, _, _ in entries])
        for number, link, title in entries:
            filename = unquote(link)
            if filename != f"U{number}-{title}.md":
                raise ValueError(f"U{number}: topic row and filename disagree")
            page = topic.parent / filename
            block = page.read_text()
            if block.splitlines()[0] != f"# U{number} · {title}":
                raise ValueError(f"{filename}: topic row and page heading disagree")
            check_handoff(block, number)
            pages[page] = block
            all_ids.append(number)
    compare_records("unique handoff IDs", set(all_ids), all_ids)
    compare_records("standalone handoffs", set(folder.rglob("U[0-9]*-*.md")), list(pages))
    for topic in topics:
        compare_records(
            topic.parent.name,
            {topic} | {page for page in pages if page.parent == topic.parent},
            list(topic.parent.glob("*.md")),
        )

    check_investigation_map(root, pages)
    print(f"{len(topics)} topics, {len(all_ids)} handoff files with input and result observations, "
          f"{len(all_ids) * len(VERSION_COMMITS)} version rows, "
          f"{positions} archived source positions and {files} files accounted for")
    return set(pages)
