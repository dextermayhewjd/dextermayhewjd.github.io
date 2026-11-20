"""Comparison fixtures for the C05b investigation, run against a selected checkout.

The three historical limits characterize C05a. The direct-output and retry
checks apply to the narrow candidate. See c05-mount-experiments.md for commands.
"""

import json
import os

import pytest
from harbor.models.task.config import EnvironmentConfig, NetworkMode, NetworkPolicy
from harbor.models.trial.config import TrialConfig
from harbor.models.trial.paths import TrialPaths
from harbor.trial.trial import Trial

from dressage.integrations.harbor.environment import DressageEnvironment
from test_environment import _configure_bwrap, bwrap_network_namespace


@pytest.mark.usefixtures("bwrap_network_namespace")
@pytest.mark.asyncio
@pytest.mark.parametrize("layout", ["outbound-link", "unlistable-agent", "read-only-self"])
async def test_known_log_layout(monkeypatch, tmp_path, layout):
    _configure_bwrap(monkeypatch, tmp_path)
    task = tmp_path / "task"
    for name in ("environment", "solution", "tests"):
        (task / name).mkdir(parents=True)
    (task / "instruction.md").write_text("Write 4 to /app/answer.txt.")
    config_text = 'schema_version = "1.3"\n[environment]\ngpus = 0\nnetwork_mode = "no-network"\n'
    if layout == "read-only-self":
        config_text += 'workdir = "/logs/agent"\n'
    (task / "task.toml").write_text(config_text)
    probe = "run/probe.log" if layout == "outbound-link" else "probe.log"
    (task / "solution/solve.sh").write_text(
        f"#!/bin/sh\nset -eu\nprintf 'fresh probe\\n' > /logs/agent/{probe}\n"
        "echo 4 > /app/answer.txt\necho solved\n"
    )
    (task / "tests/test.sh").write_text(
        "#!/bin/sh\nset -eu\ntest \"$(cat /app/answer.txt)\" = 4\n"
        "echo '{\"reward\": 1}' > /logs/verifier/reward.json\n"
    )
    logs = tmp_path / "logs"
    logs.mkdir()
    mounts = []
    if layout != "read-only-self":
        for role in ("agent", "verifier"):
            (logs / role).mkdir()
        mounts.append({"type": "bind", "source": str(logs), "target": "/logs"})
    if layout == "outbound-link":
        (logs / "other").mkdir()
        (logs / "agent/run").symlink_to("../other")
        mounts.append({"type": "bind", "source": str(logs / "other"), "target": "/logs/agent/run"})
    if layout == "unlistable-agent":
        (logs / "agent").chmod(0o333)
        if os.access(logs / "agent", os.R_OK):
            (logs / "agent").chmod(0o755)
            pytest.skip("requires a user subject to directory read permissions")
    config = TrialConfig.model_validate({
        "task": {"path": task}, "agent": {"name": "oracle"},
        "environment": {"import_path": "dressage.integrations.harbor.environment:DressageEnvironment",
                        "mounts": mounts},
        "trial_name": "review-logs", "trials_dir": tmp_path / "trials",
    })
    if layout == "read-only-self":
        initial = await Trial.create(config)
        source = initial.agent_environment._rootfs / "logs/agent"
        initial._close_logger_handler()
        (logs / "to-agent").symlink_to("../agent")
        config.environment.mounts.extend([
            {"type": "bind", "source": str(logs), "target": "/logs/view"},
            {"type": "bind", "source": str(source), "target": "/logs/view/to-agent", "read_only": True},
        ])
    trial = await Trial.create(config)
    env = trial.agent_environment
    original_start = env.start
    start = {}

    async def observe_start(*args, **kwargs):
        before = {entry.name for entry in logs.iterdir()}
        try:
            await original_start(*args, **kwargs)
            start["returned"] = True
        finally:
            start["added_host_entries"] = sorted({entry.name for entry in logs.iterdir()} - before)

    monkeypatch.setattr(env, "start", observe_start)
    try:
        result = await trial.run()
    finally:
        if layout == "unlistable-agent":
            (logs / "agent").chmod(0o755)
    collected = trial.paths.agent_dir
    observation = {
        **start,
        "reward": result.verifier_result.rewards if result.verifier_result else None,
        "oracle": (collected / "oracle.txt").read_text() if (collected / "oracle.txt").is_file() else None,
        "host_probe": (logs / "agent" / probe).read_text() if (logs / "agent" / probe).is_file() else None,
        "collected_probe": (collected / probe).read_text() if (collected / probe).is_file() else None,
        "preserved_link": (collected / "run").is_symlink(),
        "error": result.exception_info.exception_type if result.exception_info else None,
    }
    (tmp_path / "observation.json").write_text(json.dumps(observation, indent=2))
    assert observation["returned"]
    assert observation["collected_probe"] is None
    if layout == "read-only-self":
        assert observation["oracle"] is None and observation["reward"] is None
    else:
        assert observation["oracle"] == "solved\n"
        assert observation["reward"] == {"reward": 1}
        assert observation["host_probe"] == "fresh probe\n"
        assert observation["preserved_link"] == (layout == "outbound-link")


def make_environment(tmp_path, declarations):
    source = tmp_path / "logs"
    source.mkdir()
    paths = TrialPaths(tmp_path / "trial")
    paths.mkdir()
    task = tmp_path / "task-env"
    task.mkdir()
    return DressageEnvironment(
        environment_dir=task, environment_name="local", session_id="sample__env",
        trial_paths=paths, task_env_config=EnvironmentConfig(gpus=0),
        network_policy=NetworkPolicy(network_mode=NetworkMode.NO_NETWORK),
        mounts=[{"type": "bind", "target": "/logs", "source": str(source)}],
        auto_mounts=[{"type": "bind", "target": f"/logs/{leaf}", "source": str(tmp_path / leaf)}
                     for leaf in declarations],
    )


@pytest.mark.asyncio
@pytest.mark.usefixtures("bwrap_network_namespace")
@pytest.mark.parametrize("outputs", [[], ["verifier"], ["agent", "user-agent", "verifier", "artifacts"]])
async def test_declared_direct_outputs(tmp_path, monkeypatch, outputs):
    _configure_bwrap(monkeypatch, tmp_path)
    env = make_environment(tmp_path, outputs)
    try:
        await env.start(False)
        assert sorted(p.name for p in (tmp_path / "logs").iterdir()) == sorted(outputs)
        for leaf in outputs:
            result = await env.exec(f"printf 'fresh {leaf}' > /logs/{leaf}/probe.log")
            assert result.return_code == 0, result.stderr
            await env.download_dir(f"/logs/{leaf}", tmp_path / "recovered" / leaf)
            expected = f"fresh {leaf}".encode()
            assert (tmp_path / "recovered" / leaf / "probe.log").read_bytes() == expected
            assert (tmp_path / "logs" / leaf / "probe.log").read_bytes() == expected
    finally:
        await env.stop(True)


@pytest.mark.asyncio
@pytest.mark.usefixtures("bwrap_network_namespace")
async def test_uncollectible_new_leaf_is_rejected_then_retry_succeeds(tmp_path, monkeypatch):
    _configure_bwrap(monkeypatch, tmp_path)
    env = make_environment(tmp_path, ["verifier", "agent"])
    mkdir = os.mkdir

    def create_leaf(name, mode=0o777, *, dir_fd=None):
        if name == "agent" and dir_fd is not None:
            mode = 0o333
        return mkdir(name, mode, dir_fd=dir_fd)

    try:
        with monkeypatch.context() as restricted:
            restricted.setattr(os, "mkdir", create_leaf)
            with pytest.raises(PermissionError, match="/logs/agent"):
                await env.start(False)
        assert not (tmp_path / "logs/agent").exists()
        await env.start(False)
        result = await env.exec("printf fresh > /logs/agent/probe.log")
        assert result.return_code == 0, result.stderr
        await env.download_dir("/logs/agent", tmp_path / "recovered")
        assert (tmp_path / "recovered/probe.log").read_bytes() == b"fresh"
    finally:
        await env.stop(True)
