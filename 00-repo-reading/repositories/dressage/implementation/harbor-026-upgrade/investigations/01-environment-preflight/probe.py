"""Observe how the installed Harbor factory calls Dressage's bwrap preflight."""

import os
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

from harbor.environments.factory import EnvironmentFactory

from dressage.integrations.harbor import environment


class ReachedBwrapCheck(Exception):
    """The factory entered the backend. Stop before looking for binaries."""


def main() -> None:
    checkout = os.environ.get("DRESSAGE_ROOT")
    if checkout and not Path(environment.__file__).resolve().is_relative_to(Path(checkout).resolve()):
        raise RuntimeError("Import Dressage from the checkout selected by DRESSAGE_ROOT.")
    print(f"Harbor {version('harbor')}")
    with patch.object(environment, "_load_bwrap_integration_config", side_effect=ReachedBwrapCheck):
        try:
            EnvironmentFactory.run_preflight(
                type=None,
                import_path="dressage.integrations.harbor.environment:DressageEnvironment",
            )
        except ReachedBwrapCheck:
            print("factory entered Dressage's bwrap checks")
        except TypeError as exc:
            if "unexpected keyword argument 'kwargs'" not in str(exc):
                raise
            print(f"factory rejected the call: {exc}")
        else:
            raise AssertionError("The factory returned without reaching the bwrap check.")


if __name__ == "__main__":
    main()
