"""Check Harbor's discovery of a wheel-installed Dressage and the active dependencies."""

import argparse
import asyncio
import logging
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from uuid import UUID

from packaging.requirements import Requirement

from harbor.cli.job_plugins import finalize_job_plugins
from harbor.cli.plugin_registry import resolve_plugin_import_path
from harbor.models.job.result import JobResult, JobStats
from harbor.utils.import_path import import_class


class FailingStore:
    async def write_job_manifest(self, *args, **kwargs):
        raise OSError("synthetic manifest write failure")


class WarningLog(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


async def probe(wheel_site):
    import dressage

    assert Path(dressage.__file__).resolve().is_relative_to(wheel_site)
    distribution = metadata.distribution("dressage")
    assert Path(distribution.locate_file("")).resolve() == wheel_site
    print("Harbor", metadata.version("harbor"))
    extra = [r for r in distribution.requires if Requirement(r).name == "harbor"]
    print("Dressage wheel Harbor extra:", *extra)
    name = resolve_plugin_import_path("dressage")
    declared = [entry.value for entry in distribution.entry_points
                if entry.group == "harbor.plugins" and entry.name == "dressage"]
    assert declared == [name]
    cls = import_class(name, label="plugin")
    print("Harbor plugin registry resolved wheel entry point:", name)

    unsatisfied = []
    for raw in metadata.requires("harbor"):
        requirement = Requirement(raw)
        if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
            continue
        try:
            installed = metadata.version(requirement.name)
        except metadata.PackageNotFoundError:
            installed = None
        if installed is None or not requirement.specifier.contains(installed):
            unsatisfied.append(f"{requirement} (installed: {installed})")
    print("Harbor base requirements missing or out of range:", sorted(unsatisfied))

    plugin = cls(config={}, artifact_store=FailingStore())
    result = JobResult(id=UUID(int=1), started_at=datetime.now(timezone.utc),
                       n_total_trials=0, stats=JobStats(), trial_results=[])
    handler = WarningLog()
    logger = logging.getLogger("harbor.cli.job_plugins")
    logger.addHandler(handler)
    try:
        await finalize_job_plugins([plugin], result)
    finally:
        logger.removeHandler(handler)
    assert handler.messages == ["Job plugin DressageHarborPlugin failed during on_job_end"]
    print("Harbor CLI finalizer returned; observed warning:", *handler.messages)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel_site", type=Path)
    asyncio.run(probe(parser.parse_args().wheel_site.resolve()))
