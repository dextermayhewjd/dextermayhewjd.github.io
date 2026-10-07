#!/usr/bin/env python3
"""Build the public appendix archive from exactly the indexed example files."""
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples/s07-skills-lab"
manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
output = ROOT / "static/downloads/s07-skills-lab.zip"
output.parent.mkdir(parents=True, exist_ok=True)
seen = set()
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for entry in sorted(manifest["files"], key=lambda item: item["path"]):
        name = entry["path"]
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or name in seen:
            raise ValueError(f"Invalid or duplicate example path: {name}")
        source_file = SOURCE / name
        if not source_file.resolve().is_relative_to(SOURCE.resolve()):
            raise ValueError(f"Example leaves source directory: {name}")
        info = zipfile.ZipInfo("s07-skills-lab/" + name, date_time=(2026, 10, 4, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = (stat.S_IFREG | 0o644) << 16
        archive.writestr(info, source_file.read_bytes())
        seen.add(name)
print(f"Built {output.name}: {len(seen)} files, {output.stat().st_size} bytes")
