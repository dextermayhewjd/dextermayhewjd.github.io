"""Check the Harbor factory call before any external bwrap requirements."""

from importlib.metadata import version
from unittest.mock import Mock

import pytest
from harbor.environments.factory import EnvironmentFactory

from dressage.integrations.harbor import environment


class BackendCheckReached(Exception):
    """Stop at the first backend config lookup."""


@pytest.mark.parametrize(
    "factory_arguments",
    [
        {},
        {"kwargs": None},
        {"kwargs": {}},
        {"kwargs": {"test_marker": "keep"}},
    ],
    ids=["default", "explicit-none", "empty-options", "nonempty-options"],
)
def test_preflight_through_harbor_factory(factory_arguments, monkeypatch):
    legacy_factory = version("harbor") in {"0.18.0", "0.25.0"}
    if factory_arguments and legacy_factory:
        pytest.skip("This Harbor factory exposes only the default preflight call.")

    backend_check = Mock(side_effect=BackendCheckReached)
    monkeypatch.setattr(environment, "_load_bwrap_integration_config", backend_check)
    if not legacy_factory:
        backend = environment.DressageEnvironment
        parse_options = Mock(wraps=backend.parse_options)
        monkeypatch.setattr(backend, "parse_options", parse_options)

    with pytest.raises(BackendCheckReached):
        EnvironmentFactory.run_preflight(
            type=None,
            import_path="dressage.integrations.harbor.environment:DressageEnvironment",
            **factory_arguments,
        )

    backend_check.assert_called_once_with()
    if not legacy_factory:
        parse_options.assert_called_once_with(factory_arguments.get("kwargs"))
