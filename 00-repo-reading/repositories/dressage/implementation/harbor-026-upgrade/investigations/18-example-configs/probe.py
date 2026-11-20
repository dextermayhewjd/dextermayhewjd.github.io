"""Validate Dressage's example Job YAMLs and print their source checkpoint digest prefixes."""

from importlib.metadata import version
from pathlib import Path

import yaml
from harbor.models.job.config import JobConfig

import dressage
from dressage.integrations.harbor.data_source import _source_digest


def main() -> None:
    root = Path(dressage.__file__).resolve().parent.parent
    example_dir = root / "examples/harbor/harbor_job_configs"
    print(f"Harbor {version('harbor')} | n_samples=2 seed=7 shuffle=False")
    for name in ("tau3-bench-e2b", "terminal-bench-2-e2b"):
        job = JobConfig.model_validate(yaml.safe_load((example_dir / f"{name}.yaml").read_text()))
        digest = _source_digest(job, n_samples=2, seed=7, shuffle=False)
        print(f"{name} | {job.datasets[0].name} | {job.agents[0].model_name} | {job.environment.type.value} | {digest[:14]}")


if __name__ == "__main__":
    main()
