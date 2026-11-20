"""Capture Claude Code's launch environment, without starting its binary or making model calls."""

import argparse
import asyncio
import os
from contextvars import ContextVar
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

from dressage.integrations.harbor import plugin as dressage_plugin
from dressage.integrations.harbor.config import HarborIntegrationConfig
from dressage.integrations.harbor.plugin import (
    _agent_protocol,
    _inject_agent_routing,
    _reject_alternative_auth,
)
from harbor.agents.factory import AgentFactory
from harbor.environments.base import BaseEnvironment, ExecResult
from harbor.job import Job
from harbor.models.agent.context import AgentContext
from harbor.models.job.config import JobConfig


GATEWAY = "http://127.0.0.1:39100"
OTHER_ENDPOINT = "http://127.0.0.1:39101"
TRIAL_KEY = "synthetic-trial-credential"
OTHER_KEY = "synthetic-alternate-credential"


class RecordingEnvironment:
    """Use Harbor's exec environment precedence and record the CLI launch command."""

    scoped_exec_env = BaseEnvironment.scoped_exec_env
    _merge_env = BaseEnvironment._merge_env

    def __init__(self):
        self._persistent_env = {}
        self._exec_env_overlays = ContextVar("probe_exec_env_overlays", default=())
        self.launches = []

    async def exec(self, *, command, env=None, **kwargs):
        if "claude --verbose" in command:
            self.launches.append(self._merge_env(env))
        return ExecResult(stdout="", stderr="", return_code=0)


async def observe(task):
    print("Harbor", version("harbor"))
    integration = HarborIntegrationConfig()
    shipped_model = "Qwen/Qwen3.5-4B"
    native_model = "anthropic/claude-sonnet-4-5"
    provider_model = "openrouter/anthropic/claude-sonnet-4.5"
    cases = [
        ("shipped-agent", shipped_model, {}),
        ("shipped-endpoint-field", shipped_model, {"base_url": OTHER_ENDPOINT}),
        ("shipped-key-selector", shipped_model, {"model_api_key_name": "PROBE_OTHER_KEY"}),
        ("endpoint-field", native_model, {"base_url": OTHER_ENDPOINT}),
        ("key-selector", native_model, {"model_api_key_name": "PROBE_OTHER_KEY"}),
        ("missing-key-selector", native_model, {"model_api_key_name": "PROBE_MISSING_KEY"}),
        (
            "explicit-provider-env",
            provider_model,
            {"env": {
                "OPENROUTER_API_KEY": OTHER_KEY,
                "OPENROUTER_API_BASE": OTHER_ENDPOINT,
                "OPENROUTER_BASE_URL": OTHER_ENDPOINT,
            }},
        ),
        ("provider-no-credential", provider_model, {}),
    ]
    clean_env = {
        "PATH": os.getenv("PATH", ""),
        "LITELLM_LOCAL_MODEL_COST_MAP": "True",
        "DRESSAGE_ROUTE_PROBE": TRIAL_KEY,
        "PROBE_OTHER_KEY": OTHER_KEY,
    }
    key_labels = {TRIAL_KEY: "trial", OTHER_KEY: "other", "": "empty"}
    endpoint_labels = {GATEWAY: "gateway", OTHER_ENDPOINT: "other"}
    with TemporaryDirectory() as tmp, patch.dict(os.environ, clean_env, clear=True):
        for label, model, options in cases:
            job_config = JobConfig.model_validate({
                "job_name": label,
                "jobs_dir": tmp,
                "tasks": [{"path": str(task)}],
                "agents": [{"name": "claude-code", "model_name": model, **options}],
            })
            try:
                job = await Job.create(job_config)
            except Exception as exc:
                if type(exc).__name__ != "MissingModelCredentialError":
                    raise
                print(label, "Job.create rejected:", type(exc).__name__, str(exc).splitlines()[0])
                continue

            candidate = job._remaining_trial_configs[0].agent.model_copy(deep=True)
            protocol = _agent_protocol(candidate, integration)
            # The C06 baseline predates the job-start connection check.
            validate = getattr(dressage_plugin, "_validate_gateway_connection", None)
            if validate is not None:
                try:
                    validate(candidate, integration, protocol)
                except dressage_plugin.RoutingPolicyError as exc:
                    print(label, "Dressage rejected:", str(exc))
                    continue
            _reject_alternative_auth(candidate, protocol)
            _inject_agent_routing(candidate, integration, "DRESSAGE_ROUTE_PROBE", GATEWAY)
            agent = AgentFactory.create_agent_from_config(candidate, logs_dir=Path(tmp))
            environment = RecordingEnvironment()
            with environment.scoped_exec_env(agent.extra_env):
                await agent.run("offline launch capture", environment, AgentContext())

            (launch_env,) = environment.launches
            endpoint = endpoint_labels[launch_env["ANTHROPIC_BASE_URL"]]
            key = key_labels[launch_env.get("ANTHROPIC_API_KEY", "")]
            token = key_labels[launch_env.get("ANTHROPIC_AUTH_TOKEN", "")]
            print(f"{label} Job.create ok endpoint={endpoint} api_key={key} auth_token={token}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    fixture = Path(__file__).resolve().parents[1] / "09-trial-plan" / "tasks" / "first"
    parser.add_argument("--task", type=Path, default=fixture, help="local task directory")
    asyncio.run(observe(parser.parse_args().task.resolve()))
