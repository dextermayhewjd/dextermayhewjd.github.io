"""Create local Jobs with Dressage's temporary config and inspect Harbor's lock format."""

import argparse
import asyncio
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from harbor.job import Job
from harbor.models.job.config import JobConfig

from dressage.integrations.harbor.config import HarborIntegrationConfig
from dressage.integrations.harbor.rollout import _temporary_job_config


async def observe(task: Path, agent: str, model: str) -> None:
    with TemporaryDirectory() as probe_dir:
        source = JobConfig.model_validate({
            "job_name": "lock-probe", "jobs_dir": probe_dir,
            "tasks": [{"path": str(task.resolve())}],
            "agents": [{"name": agent, "model_name": model}],
        })
        integration = HarborIntegrationConfig.model_validate({
            "execution_mode": "rollout", "artifacts": {"root": probe_dir},
        })
        spec = SimpleNamespace(
            task_config=source.tasks[0], agent_config=source.agents[0],
            runtime_fingerprint="local-probe", agent_id="local-agent",
        )
        # This entry only supplies the two template slots and the resolved input configs.
        config = _temporary_job_config(
            source_job_config=source, partition=[SimpleNamespace(spec=spec, templates=[1, 2])],
            config=integration, run_id="audit", rollout_id=1, retry_round=0,
        )
        job = await Job.create(config)
        job._init_job_lock()
        print(f"{agent} | {model} | Job.create succeeded | lock schema {job._job_lock.schema_version}")


async def main(task: Path) -> None:
    print(f"Harbor {version('harbor')}")
    cases = (("claude-code", "MiniMax-M3"), ("claude-code", "Qwen/Qwen3.5-4B"), ("codex", "openai/gpt-4o"))
    for agent, model in cases:
        await observe(task, agent, model)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    example = Path(__file__).resolve().parents[1] / "09-trial-plan" / "tasks" / "first"
    parser.add_argument("--task", type=Path, default=example, help="A local Harbor task directory")
    asyncio.run(main(parser.parse_args().task))
