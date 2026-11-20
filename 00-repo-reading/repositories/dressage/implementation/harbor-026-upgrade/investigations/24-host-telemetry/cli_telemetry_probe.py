"""Render the shipped YAML in the real CLI and intercept telemetry before its sender starts."""

import argparse
from contextlib import ExitStack
import importlib.util
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
from urllib.parse import urlparse

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

from harbor.cli.main import app
from typer.testing import CliRunner


def observe(config_file, setting):
    runner = CliRunner()
    args = ["run", "--config", str(config_file), "--plugin", "dressage", "--yes", "--print-config"]
    sent_to_boundary = []
    with ExitStack() as stack:
        stack.enter_context(patch.dict(os.environ))
        if setting is None:
            os.environ.pop("HARBOR_TELEMETRY", None)
        else:
            os.environ["HARBOR_TELEMETRY"] = setting
        if importlib.util.find_spec("harbor.telemetry") is not None:
            stack.enter_context(patch("harbor.telemetry._get_install_id", return_value="probe-id"))
            stack.enter_context(patch("harbor.telemetry._spawn_sender", side_effect=sent_to_boundary.append))
        stack.enter_context(patch.object(sys, "argv", ["harbor", *args]))
        result = runner.invoke(app, args)
        if result.exit_code:
            raise RuntimeError(f"CLI exit {result.exit_code}") from result.exception
        config = json.loads(result.stdout)
        assert config["agents"][0]["n_concurrent"] == 4
    if sent_to_boundary:
        (payload,) = sent_to_boundary
        event = payload["body"]["event"]
        destination = urlparse(payload["url"]).hostname
        flags = ",".join(payload["body"]["properties"]["command_flags"])
    else:
        event = destination = flags = "none"
    print(f"{version('harbor')} {config_file.name} setting={setting or 'unset'} "
          f"event={event} host={destination} flags={flags}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dressage_checkout", type=Path)
    checkout = parser.parse_args().dressage_checkout
    directory = checkout / "examples" / "harbor" / "harbor_job_configs"
    for filename in ("tau3-bench-e2b.yaml", "terminal-bench-2-e2b.yaml"):
        for setting in (None, "0"):
            observe(directory / filename, setting)
