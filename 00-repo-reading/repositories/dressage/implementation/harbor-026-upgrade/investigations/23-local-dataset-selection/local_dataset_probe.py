"""Observe the order and subset of real HarborDataSource samples for one shared fixture."""

import argparse
from importlib.metadata import version
from pathlib import Path
import shutil
from types import SimpleNamespace


def prepare(directory):
    directory.mkdir(parents=True, exist_ok=False)
    fixture = Path(__file__).resolve().parents[1] / "09-trial-plan" / "tasks" / "first"
    for name in ("zeta", "theta", "lambda", "beta", "alpha", "gamma", "eta", "iota", "kappa"):
        shutil.copytree(fixture, directory / name)
        (directory / name / "environment").mkdir(exist_ok=True)


def observe(directory):
    from dressage.integrations.harbor import compat
    from dressage.integrations.harbor.data_source import HarborDataSource

    release = version("harbor")
    if release not in {"0.18.0", "0.25.0", "0.26.0"}:
        raise ValueError(f"Use a recorded release, got {release!r}")
    compat.SUPPORTED_HARBOR_VERSION = release
    names = [entry.name for entry in directory.iterdir()]
    print(f"Harbor {release} | directory iteration {','.join(names)}")
    for limit in (None, 2):
        dataset = {"path": str(directory)}
        if limit is not None:
            dataset["n_tasks"] = limit
        source = HarborDataSource(SimpleNamespace(
            harbor_integration_config={
                "execution_mode": "training",
                "training": {"model_override": "fixture"},
            },
            harbor_job_config={
                "job_name": "dataset-order",
                "verifier": {"disable": True},
                "datasets": [dataset],
                "agents": [{"name": "claude-code"}],
            },
            rollout_shuffle=False,
            rollout_seed=7,
        ))
        selected = []
        for group in source.get_samples(len(source.specs)):
            spec = source.resolve_spec(group[0].metadata["harbor_spec_id"])
            selected.append(spec.task_config.path.name)
        print(f"n_tasks={limit} | emitted samples {','.join(selected)}")
        expected = names if release == "0.18.0" else sorted(names)
        assert selected == expected[:limit], (selected, expected[:limit])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "observe"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if args.operation == "prepare":
        prepare(directory)
    else:
        observe(directory)
