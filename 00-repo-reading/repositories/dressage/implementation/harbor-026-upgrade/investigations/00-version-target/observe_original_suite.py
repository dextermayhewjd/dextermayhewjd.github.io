"""Count original suite entries into the indexed Dressage functions and selected boundaries."""

import ast
import re
import sys
from collections import defaultdict
from importlib.metadata import version
from pathlib import Path

import pytest


# Match implementations by file and qualified name. A fixture with a method
# called Job.run is a different observation from harbor/job.py's Job.run.
WATCH = {
    "harbor/environments/factory.py": ["EnvironmentFactory.run_preflight"],
    "harbor/job.py": ["Job.create", "Job._init_job_lock", "Job.run"],
    "harbor/trial/trial.py": ["Trial.run", "Trial._emit", "Trial._download_agent_logs"],
    "harbor/trial/queue.py": ["TrialQueue._execute_trial_with_retries"],
    "dressage/integrations/harbor/environment.py": [
        "DressageEnvironment.preflight", "DressageEnvironment.download_dir",
    ],
    "dressage/integrations/harbor/plugin.py": [
        "DressageHarborPlugin._on_cancel", "DressageHarborPlugin._on_end",
        "DressageHarborPlugin.on_job_end",
    ],
    "dressage/integrations/harbor/artifacts.py": ["HarborArtifactStore.commit_attempt"],
    "dressage/integrations/harbor/rollout.py": ["_temporary_job_config", "_bundle_samples"],
}


def function_ranges(node, prefix=""):
    """Yield lexical function ranges, visiting enclosing functions before nested ones."""
    for child in ast.iter_child_nodes(node):
        child_prefix = prefix
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbol = prefix + child.name
            yield child.lineno, child.end_lineno, symbol
            child_prefix = symbol + ".<locals>."
        elif isinstance(child, ast.ClassDef):
            child_prefix = prefix + child.name + "."
        yield from function_ranges(child, child_prefix)


def indexed_functions(checkout):
    index = Path(__file__).resolve().parents[2] / "usage/source-index.md"
    source_rows = index.read_text().partition('<a id="files"></a>')[0]
    locations = defaultdict(set)
    for path, numbers, uses in re.findall(
        r"^\| `(dressage/integrations/harbor/[^`]+\.py)` \| (\d+(?:, \d+)*) \| (.+) \|$",
        source_rows, re.MULTILINE,
    ):
        if re.search(r"\[U\d+\]", uses):
            locations[path].update(map(int, numbers.split(", ")))
    scoped = defaultdict(list)
    for path, lines in locations.items():
        owners = dict.fromkeys(lines)
        for start, end, symbol in function_ranges(ast.parse((checkout / path).read_text())):
            for line in lines:
                if start <= line <= end:
                    owners[line] = symbol
        for line, symbol in owners.items():
            scoped[path, symbol].append(line)
    return scoped


class OriginalSuiteObserver:
    def __init__(self, methods):
        self.current_case = None
        self.reached = {method: set() for method in methods}
        self.paths_by_symbol = defaultdict(list)
        for path, symbol in methods:
            self.paths_by_symbol[symbol].append(path)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item):
        self.current_case = item.nodeid
        try:
            yield
        finally:
            self.current_case = None

    def observe_start(self, code, offset):
        symbol = code.co_qualname
        for path in self.paths_by_symbol.get(symbol, ()):
            if code.co_filename.endswith("/" + path):
                if self.current_case is not None:
                    self.reached[path, symbol].add(self.current_case)
                return
        return sys.monitoring.DISABLE


def main():
    suite = Path("tests/integrations/harbor")
    if not suite.is_dir():
        raise SystemExit("Run from the pinned Dressage worktree.")
    boundaries = [(path, symbol) for path, symbols in WATCH.items() for symbol in symbols]
    positions = indexed_functions(Path.cwd())
    indexed = sorted((path, symbol) for path, symbol in positions if symbol)
    observer = OriginalSuiteObserver(set(indexed) | set(boundaries))
    monitor = sys.monitoring
    tool_id = monitor.PROFILER_ID
    monitor.use_tool_id(tool_id, "harbor integration audit")
    try:
        monitor.register_callback(tool_id, monitor.events.PY_START, observer.observe_start)
        monitor.set_events(tool_id, monitor.events.PY_START)
        status = pytest.main([
            "-p", "no:cacheprovider", "-p", "pytest_asyncio.plugin",
            "-o", "asyncio_default_fixture_loop_scope=function",
            "-m", "not harbor_e2e", "--tb=line", "-q", "-r", "f", str(suite),
        ], plugins=[observer])
    finally:
        monitor.set_events(tool_id, 0)
        monitor.register_callback(tool_id, monitor.events.PY_START, None)
        monitor.free_tool_id(tool_id)

    print(f"Harbor {version('harbor')} | pytest exit {int(status)} | distinct test items per method")
    for path, symbol in boundaries:
        print(f"{path} | {symbol} | {len(observer.reached[path, symbol])}")
    entered = sum(bool(observer.reached[key]) for key in indexed)
    print(f"Indexed Dressage functions entered: {entered}/{len(indexed)}")
    print("source file | function | distinct test items | archived lines inside function")
    for path, symbol in indexed:
        lines = ", ".join(map(str, sorted(positions[path, symbol])))
        print(f"{path} | {symbol} | {len(observer.reached[path, symbol])} | {lines}")
    for (path, symbol), lines in positions.items():
        if symbol is None:
            print(f"{path} | module scope | n/a | {', '.join(map(str, sorted(lines)))}")
    return int(status)


if __name__ == "__main__":
    raise SystemExit(main())
