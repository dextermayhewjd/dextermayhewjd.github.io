"""Observe the real Harbor Job plan and Dressage hook registration before executing a Trial."""

import argparse
import asyncio
from contextlib import nullcontext
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from harbor.job import Job
from harbor.models.job.config import JobConfig

from dressage.integrations.harbor import compat
from dressage.integrations.harbor.config import HarborIntegrationConfig
from dressage.integrations.harbor.plugin import DressageHarborPlugin
from tests.integrations.harbor.conftest import RecordingRuntime


async def observe(tasks: list[Path], models: list[str], attempts: int) -> None:
    with TemporaryDirectory() as probe_dir:
        config = JobConfig.model_validate({
            "job_name": "plan-probe",
            "jobs_dir": probe_dir,
            "tasks": [{"path": str(task)} for task in tasks],
            "agents": [{"name": "claude-code", "model_name": model} for model in models],
            "n_attempts": attempts,
        })
        resolved = await compat.resolve_task_configs(config)
        job = await Job.create(config)
        plan = compat.assign_trial_names(job, lambda entry: f"probe-{entry.position}")
        positions = [(entry.attempt_index, entry.task_index, entry.agent_index) for entry in plan]
        expected = [
            (attempt, task, agent)
            for attempt in range(attempts)
            for task in range(len(tasks))
            for agent in range(len(models))
        ]
        assert len(resolved) == len(tasks) and positions == expected
        print("plan (attempt, task, agent):", positions)

        plugin = DressageHarborPlugin(
            HarborIntegrationConfig.model_validate({
                "execution_mode": "rollout", "artifacts": {"root": probe_dir},
            }),
            gateway_runtime=RecordingRuntime(),
        )
        hooks = job._trial_queue._hooks
        before = {event: len(callbacks) for event, callbacks in hooks.items()}
        try:
            await plugin.on_job_start(job)
            added = {
                event.name for event, callbacks in hooks.items()
                if len(callbacks) == before.get(event, 0) + 1
            }
            assert added == {"START", "AGENT_START", "AGENT_END", "VERIFICATION_START", "CANCEL", "END"}
            pending = compat.pending_trial_configs(job)
            assert len(pending) == len(expected)
            assert all(trial.agent.env.get("ANTHROPIC_BASE_URL") for trial in pending)
            print("registered:", ", ".join(sorted(added)))
            print("Trial configs with a Gateway URL:", len(pending))
        finally:
            await plugin.aclose()


async def main(first: Path, second: Path) -> None:
    installed = version("harbor")
    print(f"Harbor {installed}")
    gate = nullcontext()
    try:
        compat.require_harbor_runtime()
    except compat.HarborCompatibilityError as exc:
        if installed not in {"0.25.0", "0.26.0"} or compat.SUPPORTED_HARBOR_VERSION != "0.18.0":
            raise
        print("original version check:", exc)
        # Constrain the substitution to this observation and restore it on exit.
        gate = patch.object(compat, "SUPPORTED_HARBOR_VERSION", installed)
    else:
        print("original version check: accepted")
    with gate:
        await observe([first.resolve()], ["MiniMax-M3"], 1)
        await observe([first.resolve(), second.resolve()], ["MiniMax-M3", "audit-model"], 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    examples = Path(__file__).resolve().parent / "tasks"
    parser.add_argument("--tasks", type=Path, nargs=2, default=(examples / "first", examples / "second"),
                        metavar=("FIRST", "SECOND"), help="Two local Harbor task directories")
    asyncio.run(main(*parser.parse_args().tasks))
