"""Observe E2B option identity, creation and renewal at a local fake SDK boundary."""
import asyncio
import json
from contextlib import ExitStack
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from harbor.environments import e2b
from harbor.environments.factory import EnvironmentFactory
from harbor.models.task.config import EnvironmentConfig
from harbor.models.trial.config import EnvironmentConfig as TrialEnvironmentConfig
from harbor.models.trial.paths import TrialPaths


def make_env(root, cpus, settings):
    config = TrialEnvironmentConfig(type="e2b", kwargs=settings)
    return EnvironmentFactory.create_environment_from_config(
        config, root, "demo", "local-session", TrialPaths(root / "trial"),
        EnvironmentConfig(cpus=cpus, memory_mb=1024, network_mode="no-network", docker_image="offline-image:v1"),
    )


async def run(root):
    old = version("harbor") in {"0.18.0", "0.25.0"}
    env1, env2 = (make_env(root, cpu, {}) for cpu in (1, 2))
    identity1 = getattr(env1, "template_ref", env1._template_name)
    identity2 = getattr(env2, "template_ref", env2._template_name)
    print(json.dumps({"harbor": version("harbor"), "sdk":version("e2b"),
                      "cpu1_ref": identity1, "cpu2_ref": identity2, "same_ref":identity1==identity2}))
    settings = {} if old else {"prebuilt_template_id": "fixture-template", "renew_interval_sec": .015,
                                "sandbox_timeout_sec": 9, "restore_login_path": False, "allow_memory_overcommit": False}
    env = make_env(root, 1, settings)
    renewed = asyncio.Event()
    async def extend(timeout):
        renewed.set()
    handle = SimpleNamespace(sandbox_id="offline-only", files=SimpleNamespace(read=AsyncMock(return_value="")),
                             set_timeout=AsyncMock(side_effect=extend), kill=AsyncMock(return_value=True))
    with ExitStack() as stack:
        create = stack.enter_context(patch.object(e2b.AsyncSandbox, "create", new=AsyncMock(return_value=handle)))
        if old:
            stack.enter_context(patch.object(e2b.AsyncTemplate, "alias_exists", new=AsyncMock(return_value=True)))
        await env.start(force_build=False)
        if not old:
            await asyncio.wait_for(renewed.wait(), timeout=1)
        await env.stop(delete=True)
        count_at_stop = handle.set_timeout.await_count
        await asyncio.sleep(.035)
        result = {"harbor": version("harbor"), "created_ref": create.await_args.kwargs["template"],
                  "create_timeout": create.await_args.kwargs["timeout"], "renewals": [c.args[0] for c in handle.set_timeout.await_args_list],
                  "no_calls_after_stop": handle.set_timeout.await_count == count_at_stop,
                  "kill_calls": handle.kill.await_count, "sandbox_cleared": env._sandbox is None}
        assert (identity1 == identity2) == old
        assert result["no_calls_after_stop"] and result["kill_calls"] == 1 and result["sandbox_cleared"]
        assert result["create_timeout"] == (86400 if old else 9)
        assert result["renewals"] == ([] if old else [9])
        print(json.dumps(result))


if __name__ == "__main__":
    with TemporaryDirectory() as temp:
        asyncio.run(run(Path(temp)))
