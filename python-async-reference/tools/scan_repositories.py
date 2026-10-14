#!/usr/bin/env python3
"""Inventory tracked Python files without importing or executing target projects.

python3 python-async-reference/tools/scan_repositories.py \
    --repo slime=/path/to/slime --repo areal=/path/to/AReaL --repo verl=/path/to/verl

The existing Slime inventory supplies lexical scopes, AST syntax recording and
source spans. This adapter keeps its output untouched and adds conservative
receiver evidence, repository manifests and reproducible byte snapshots.
"""

import argparse
import ast
import collections
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tokenize
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "python-async-concurrency" / "tools" / "scan.py"
SPEC = importlib.util.spec_from_file_location("_reference_base_scanner", BASE_PATH)
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)
SCHEMA_VERSION = 2
DEFAULT_OUTPUT = ROOT / "python-async-reference" / "repositories"
OFFICIAL_REPOSITORIES = {
    "slime": "https://github.com/THUDM/slime",
    "areal": "https://github.com/areal-project/AReaL",
    "verl": "https://github.com/verl-project/verl",
}
CORE_PACKAGES = {"slime": "slime", "areal": "areal", "verl": "verl"}
FULL_MODULES = {**BASE.FULL_MODULES, "selectors": "selectors"}
BUILTIN_ERRORS = {
    "StopAsyncIteration", "StopIteration", "GeneratorExit", "TimeoutError",
    "ExceptionGroup", "BaseExceptionGroup",
}
BUILTIN_NAMES = {"aiter", "anext"} | BUILTIN_ERRORS
SELECTED_NAMES = {key: set(value) for key, value in BASE.SELECTED_NAMES.items()}
SELECTED_NAMES["builtins"] = BUILTIN_NAMES
SELECTED_NAMES["time"] = {"sleep", "monotonic", "monotonic_ns", "perf_counter", "perf_counter_ns"}
SELECTED_NAMES["inspect"].add("markcoroutinefunction")
SELECTED_NAMES["types"].update({"CoroutineType", "AsyncGeneratorType", "GeneratorType"})
SELECTED_NAMES["unittest"] = {"IsolatedAsyncioTestCase"}
SELECTED_NAMES["unittest.mock"] = {"AsyncMock"}
SELECTED_CATEGORIES = {**BASE.SELECTED_CATEGORIES, "unittest": "async-testing", "unittest.mock": "async-testing"}


def category_for(name, imported=False):
    for module, category in FULL_MODULES.items():
        if name == module or name.startswith(module + "."):
            return category
    if imported and name == "concurrent":
        return "executors"
    for module in sorted(SELECTED_NAMES, key=len, reverse=True):
        if name.startswith(module + "."):
            member = name[len(module) + 1:].split(".")[0]
            if member in SELECTED_NAMES[module] or (module == "os" and member.startswith(("exec", "spawn", "posix_spawn"))):
                if module == "builtins" and member in BUILTIN_ERRORS:
                    return "builtin-exceptions"
                if module == "time" and member != "sleep":
                    return "time-clocks"
                return SELECTED_CATEGORIES[module]
        if imported and name == module:
            return SELECTED_CATEGORIES[module]
    return None


def words(value):
    return set(value.split())


# These tables are evidence rules, not a whitelist of direct APIs. All lexically
# resolved asyncio.* names, including newly added submodules, are recorded.
FUTURE_METHODS = words("""
    cancel cancelled done result exception add_done_callback remove_done_callback
    set_result set_exception get_loop __await__
""")
TASK_METHODS = (FUTURE_METHODS - {"set_result", "set_exception"}) | words("""
    get_stack print_stack get_coro get_context get_name set_name cancelling uncancel
""")
LOOP_METHODS = words("""
    run_until_complete run_forever stop is_running is_closed close shutdown_asyncgens
    shutdown_default_executor call_soon call_soon_threadsafe call_later call_at time
    create_future create_task set_task_factory get_task_factory create_connection
    create_server create_unix_connection create_unix_server connect_accepted_socket
    sendfile start_tls create_datagram_endpoint connect_read_pipe connect_write_pipe
    subprocess_exec subprocess_shell add_reader remove_reader add_writer remove_writer
    sock_recv sock_recv_into sock_recvfrom sock_recvfrom_into sock_sendall sock_sendto
    sock_accept sock_connect sock_sendfile getaddrinfo getnameinfo add_signal_handler
    remove_signal_handler run_in_executor set_default_executor set_exception_handler
    get_exception_handler default_exception_handler call_exception_handler get_debug
    set_debug
""")
QUEUE_METHODS = words("""
    qsize empty full put put_nowait get get_nowait task_done join shutdown
""")
CONTEXT_METHODS = {"__enter__", "__exit__"}
ASYNC_CONTEXT_METHODS = {"__aenter__", "__aexit__"}
TRANSPORT_METHODS = words("""
    close is_closing get_extra_info set_protocol get_protocol
""")
READ_TRANSPORT_METHODS = TRANSPORT_METHODS | words("is_reading pause_reading resume_reading")
WRITE_TRANSPORT_METHODS = TRANSPORT_METHODS | words("""
    set_write_buffer_limits get_write_buffer_size get_write_buffer_limits write
    writelines write_eof can_write_eof abort
""")
METHODS = {
    "asyncio.Future": FUTURE_METHODS,
    "asyncio.Task": TASK_METHODS,
    "asyncio.AbstractEventLoop": LOOP_METHODS,
    "asyncio.TaskGroup": {"create_task"} | ASYNC_CONTEXT_METHODS,
    "asyncio.Runner": {"run", "get_loop", "close"} | CONTEXT_METHODS,
    "asyncio.Timeout": {"when", "reschedule", "expired"} | ASYNC_CONTEXT_METHODS,
    "asyncio.Lock": {"acquire", "release", "locked"} | ASYNC_CONTEXT_METHODS,
    "asyncio.Event": {"set", "clear", "is_set", "wait"},
    "asyncio.Condition": words("acquire release locked notify notify_all wait wait_for") | ASYNC_CONTEXT_METHODS,
    "asyncio.Semaphore": {"acquire", "release", "locked"} | ASYNC_CONTEXT_METHODS,
    "asyncio.BoundedSemaphore": {"acquire", "release", "locked"} | ASYNC_CONTEXT_METHODS,
    "asyncio.Barrier": {"wait", "reset", "abort"} | ASYNC_CONTEXT_METHODS,
    "asyncio.Queue": QUEUE_METHODS,
    "asyncio.PriorityQueue": QUEUE_METHODS,
    "asyncio.LifoQueue": QUEUE_METHODS,
    "asyncio.StreamReader": words("read readline readuntil readexactly at_eof exception feed_eof feed_data set_exception __aiter__ __anext__"),
    "asyncio.StreamWriter": words("write writelines close is_closing wait_closed can_write_eof write_eof drain get_extra_info start_tls"),
    "asyncio.Server": words("get_loop is_serving start_serving serve_forever close close_clients abort_clients wait_closed") | ASYNC_CONTEXT_METHODS,
    "asyncio.subprocess.Process": words("wait communicate send_signal terminate kill"),
    "asyncio.Handle": {"cancel", "cancelled", "get_context"},
    "asyncio.TimerHandle": {"cancel", "cancelled", "get_context", "when"},
    "asyncio.BaseTransport": TRANSPORT_METHODS,
    "asyncio.ReadTransport": READ_TRANSPORT_METHODS,
    "asyncio.WriteTransport": WRITE_TRANSPORT_METHODS,
    "asyncio.Transport": READ_TRANSPORT_METHODS | WRITE_TRANSPORT_METHODS,
    "asyncio.DatagramTransport": TRANSPORT_METHODS | {"sendto", "abort"},
    "asyncio.SubprocessTransport": TRANSPORT_METHODS | words("get_pid get_pipe_transport get_returncode send_signal terminate kill"),
    "asyncio.Protocol": words("connection_made connection_lost data_received eof_received pause_writing resume_writing"),
    "asyncio.BufferedProtocol": words("connection_made connection_lost get_buffer buffer_updated eof_received pause_writing resume_writing"),
    "asyncio.DatagramProtocol": words("connection_made connection_lost datagram_received error_received"),
    "asyncio.SubprocessProtocol": words("connection_made connection_lost pipe_data_received pipe_connection_lost process_exited"),
    "asyncio.AbstractEventLoopPolicy": words("get_event_loop set_event_loop new_event_loop get_child_watcher set_child_watcher"),
    "threading.Thread": words("start run join is_alive getName setName isDaemon setDaemon"),
    "threading.Timer": words("start run join is_alive cancel"),
    "threading.Lock": {"acquire", "release", "locked"} | CONTEXT_METHODS,
    "threading.RLock": {"acquire", "release", "locked"} | CONTEXT_METHODS,
    "threading.Condition": words("acquire release locked notify notify_all wait wait_for") | CONTEXT_METHODS,
    "threading.Event": words("set clear is_set wait"),
    "threading.Semaphore": {"acquire", "release"} | CONTEXT_METHODS,
    "threading.BoundedSemaphore": {"acquire", "release"} | CONTEXT_METHODS,
    "threading.Barrier": {"wait", "reset", "abort"},
    "queue.Queue": QUEUE_METHODS,
    "queue.SimpleQueue": words("qsize empty put put_nowait get get_nowait"),
    "queue.PriorityQueue": QUEUE_METHODS,
    "queue.LifoQueue": QUEUE_METHODS,
    "concurrent.futures.Future": FUTURE_METHODS - {"get_loop", "__await__", "remove_done_callback"} | {"running", "set_running_or_notify_cancel"},
    "concurrent.futures.ThreadPoolExecutor": {"submit", "map", "shutdown"} | CONTEXT_METHODS,
    "concurrent.futures.ProcessPoolExecutor": {"submit", "map", "shutdown", "terminate_workers", "kill_workers"} | CONTEXT_METHODS,
    "multiprocessing.Process": words("start run join is_alive terminate kill close interrupt"),
    "multiprocessing.Pool": words("apply apply_async map map_async imap imap_unordered starmap starmap_async close terminate join") | CONTEXT_METHODS,
    "multiprocessing.Queue": words("qsize empty full put put_nowait get get_nowait close join_thread cancel_join_thread"),
    "multiprocessing.SimpleQueue": {"empty", "put", "get", "close"},
    "multiprocessing.JoinableQueue": words("qsize empty full put put_nowait get get_nowait close join_thread cancel_join_thread task_done join"),
    "multiprocessing.Lock": {"acquire", "release", "locked"} | CONTEXT_METHODS,
    "multiprocessing.RLock": {"acquire", "release", "locked"} | CONTEXT_METHODS,
    "multiprocessing.Event": words("set clear is_set wait"),
    "multiprocessing.Condition": words("acquire release wait wait_for notify notify_all") | CONTEXT_METHODS,
    "multiprocessing.Semaphore": {"acquire", "release", "get_value"} | CONTEXT_METHODS,
    "multiprocessing.BoundedSemaphore": {"acquire", "release", "get_value"} | CONTEXT_METHODS,
    "multiprocessing.Barrier": {"wait", "reset", "abort"},
    "multiprocessing.context.BaseContext": words("Process Pool Queue SimpleQueue JoinableQueue Lock RLock Event Condition Semaphore BoundedSemaphore Barrier Pipe Manager get_start_method set_start_method"),
    "multiprocessing.connection.Connection": words("send recv send_bytes recv_bytes recv_bytes_into poll close") | CONTEXT_METHODS,
    "multiprocessing.pool.AsyncResult": words("get wait ready successful"),
    "subprocess.Popen": words("poll wait communicate send_signal terminate kill") | CONTEXT_METHODS,
    "contextvars.ContextVar": {"get", "set", "reset"},
    "contextvars.Context": words("run copy get keys values items __enter__ __exit__"),
    "contextvars.Token": CONTEXT_METHODS,
    "contextlib.AsyncExitStack": words("enter_context enter_async_context push push_async_exit callback push_async_callback pop_all aclose") | ASYNC_CONTEXT_METHODS,
    "selectors.BaseSelector": words("register unregister modify select close get_key get_map fileno") | CONTEXT_METHODS,
    "unittest.mock.AsyncMock": words("""
        assert_awaited assert_awaited_once assert_awaited_with assert_awaited_once_with
        assert_any_await assert_has_awaits assert_not_awaited reset_mock
    """),
    "unittest.IsolatedAsyncioTestCase": words("asyncSetUp asyncTearDown addAsyncCleanup enterAsyncContext"),
}

TYPE_ALIASES = {}
for module, names in {
    "asyncio.tasks": "Task",
    "asyncio.futures": "Future",
    "asyncio.locks": "Lock Event Condition Semaphore BoundedSemaphore Barrier",
    "asyncio.queues": "Queue PriorityQueue LifoQueue",
    "asyncio.taskgroups": "TaskGroup",
    "asyncio.runners": "Runner",
    "asyncio.timeouts": "Timeout",
    "asyncio.streams": "StreamReader StreamWriter",
    "asyncio.events": "AbstractEventLoop AbstractEventLoopPolicy Handle TimerHandle",
    "asyncio.transports": "BaseTransport ReadTransport WriteTransport Transport DatagramTransport SubprocessTransport",
    "asyncio.protocols": "Protocol BufferedProtocol DatagramProtocol SubprocessProtocol",
    "concurrent.futures.thread": "ThreadPoolExecutor",
    "concurrent.futures.process": "ProcessPoolExecutor",
    "concurrent.futures._base": "Future",
}.items():
    public_module = "concurrent.futures" if module.startswith("concurrent.") else "asyncio"
    for name in names.split():
        TYPE_ALIASES[f"{module}.{name}"] = f"{public_module}.{name}"
for name in ("BaseEventLoop", "SelectorEventLoop", "ProactorEventLoop"):
    TYPE_ALIASES[f"asyncio.{name}"] = "asyncio.AbstractEventLoop"
for name in ("DefaultEventLoopPolicy", "WindowsSelectorEventLoopPolicy", "WindowsProactorEventLoopPolicy"):
    TYPE_ALIASES[f"asyncio.{name}"] = "asyncio.AbstractEventLoopPolicy"
for name in ("DefaultSelector", "SelectSelector", "PollSelector", "EpollSelector", "DevpollSelector", "KqueueSelector"):
    TYPE_ALIASES[f"selectors.{name}"] = "selectors.BaseSelector"

CONSTRUCTORS = set(BASE.CONSTRUCTORS) | set(METHODS) | set(TYPE_ALIASES)
SYNC_FACTORIES = {
    **BASE.RETURN_TYPES,
    "asyncio.timeout": "asyncio.Timeout",
    "asyncio.timeout_at": "asyncio.Timeout",
    "asyncio.get_event_loop_policy": "asyncio.AbstractEventLoopPolicy",
    "contextlib.aclosing": "contextlib.aclosing",
}
ASYNC_FACTORIES = {
    "asyncio.create_subprocess_exec": "asyncio.subprocess.Process",
    "asyncio.create_subprocess_shell": "asyncio.subprocess.Process",
    "asyncio.start_server": "asyncio.Server",
    "asyncio.start_unix_server": "asyncio.Server",
    "asyncio.open_connection": ("asyncio.StreamReader", "asyncio.StreamWriter"),
    "asyncio.open_unix_connection": ("asyncio.StreamReader", "asyncio.StreamWriter"),
}
for name in ASYNC_FACTORIES:
    SYNC_FACTORIES.pop(name, None)
METHOD_FACTORIES = {
    ("asyncio.TaskGroup", "create_task"): "asyncio.Task",
    ("asyncio.Runner", "get_loop"): "asyncio.AbstractEventLoop",
    ("asyncio.AbstractEventLoop", "create_task"): "asyncio.Task",
    ("asyncio.AbstractEventLoop", "create_future"): "asyncio.Future",
    ("asyncio.AbstractEventLoop", "run_in_executor"): "asyncio.Future",
    ("asyncio.AbstractEventLoop", "call_soon"): "asyncio.Handle",
    ("asyncio.AbstractEventLoop", "call_soon_threadsafe"): "asyncio.Handle",
    ("asyncio.AbstractEventLoop", "call_at"): "asyncio.TimerHandle",
    ("asyncio.AbstractEventLoop", "call_later"): "asyncio.TimerHandle",
    ("asyncio.AbstractEventLoopPolicy", "get_event_loop"): "asyncio.AbstractEventLoop",
    ("asyncio.AbstractEventLoopPolicy", "new_event_loop"): "asyncio.AbstractEventLoop",
    ("concurrent.futures.ThreadPoolExecutor", "submit"): "concurrent.futures.Future",
    ("concurrent.futures.ProcessPoolExecutor", "submit"): "concurrent.futures.Future",
    ("contextvars.ContextVar", "set"): "contextvars.Token",
    ("contextvars.Context", "copy"): "contextvars.Context",
    ("contextlib.AsyncExitStack", "pop_all"): "contextlib.AsyncExitStack",
}
ASYNC_METHOD_FACTORIES = {
    ("asyncio.AbstractEventLoop", "create_server"): "asyncio.Server",
    ("asyncio.AbstractEventLoop", "create_unix_server"): "asyncio.Server",
    ("asyncio.AbstractEventLoop", "sock_accept"): None,
    ("contextlib.AsyncExitStack", "__aenter__"): "contextlib.AsyncExitStack",
}
CANDIDATE_METHODS = set(BASE.CANDIDATE_METHODS)
for methods in METHODS.values():
    CANDIDATE_METHODS.update(methods)
SYNTAX_KINDS = {
    "async_def", "async_generator_def", "async_protocol_def", "await", "async_with",
    "async_for", "async_comprehension", "async_yield",
}
KIND_ORDER = {**BASE.KIND_ORDER, "inferred_method": 11, "instance_candidate": 12}
ASYNC_ENTER_SELF = {"asyncio.TaskGroup", "asyncio.Timeout", "asyncio.Server", "contextlib.AsyncExitStack"}
SYNC_ENTER_SELF = {
    "asyncio.Runner", "concurrent.futures.ThreadPoolExecutor", "concurrent.futures.ProcessPoolExecutor",
    "multiprocessing.Pool", "subprocess.Popen", "multiprocessing.connection.Connection",
    "selectors.BaseSelector",
}


def canonical_type(name):
    return TYPE_ALIASES.get(name, name)


def file_scope(filename, repository_name):
    parts = Path(filename).parts
    if any(part in {"test", "tests", "testing"} for part in parts[:-1]) or parts[-1].startswith("test_"):
        return "tests"
    if any(part in {"example", "examples", "tutorial", "tutorials"} for part in parts[:-1]):
        return "examples"
    if parts[0] == CORE_PACKAGES.get(repository_name, repository_name):
        return "core"
    return "other"


class PatternBindings(ast.NodeVisitor):
    """Collect capture-name strings missed by the legacy Name-based collector."""

    def __init__(self, scope):
        self.scope = scope

    def visit_MatchAs(self, node):
        if node.name:
            self.scope.locals.add(node.name)
            self.scope.assigned.add(node.name)
        self.generic_visit(node)

    visit_MatchStar = visit_MatchAs

    def visit_MatchMapping(self, node):
        if node.rest:
            self.scope.locals.add(node.rest)
            self.scope.assigned.add(node.rest)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        pass

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef


class AssignedTargets(ast.NodeVisitor):
    """Names potentially overwritten during a loop iteration or try arm."""

    def __init__(self):
        self.keys = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.keys.add(node.id)

    def visit_Attribute(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)) and BASE.dotted(node):
            self.keys.add(BASE.dotted(node))
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.keys.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef

    def visit_Lambda(self, node):
        pass

    def visit_Import(self, node):
        self.keys.update(alias.asname or alias.name.split(".")[0] for alias in node.names)

    def visit_ImportFrom(self, node):
        self.keys.update(alias.asname or alias.name for alias in node.names)

    def visit_ExceptHandler(self, node):
        if node.name:
            self.keys.add(node.name)
        self.generic_visit(node)


class EvidenceScope(BASE.Scope):
    """Local evidence never falls back past a local binding or to another method."""

    def __init__(self, node, parent=None):
        super().__init__(node, parent)
        collector = PatternBindings(self)
        for child in getattr(node, "body", []) if not isinstance(node, ast.Lambda) else []:
            collector.visit(child)
        self.locals.difference_update(self.globals | self.nonlocals)

    def lookup(self, name):
        if name in (self.globals | self.nonlocals) and name in self.assigned:
            return None
        if name in self.globals and self.parent:
            scope = self.parent
            while scope.parent:
                scope = scope.parent
            return scope.lookup(name)
        if name in self.imports and name not in self.assigned and len(self.imports[name]) == 1:
            return next(iter(self.imports[name]))
        if name in self.locals:
            return None
        parent = self.parent
        if self.kind == "function":
            while parent and parent.kind == "class":
                parent = parent.parent
        if parent:
            return parent.lookup(name)
        if name in BUILTIN_NAMES:
            return "builtins." + name
        return None

    def instance(self, key):
        if not key:
            return None
        first = key.split(".", 1)[0]
        if first in self.globals or first in self.nonlocals:
            return None
        if key in self.instances:
            return self.instances[key]
        if first in self.locals:
            return None
        if self.parent and self.parent.kind != "class":
            return self.parent.instance(key)
        return None


class RepositoryVisitor(BASE.InventoryVisitor):
    def __init__(self, filename, text, head, repository, repository_name):
        super().__init__(filename, text, head)
        self.repository = repository
        self.repository_name = repository_name

    def add(self, node, kind, category, name, provenance, details=None, expression=None):
        super().add(node, kind, category, name, provenance, details, expression)
        event = self.events[-1]
        event["canonical_name"] = name if kind in {"import", "api_call", "api_reference"} else None
        event["resolution"] = "direct" if kind != "instance_candidate" else "unresolved"
        event["scope"] = file_scope(self.filename, self.repository_name)
        end = event["end_line"]
        fragment = f"#L{event['line']}" + (f"-L{end}" if end != event["line"] else "")
        event["source_url"] = f"{self.repository}/blob/{self.head}/{quote(self.filename)}{fragment}"

    def enter_scope(self, node):
        previous = self.scope
        self.scope = self.scopes.setdefault(id(node), EvidenceScope(node, previous))
        for imp, alias, name in self.scope.import_nodes:
            category = category_for(name, imported=True)
            if category:
                self.add(alias, "import", category, name, "explicit_import", {
                    "local_binding": alias.asname or (alias.name if isinstance(imp, ast.ImportFrom) else alias.name.split(".")[0]),
                    "statement_line": imp.lineno,
                    "selective_module_import": name in SELECTED_NAMES,
                }, expression=self.expression(imp))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for argument in ast.walk(node.args):
                if isinstance(argument, ast.arg) and argument.annotation:
                    evidence = self.annotation_evidence(argument.annotation, previous)
                    if evidence:
                        self.scope.instances[argument.arg] = evidence
        for child in getattr(node, "body", []):
            self.visit(child)
        self.scope = previous

    def native_reference(self, node):
        parent = self.parents.get(id(node))
        if isinstance(parent, ast.Attribute) and parent.value is node:
            return
        if not isinstance(node.ctx, ast.Load) and not isinstance(node, ast.Attribute):
            return
        name = self.resolve(node)
        category = category_for(name) if name else None
        if category:
            called = isinstance(parent, ast.Call) and parent.func is node
            self.add(node, "api_call" if called else "api_reference", category, name,
                     "unshadowed_builtin" if name.startswith("builtins.") else "lexical_import_resolution",
                     {"access": type(node.ctx).__name__.lower()})

    def invalidate_key(self, key):
        self.scope.instances[key] = None
        for existing in list(self.scope.instances):
            if existing.startswith(key + "."):
                self.scope.instances[existing] = None

    def invalidate_assigned(self, bodies):
        assigned = AssignedTargets()
        for body in bodies:
            for node in body:
                assigned.visit(node)
        for key in assigned.keys:
            self.invalidate_key(key)

    def function(self, node, asynchronous):
        self.invalidate_key(node.name)
        super().function(node, asynchronous)

    def visit_ClassDef(self, node):
        self.invalidate_key(node.name)
        super().visit_ClassDef(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.invalidate_key(alias.asname or alias.name.split(".")[0])

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.invalidate_key(alias.asname or alias.name)

    def annotation_evidence(self, node, scope=None):
        original = node
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                node = ast.parse(node.value, mode="eval").body
            except SyntaxError:
                return None
        if isinstance(node, ast.Subscript):
            node = node.value
        previous = self.scope
        if scope is not None:
            self.scope = scope
        name = self.resolve(node)
        self.scope = previous
        if name in CONSTRUCTORS:
            return self.evidence(canonical_type(name), "annotation", original)
        return None

    def evidence(self, typename, reason, node, **extra):
        return {"type": typename, "evidence": reason, "line": getattr(node, "lineno", 1),
                "expression": self.expression(node), **extra}

    def infer(self, node, awaited=False):
        if isinstance(node, ast.Await):
            return self.infer(node.value, awaited=True)
        if not isinstance(node, ast.Call):
            return None if awaited else self.scope.instance(BASE.dotted(node))
        name = self.resolve(node.func)
        if name in ASYNC_FACTORIES:
            if not awaited:
                return None
            result = ASYNC_FACTORIES[name]
        elif awaited:
            result = None
        elif name in CONSTRUCTORS:
            result = canonical_type(name)
        else:
            result = SYNC_FACTORIES.get(name)
        if result:
            return self.evidence(result, "awaited_known_factory" if awaited else "constructor_or_known_factory", node)
        if isinstance(node.func, ast.Attribute):
            receiver = self.infer(node.func.value)
            if not receiver or not isinstance(receiver["type"], str):
                return None
            owner, method = receiver["type"], node.func.attr
            mapping = ASYNC_METHOD_FACTORIES if awaited else METHOD_FACTORIES
            result = mapping.get((owner, method))
            if not awaited and owner == "multiprocessing.context.BaseContext" and f"multiprocessing.{method}" in CONSTRUCTORS:
                result = f"multiprocessing.{method}"
            if not awaited and owner == "multiprocessing.Pool" and method in {"apply_async", "map_async", "starmap_async"}:
                result = "multiprocessing.pool.AsyncResult"
            if result:
                return self.evidence(result, "known_factory_on_inferred_receiver", node, receiver_evidence=receiver)
        return None

    def set_evidence(self, target, evidence):
        if isinstance(target, (ast.Tuple, ast.List)):
            types = evidence.get("type") if evidence else None
            if isinstance(types, tuple) and len(types) == len(target.elts):
                for element, typename in zip(target.elts, types):
                    self.set_evidence(element, {**evidence, "type": typename})
            else:
                for element in target.elts:
                    self.set_evidence(element, None)
            return
        key = BASE.dotted(target)
        if key:
            # A tombstone prevents fallback to evidence in a parent scope.
            self.invalidate_key(key)
            self.scope.instances[key] = evidence

    def bind_instance(self, target, value):
        self.set_evidence(target, self.infer(value))

    def visit_AnnAssign(self, node):
        self.visit(node.annotation)
        if node.value is not None:
            self.visit(node.value)
            # An incompatible or unknown assignment must not inherit its hint.
            evidence = self.infer(node.value)
        else:
            evidence = self.annotation_evidence(node.annotation)
        self.set_evidence(node.target, evidence)
        self.visit(node.target)

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        self.set_evidence(node.target, None)

    def visit_NamedExpr(self, node):
        self.visit(node.value)
        self.bind_instance(node.target, node.value)

    def visit_Delete(self, node):
        for target in node.targets:
            self.set_evidence(target, None)
            self.visit(target)

    def visit_With(self, node):
        returns_self = ASYNC_ENTER_SELF if isinstance(node, ast.AsyncWith) else SYNC_ENTER_SELF
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars:
                evidence = self.infer(item.context_expr)
                if evidence and isinstance(evidence["type"], str) and evidence["type"] in returns_self:
                    evidence = {**evidence, "context_result": "documented_enter_returns_self"}
                else:
                    evidence = None
                self.set_evidence(item.optional_vars, evidence)
                self.visit(item.optional_vars)
        for child in node.body:
            self.visit(child)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            resolved = self.resolve(node.func)
            if not (resolved and category_for(resolved)):
                evidence = self.infer(node.func.value)
                owner = evidence["type"] if evidence else None
                method = node.func.attr
                known = isinstance(owner, str) and method in METHODS.get(owner, set())
                if known or method in CANDIDATE_METHODS:
                    self.add(node.func, "instance_candidate", "candidates", method,
                             "inferred_receiver_candidate" if evidence else "unresolved_receiver_candidate", {
                                 "receiver": self.expression(node.func.value),
                                 "receiver_evidence": evidence,
                                 "resolved_non_native_name": resolved,
                             })
                    if known:
                        event = self.events[-1]
                        event.update(kind="inferred_method", category=category_for(owner),
                                     name=f"{owner}.{method}", canonical_name=f"{owner}.{method}",
                                     resolution="inferred", provenance="known_receiver_method")
        self.generic_visit(node)

    def visit_If(self, node):
        self.visit(node.test)
        self.branch_bodies([node.body, node.orelse])

    def branch_bodies(self, bodies):
        before = self.scope.instances.copy()
        changed = set()
        for body in bodies:
            self.scope.instances = before.copy()
            for child in body:
                self.visit(child)
            changed.update(key for key, value in self.scope.instances.items() if before.get(key) != value)
        self.scope.instances = before
        # Even identical-looking branch evidence is not a control-flow proof.
        for key in changed:
            self.scope.instances[key] = None

    def visit_For(self, node):
        self.visit(node.iter)
        self.set_evidence(node.target, None)
        self.visit(node.target)
        self.invalidate_assigned([node.body])
        self.branch_bodies([node.body, node.orelse])

    def visit_AsyncFor(self, node):
        self.add(node, "async_for", "syntax", "async for", "python_ast", expression=self.lines[node.lineno - 1])
        self.visit_For(node)

    def visit_While(self, node):
        self.visit(node.test)
        self.invalidate_assigned([node.body])
        self.branch_bodies([node.body, node.orelse])

    def visit_Try(self, node):
        # Exceptions can leave assignments partially executed. Process each arm
        # for occurrences, but never promote arm-local evidence beyond it.
        bodies = [node.body, node.orelse] + [[handler] for handler in node.handlers]
        self.invalidate_assigned(bodies)
        self.branch_bodies(bodies)
        for child in node.finalbody:
            self.visit(child)

    visit_TryStar = visit_Try

    def visit_ExceptHandler(self, node):
        if node.type:
            self.visit(node.type)
        if node.name:
            self.scope.instances[node.name] = None
        for child in node.body:
            self.visit(child)

    def visit_Match(self, node):
        self.visit(node.subject)
        for case in node.cases:
            for pattern in ast.walk(case.pattern):
                name = getattr(pattern, "name", None) or getattr(pattern, "rest", None)
                if isinstance(name, str):
                    self.scope.instances[name] = None
            if case.guard:
                self.visit(case.guard)
        self.branch_bodies([case.body for case in node.cases])

    def visit_Lambda(self, node):
        self.visit(node.args)
        previous = self.scope
        self.scope = EvidenceScope(node, previous)
        self.visit(node.body)
        self.scope = previous

    def comprehension(self, node):
        previous = self.scope
        self.visit(node.generators[0].iter)
        scope = EvidenceScope(ast.Lambda(args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]), body=ast.Constant(None)), previous)
        scope.symbol = previous.symbol + ".<comprehension>"
        for generator in node.generators:
            scope.locals.update(BASE.target_names(generator.target))
        self.scope = scope
        for index, generator in enumerate(node.generators):
            if index:
                self.visit(generator.iter)
            if generator.is_async:
                self.add(generator.iter, "async_comprehension", "syntax", "async comprehension", "python_ast", {"clause_index": index})
            for test in generator.ifs:
                self.visit(test)
        if isinstance(node, ast.DictComp):
            self.visit(node.key)
            self.visit(node.value)
        else:
            self.visit(node.elt)
        self.scope = previous

    visit_ListComp = comprehension
    visit_SetComp = comprehension
    visit_DictComp = comprehension
    visit_GeneratorExp = comprehension

    def finish(self):
        # Keep unknown candidates even in files with no native async API: they
        # are an explicit review queue, never an affirmative ownership claim.
        used = {event["canonical_name"] for event in self.events
                if event["kind"] not in {"import", "instance_candidate"} and event["canonical_name"]}
        return [event for event in self.events if not (
            event["kind"] == "import" and event["details"].get("selective_module_import")
            and not any(name.startswith(event["name"] + ".") for name in used))]


def scan_source(source, filename="example.py", head="0" * 40,
                repository="https://github.com/THUDM/slime", repository_name="slime"):
    tree = ast.parse(source, filename=filename, type_comments=True)
    visitor = RepositoryVisitor(filename, source, head, repository, repository_name)
    visitor.visit(tree)
    return sorted(visitor.finish(), key=lambda row: (row["line"], row["col"], KIND_ORDER[row["kind"]], row["name"]))


def summarize(events):
    kinds = collections.Counter(event["kind"] for event in events)
    return {
        "total_static_occurrences": len(events),
        "imports": kinds["import"],
        "direct_calls": kinds["api_call"],
        "references": kinds["api_reference"],
        "direct_native_api_occurrences": kinds["api_call"] + kinds["api_reference"],
        "inferred_methods": kinds["inferred_method"],
        "syntax_occurrences": sum(kinds[kind] for kind in SYNTAX_KINDS),
        "instance_candidates": kinds["instance_candidate"],
        "by_kind": {kind: kinds[kind] for kind in KIND_ORDER},
    }


COUNTING_POLICY = {
    "unit": "Static source occurrences, never runtime executions or API mastery.",
    "direct_api": "Lexically resolved import names; one maximal expression is either api_call or api_reference, never both. Unknown asyncio.* members remain visible for catalog reconciliation.",
    "imports": "One alias per import; selected broad standard-library module imports require another relevant use in the file.",
    "inferred_methods": "Known constructors, selected factories or explicit annotations plus a receiver-specific method table. Kept separate from direct API calls and references.",
    "candidates": "Unresolved method-name matches in all tracked Python files, including third-party and custom objects. canonical_name=null; excluded from native API totals.",
    "syntax": "One AST node per syntax kind; async_def excludes async_generator_def; async_yield separately counts each yield in an async generator.",
    "scope": "tests: any test/tests/testing directory or test_ filename; examples: example/examples/tutorial/tutorials directory; core: primary package; otherwise other. Applied in this precedence.",
    "columns": "One-based lines, zero-based UTF-8 byte columns from ast, end columns exclusive.",
    "full_modules": FULL_MODULES,
    "selected_module_members": {module: sorted(names) for module, names in sorted(SELECTED_NAMES.items())},
}
LIMITATIONS = [
    "Static lexical resolution and deliberately shallow evidence rules; no imports, training, GPU work, runtime execution, full type checking or whole-program data-flow analysis.",
    "Function parameters and assignments shadow imported names; ambiguous or reassigned import bindings are conservatively unresolved, even before the reassignment.",
    "Instance evidence is local to a scope. Class fields are not transferred between methods; containers, inheritance, arbitrary function returns and cross-module re-exports are not inferred.",
    "Assignments, deletion and loop targets invalidate prior receiver evidence. Branch-local evidence is discarded after conditional/loop/try arms; path reachability and exception flow are not proven.",
    "Explicit annotations and selected factories are clues, not runtime type proof. Inferred methods stay separate from direct calls. Monkey-patching, dynamic imports, star imports, getattr and mutation through aliases are not resolved.",
    "Known async factories require await before their result type is inferred. Arbitrary await results, nested containers and Optional/Union annotations are not inferred.",
    "The method-name review queue includes unrelated third-party/custom .get/.wait/.create_task calls; candidates never establish Python-native ownership.",
    "Direct asyncio.* references cover new submodules automatically, but unknown/private/removed names are not proof of membership in a specific Python version; reconcile with the official catalog.",
    "Only current bytes at git ls-files paths ending in .py are scanned. Untracked files, notebooks, strings containing code, dependencies and non-Python examples are excluded.",
    "GitHub links are pinned to HEAD. When tracked files differ from HEAD, hashes and byte snapshots describe the local scan; the remote link may show different content.",
]


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args]).decode("utf-8").strip()


def repository_url(name, remote):
    if name in OFFICIAL_REPOSITORIES:
        return OFFICIAL_REPOSITORIES[name]
    match = re.fullmatch(r"git@([^:]+):(.+?)(?:\.git)?", remote)
    if match:
        return f"https://{match[1]}/{match[2]}"
    if remote.startswith(("https://", "http://")):
        return remote.removesuffix(".git").rstrip("/")
    raise ValueError(f"No official or HTTP repository URL available for {name!r}")


def build_repository(name, root):
    root = Path(root).resolve()
    if root != Path(git(root, "rev-parse", "--show-toplevel")).resolve():
        raise ValueError("--repo paths must name Git repository roots")
    head = git(root, "rev-parse", "HEAD")
    remotes = git(root, "remote").splitlines()
    remote = git(root, "remote", "get-url", "origin") if "origin" in remotes else ""
    url = repository_url(name, remote)
    status_before = git(root, "status", "--porcelain=v1", "--untracked-files=normal")
    paths = sorted(set(path for path in git(root, "ls-files", "-z").split("\0") if path.endswith(".py")))
    changes = sorted(filter(None, git(root, "diff", "HEAD", "--name-only", "-z", "--", "*.py").split("\0")))
    events, files, errors, snapshots = [], [], [], {}
    for filename in paths:
        metadata = {"file": filename, "scope": file_scope(filename, name)}
        found = []
        try:
            raw = (root / filename).read_bytes()
            metadata.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
            source = raw.decode(encoding)
            found = scan_source(source, filename, head, url, name)
            metadata.update(parse_status="ok", encoding=encoding)
            if found:
                snapshots["source_snapshot/" + filename + ".txt"] = raw
        except (SyntaxError, UnicodeError, OSError, ValueError) as error:
            metadata.setdefault("sha256", None)
            metadata.setdefault("bytes", None)
            metadata.update(parse_status="missing" if isinstance(error, FileNotFoundError) else "error", parse_error=str(error))
            errors.append({"file": filename, "error": str(error)})
        metadata.update(summarize(found))
        events.extend(found)
        files.append(metadata)
    # Fail instead of publishing an inventory assembled across two checkouts.
    if head != git(root, "rev-parse", "HEAD") or status_before != git(root, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise ValueError(f"{name}: Git HEAD or working-tree status changed during the scan; rerun")
    for index, event in enumerate(events, 1):
        event["id"] = f"{name}-occ-{index:06d}"
    summary = {
        **summarize(events), "source_head": head, "tracked_python_files": len(paths),
        "relevant_python_files": len(snapshots), "parse_error_count": len(errors),
        "async_definitions_total": sum(row["kind"] in {"async_def", "async_generator_def"} for row in events),
        "by_scope": {scope: summarize([row for row in events if row["scope"] == scope]) for scope in ("core", "tests", "examples", "other")},
        "by_category": {category: summarize([row for row in events if row["category"] == category]) for category in sorted({row["category"] for row in events})},
    }
    inventory = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "name": name, "repository": url, "origin_remote": remote, "head": head,
            "root": str(root), "scope": "git ls-files: all tracked paths ending in .py",
            "working_tree_policy": "Scan current tracked bytes, including local modifications; record HEAD, status and hashes; ignore untracked files.",
            "status_porcelain_v1": status_before,
            "tracked_python_changes_from_head": changes,
            "tracked_python_file_count": len(paths), "parse_errors": errors, "files": files,
        },
        "scanner": {
            "adapter": str(Path(__file__).resolve().relative_to(ROOT)),
            "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "base": str(BASE_PATH.relative_to(ROOT)),
            "base_sha256": hashlib.sha256(BASE_PATH.read_bytes()).hexdigest(),
            "python_implementation": sys.implementation.name,
            "python_version": ".".join(map(str, sys.version_info[:3])),
        },
        "counting_policy": COUNTING_POLICY, "limitations": LIMITATIONS,
        "summary": summary, "occurrences": events,
    }
    artifacts = {"inventory.json": BASE.json_bytes(inventory), **snapshots}
    return artifacts, inventory


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", action="append", required=True, metavar="NAME=PATH")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Compare output without writing or deleting any file.")
    args = parser.parse_args(argv)
    repositories = {}
    for value in args.repo:
        name, separator, path = value.partition("=")
        if not separator or not path or not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
            parser.error("--repo must be NAME=PATH with a lowercase safe directory name")
        if name in repositories:
            parser.error(f"duplicate --repo name: {name}")
        repositories[name] = Path(path)
    output_root = args.output.resolve()
    for root in repositories.values():
        if output_root.is_relative_to(root.resolve()):
            parser.error("--output must be outside every source repository")
    failed = False
    for name, root in repositories.items():
        try:
            artifacts, inventory = build_repository(name, root)
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            print(f"ERROR {name}: {error}", file=sys.stderr)
            return 2
        output = args.output / name
        managed = {"inventory.json"}
        managed.update(str(path.relative_to(output)) for path in (output / "source_snapshot").rglob("*") if path.is_file())
        stale = sorted(managed - artifacts.keys())
        differences = sorted(path for path, raw in artifacts.items()
                             if not (output / path).is_file() or (output / path).read_bytes() != raw)
        if args.check:
            for path in differences:
                print(f"DIFF {name}/{path}")
            for path in stale:
                print(f"STALE {name}/{path}")
            failed |= bool(differences or stale)
        else:
            for path, raw in artifacts.items():
                destination = output / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)
            for path in stale:
                (output / path).unlink()
        summary = inventory["summary"]
        failed |= bool(summary["parse_error_count"])
        printed_keys = ("source_head", "tracked_python_files", "relevant_python_files", "parse_error_count",
                        "total_static_occurrences", "imports", "direct_calls", "references",
                        "inferred_methods", "syntax_occurrences", "instance_candidates")
        print(json.dumps({"repository": name, "mode": "check" if args.check else "write",
                          **{key: summary[key] for key in printed_keys}}, ensure_ascii=False))
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
