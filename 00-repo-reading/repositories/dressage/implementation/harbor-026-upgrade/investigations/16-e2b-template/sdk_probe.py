"""Inspect the installed E2B extra and read a Dockerfile without using a cloud account."""

from importlib import metadata
from pathlib import Path
from tempfile import TemporaryDirectory

from harbor.environments import e2b
from harbor.environments.definition import parse_dockerfile_workdir
from packaging.requirements import Requirement

print("Harbor", metadata.version("harbor"), "E2B adapter imports its SDK:", e2b._HAS_E2B)
for raw in metadata.requires("harbor"):
    requirement = Requirement(raw)
    marker = requirement.marker
    if marker and marker.evaluate({"extra": "e2b"}) and not marker.evaluate({"extra": ""}):
        try:
            installed = metadata.version(requirement.name)
        except metadata.PackageNotFoundError:
            installed = None
        print(requirement.name, str(requirement.specifier), "installed:", installed)

with TemporaryDirectory() as root:
    dockerfile = Path(root) / "Dockerfile"
    dockerfile.write_text("FROM scratch\nWORKDIR /app\n")
    try:
        print("WORKDIR:", parse_dockerfile_workdir(dockerfile))
    except ModuleNotFoundError as exc:
        print("WORKDIR lookup:", type(exc).__name__, str(exc))
