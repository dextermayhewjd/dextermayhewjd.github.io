"""Reproduce log recovery or skill upload against a disposable Dressage bwrap root."""

import argparse
import asyncio
import json
import os
import shutil
from importlib.metadata import version
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from unittest.mock import patch

from harbor.models.task.config import EnvironmentConfig
from harbor.models.trial.paths import TrialPaths

from dressage.integrations.harbor.environment import DressageEnvironment


async def recover_logs(env: DressageEnvironment, trial_paths: TrialPaths) -> None:
    sandbox_path = PurePosixPath("/logs/agent")
    host_dir = trial_paths.agent_dir
    same_directory = env._host_path(str(sandbox_path)) == host_dir
    mounted = env.is_path_mounted(sandbox_path, host_dir)
    print(f"actual directory equals Trial directory: {same_directory}")
    print(f"Harbor reports the directory mounted: {mounted}")

    # Write through the sandbox mapping so the logs originate in the environment.
    sample_log = "one nonempty agent log\n"
    (env._host_path(str(sandbox_path)) / "probe.log").write_text(sample_log)
    if mounted:
        print("Trial branch: skip download")
    else:
        print("Trial branch: download_dir")
        try:
            await env.download_dir(str(sandbox_path), host_dir)
        except shutil.Error as exc:
            if not same_directory:
                raise
            print(f"nonempty directory copy raised {type(exc).__module__}.{type(exc).__name__}")
        else:
            print("nonempty directory copy completed")

    if (host_dir / "probe.log").read_text() != sample_log:
        raise AssertionError("The agent log was not preserved in the Trial directory.")


async def upload_skill(env: DressageEnvironment, root: Path) -> None:
    source = root / "demo"
    source.mkdir()
    (source / "SKILL.md").write_text("demo\n")
    await env.upload_dir(source, "/runtime/skills/demo")
    if env._host_path("/runtime/skills/demo/SKILL.md").read_text() != "demo\n":
        raise AssertionError("Skill content did not survive upload.")
    print("uploaded skill read back from /runtime/skills/demo/SKILL.md")


async def observe(operation: str) -> None:
    print(f"Harbor {version('harbor')} | {operation}")
    with TemporaryDirectory() as probe_dir:
        root = Path(probe_dir)
        config = root / "integration.json"
        config.write_text(json.dumps({
            "gateway": {"listen_port": 39100},
            "environment": {"mode": "bwrap", "runtime_root": str(root / "runtime")},
            "security": {"routing_guarantee": "enforced"},
        }))
        paths = TrialPaths(root / "trial")
        paths.mkdir()
        environment_dir = root / "environment"
        environment_dir.mkdir()
        with patch.dict(os.environ, {"DRESSAGE_HARBOR_INTEGRATION_CONFIG": str(config)}), patch(
            "dressage.integrations.harbor.environment._required_binary",
            side_effect=lambda name: f"/usr/bin/{name}",
        ):
            env = DressageEnvironment(
                environment_dir=environment_dir,
                environment_name="audit",
                session_id="trial__env",
                trial_paths=paths,
                task_env_config=EnvironmentConfig(workdir="/app"),
                auto_mounts=[{"type": "bind", "source": str(paths.agent_dir), "target": "/logs/agent"}],
            )
            try:
                await env.start(force_build=False)
                if operation == "logs":
                    await recover_logs(env, paths)
                else:
                    await upload_skill(env, root)
            finally:
                await env.stop(delete=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("logs", "skills"))
    asyncio.run(observe(parser.parse_args().operation))
