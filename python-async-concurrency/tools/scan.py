#!/usr/bin/env python3
"""Build a deterministic, read-only AST inventory of tracked Slime Python files.

Usage: python3 tools/scan.py SOURCE_ROOT [--check]
Only this inventory directory is written. The source repository is never changed.
"""

import argparse
import ast
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tokenize


SCHEMA_VERSION = 1
OUTPUT_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "https://github.com/THUDM/slime"
FULL_MODULES = {
    "asyncio": "asyncio",
    "threading": "threading",
    "_thread": "threading",
    "queue": "queue",
    "concurrent.futures": "executors",
    "multiprocessing": "multiprocessing",
    "subprocess": "subprocess",
    "signal": "signal",
    "contextvars": "contextvars",
    "select": "select",
}
ASYNC_TYPES = {
    "Awaitable", "Coroutine", "AsyncIterable", "AsyncIterator", "AsyncGenerator",
    "AsyncContextManager",
}
SELECTED_NAMES = {
    "contextlib": {"asynccontextmanager", "AsyncExitStack", "aclosing", "AbstractAsyncContextManager"},
    "inspect": {
        "isawaitable", "iscoroutine", "iscoroutinefunction", "isasyncgen", "isasyncgenfunction",
        "getcoroutinestate", "getcoroutinelocals", "getasyncgenstate", "getasyncgenlocals",
        "CO_COROUTINE", "CO_ASYNC_GENERATOR", "CO_ITERABLE_COROUTINE",
    },
    "typing": ASYNC_TYPES,
    "collections.abc": ASYNC_TYPES,
    "builtins": {"aiter", "anext"},
    "time": {"sleep"},
    "types": {"coroutine"},
    "os": {
        "fork", "forkpty", "_exit", "kill", "killpg", "wait", "waitpid", "waitid",
        "wait3", "wait4", "register_at_fork", "getpid", "getppid", "setsid", "getsid",
        "setpgid", "getpgid", "getpgrp", "setpgrp", "pipe", "pipe2", "pidfd_open",
        "sched_yield", "system", "popen",
    },
    "fcntl": {"flock", "lockf", "LOCK_SH", "LOCK_EX", "LOCK_UN", "LOCK_NB"},
}
SELECTED_CATEGORIES = {
    "contextlib": "contextlib-async", "inspect": "inspect-async", "typing": "async-typing",
    "collections.abc": "async-typing", "builtins": "async-builtins", "time": "time-sleep",
    "types": "coroutine-helpers", "os": "os-process", "fcntl": "fcntl",
}
CATEGORY_DESCRIPTIONS = {
    "syntax": "Python 原生异步语法；async def 与异步生成器定义分开计数。",
    "asyncio": "asyncio 模块的导入、直接调用与非调用引用。",
    "threading": "threading / _thread 原生线程和同步原语。",
    "queue": "queue 标准库队列。",
    "executors": "concurrent.futures 执行器与 Future。",
    "multiprocessing": "multiprocessing 原生进程与进程间通信。",
    "subprocess": "subprocess 子进程创建、控制、通信及常量。",
    "signal": "signal 信号注册、控制及常量。",
    "contextvars": "contextvars 上下文变量与上下文传播。",
    "contextlib-async": "contextlib 异步上下文管理辅助接口。",
    "inspect-async": "inspect 异步对象检查。",
    "async-builtins": "内置 aiter / anext。",
    "async-typing": "typing / collections.abc 异步类型标记。",
    "time-sleep": "邻接机制：time.sleep 阻塞等待。",
    "os-process": "邻接机制：os 进程生命周期、信号和管道接口。",
    "fcntl": "邻接机制：fcntl 文件锁同步。",
    "select": "邻接机制：select I/O 就绪检查。",
    "coroutine-helpers": "types.coroutine 生成器协程兼容辅助接口。",
    "candidates": "相关文件中的实例方法候选；即使有构造或注解证据，也不并入原生 API 计数。",
}
CANDIDATE_METHODS = {
    "cancel", "cancelled", "cancelling", "uncancel", "done", "result", "exception", "running",
    "add_done_callback", "remove_done_callback", "set_result", "set_exception",
    "set_running_or_notify_cancel", "get_loop", "get_name", "set_name", "get_coro",
    "get_stack", "print_stack", "run_forever", "run_until_complete", "run_in_executor",
    "call_soon", "call_soon_threadsafe", "call_later", "call_at", "create_task", "create_future",
    "shutdown_asyncgens", "shutdown_default_executor", "set_default_executor", "set_task_factory",
    "get_task_factory", "set_exception_handler", "get_exception_handler", "call_exception_handler",
    "add_reader", "remove_reader", "add_writer", "remove_writer", "add_signal_handler",
    "remove_signal_handler", "connect_read_pipe", "connect_write_pipe", "create_connection",
    "create_server", "start_tls", "sock_recv", "sock_sendall", "sock_accept",
    "start", "join", "is_alive", "is_running", "is_closed", "stop", "close", "shutdown",
    "terminate", "kill", "send_signal", "wait", "wait_for", "wait_closed", "poll", "communicate",
    "acquire", "release", "locked", "notify", "notify_all", "set", "clear", "is_set",
    "put", "put_nowait", "get", "get_nowait", "qsize", "empty", "full", "task_done",
    "submit", "map", "starmap", "imap", "imap_unordered", "apply", "apply_async", "map_async",
    "starmap_async", "get_context", "Process", "Pool", "Queue", "SimpleQueue", "Pipe", "Manager",
    "send", "recv", "send_bytes", "recv_bytes", "wait_for_handle", "abort", "reset",
    "drain", "write", "read", "readline", "readexactly", "readuntil", "feed_eof",
    "__await__", "__aiter__", "__anext__", "__aenter__", "__aexit__",
}
PROTOCOL_METHODS = {"__await__", "__aiter__", "__anext__", "__aenter__", "__aexit__"}
CONSTRUCTORS = {
    "asyncio.Task", "asyncio.Future", "asyncio.Lock", "asyncio.Event", "asyncio.Condition",
    "asyncio.Semaphore", "asyncio.BoundedSemaphore", "asyncio.Barrier", "asyncio.Queue",
    "asyncio.PriorityQueue", "asyncio.LifoQueue", "asyncio.TaskGroup", "asyncio.Runner",
    "threading.Thread", "threading.Lock", "threading.RLock", "threading.Event", "threading.Condition",
    "threading.Semaphore", "threading.BoundedSemaphore", "threading.Barrier", "threading.Timer",
    "queue.Queue", "queue.SimpleQueue", "queue.PriorityQueue", "queue.LifoQueue",
    "concurrent.futures.ThreadPoolExecutor", "concurrent.futures.ProcessPoolExecutor",
    "concurrent.futures.Future", "multiprocessing.Process", "multiprocessing.Pool",
    "multiprocessing.Queue", "multiprocessing.SimpleQueue", "multiprocessing.JoinableQueue",
    "multiprocessing.Lock", "multiprocessing.RLock", "multiprocessing.Event", "multiprocessing.Condition",
    "multiprocessing.Semaphore", "multiprocessing.BoundedSemaphore", "multiprocessing.Barrier",
    "subprocess.Popen", "contextvars.ContextVar", "contextvars.Context", "contextlib.AsyncExitStack",
}
RETURN_TYPES = {
    "asyncio.get_event_loop": "asyncio.AbstractEventLoop",
    "asyncio.get_running_loop": "asyncio.AbstractEventLoop",
    "asyncio.new_event_loop": "asyncio.AbstractEventLoop",
    "asyncio.create_task": "asyncio.Task", "asyncio.ensure_future": "asyncio.Future",
    "asyncio.run_coroutine_threadsafe": "concurrent.futures.Future",
    "asyncio.current_task": "asyncio.Task", "asyncio.create_subprocess_exec": "asyncio.subprocess.Process",
    "asyncio.create_subprocess_shell": "asyncio.subprocess.Process",
    "multiprocessing.get_context": "multiprocessing.context.BaseContext",
    "contextvars.copy_context": "contextvars.Context", "_thread.allocate_lock": "threading.Lock",
}
KIND_ORDER = {
    "import": 0, "async_def": 1, "async_generator_def": 2, "async_protocol_def": 3,
    "await": 4, "async_with": 5, "async_for": 6, "async_comprehension": 7,
    "async_yield": 8, "api_call": 9, "api_reference": 10, "instance_candidate": 11,
}
TSV_FIELDS = [
    "id", "file", "module", "line", "end_line", "col", "end_col", "symbol", "kind",
    "category", "name", "provenance", "expression", "source_line", "source_url", "snapshot",
    "details",
]


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args]).decode("utf-8").strip()


def category_for(name, imported=False):
    for module, category in FULL_MODULES.items():
        if name == module or name.startswith(module + "."):
            return category
    if imported and name == "concurrent":
        return "executors"
    for module, names in SELECTED_NAMES.items():
        if name.startswith(module + "."):
            member = name[len(module) + 1:].split(".")[0]
            if member in names or (module == "os" and member.startswith(("exec", "spawn", "posix_spawn"))):
                return SELECTED_CATEGORIES[module]
        if imported and name == module:
            return SELECTED_CATEGORIES[module]
    return None


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        if base:
            return base + "." + node.attr
    return None


def target_names(node):
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)}


class Scope:
    def __init__(self, node, parent=None):
        self.node = node
        self.parent = parent
        self.kind = "module" if parent is None else ("class" if isinstance(node, ast.ClassDef) else "function")
        name = getattr(node, "name", "<lambda>")
        self.symbol = "<module>" if parent is None else (name if parent.symbol == "<module>" else parent.symbol + "." + name)
        self.locals = set()
        self.assigned = set()
        self.imports = collections.defaultdict(set)
        self.globals = set()
        self.nonlocals = set()
        self.instances = {}
        self.import_nodes = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            for arg in ast.walk(node.args):
                if isinstance(arg, ast.arg):
                    self.locals.add(arg.arg)
                    self.assigned.add(arg.arg)
        collector = BindingCollector(self)
        for child in getattr(node, "body", []) if not isinstance(node, ast.Lambda) else []:
            collector.visit(child)
        self.locals.difference_update(self.globals | self.nonlocals)

    def lookup(self, name):
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
        if name in {"aiter", "anext"}:
            return "builtins." + name
        return None

    def instance(self, key):
        if key in self.instances:
            return self.instances[key]
        if key and key.startswith(("self.", "cls.")):
            scope = self
            while scope:
                if scope.kind == "class" and key in scope.instances:
                    return scope.instances[key]
                scope = scope.parent
        if key and "." not in key and key not in self.locals and self.parent:
            return self.parent.instance(key)
        return None


class BindingCollector(ast.NodeVisitor):
    def __init__(self, scope):
        self.scope = scope

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.scope.locals.add(node.id)
            self.scope.assigned.add(node.id)

    def visit_Import(self, node):
        for alias in node.names:
            local = alias.asname or alias.name.split(".")[0]
            resolved = alias.name if alias.asname else alias.name.split(".")[0]
            self.scope.locals.add(local)
            self.scope.imports[local].add(resolved)
            self.scope.import_nodes.append((node, alias, alias.name))

    def visit_ImportFrom(self, node):
        for alias in node.names:
            local = alias.asname or alias.name
            resolved = (node.module + "." if node.module else "") + alias.name
            self.scope.locals.add(local)
            if not node.level:
                self.scope.imports[local].add(resolved)
                self.scope.import_nodes.append((node, alias, resolved))

    def visit_Global(self, node):
        self.scope.globals.update(node.names)

    def visit_Nonlocal(self, node):
        self.scope.nonlocals.update(node.names)

    def visit_ExceptHandler(self, node):
        if node.name:
            self.scope.locals.add(node.name)
            self.scope.assigned.add(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.scope.locals.add(node.name)
        self.scope.assigned.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef

    def visit_Lambda(self, node):
        pass

    def visit_ListComp(self, node):
        # Comprehension iteration variables have their own Python 3 scope.
        for generator in node.generators:
            self.visit(generator.iter)
        self.visit(node.elt)

    visit_SetComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_DictComp(self, node):
        for generator in node.generators:
            self.visit(generator.iter)
        self.visit(node.key)
        self.visit(node.value)


class InventoryVisitor(ast.NodeVisitor):
    def __init__(self, filename, text, head):
        self.filename = filename
        self.text = text
        self.lines = text.splitlines()
        self.head = head
        self.events = []
        self.scope = None
        self.scopes = {}
        self.parents = {}
        self.async_generator_stack = []

    def resolve(self, node):
        if isinstance(node, ast.Name):
            return self.scope.lookup(node.id)
        if isinstance(node, ast.Attribute):
            base = self.resolve(node.value)
            return base + "." + node.attr if base else None
        return None

    def expression(self, node):
        return ast.get_source_segment(self.text, node) or ast.unparse(node)

    def add(self, node, kind, category, name, provenance, details=None, expression=None):
        line = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", line)
        self.events.append({
            "file": self.filename, "module": self.filename[:-3].replace("/", "."),
            "line": line, "end_line": end, "col": getattr(node, "col_offset", 0),
            "end_col": getattr(node, "end_col_offset", 0), "symbol": self.scope.symbol,
            "kind": kind, "category": category, "name": name, "provenance": provenance,
            "expression": expression if expression is not None else self.expression(node),
            "source_line": self.lines[line - 1] if self.lines else "",
            "source_url": f"{UPSTREAM}/blob/{self.head}/{self.filename}#L{line}" + (f"-L{end}" if end != line else ""),
            "snapshot": "source_snapshot/" + self.filename + ".txt", "details": details or {},
        })

    def enter_scope(self, node):
        previous = self.scope
        self.scope = self.scopes.setdefault(id(node), Scope(node, previous))
        for imp, alias, name in self.scope.import_nodes:
            category = category_for(name, imported=True)
            if category:
                self.add(alias, "import", category, name, "explicit_import", {
                    "local_binding": alias.asname or alias.name.split(".")[0],
                    "statement_line": imp.lineno,
                    "selective_module_import": name in SELECTED_NAMES,
                }, expression=self.expression(imp))
        for child in getattr(node, "body", []):
            self.visit(child)
        self.scope = previous

    def visit_Module(self, node):
        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                self.parents[id(child)] = parent
        self.enter_scope(node)

    def visit_ClassDef(self, node):
        for child in node.decorator_list + node.bases + [kw.value for kw in node.keywords]:
            self.visit(child)
        self.enter_scope(node)

    def function(self, node, asynchronous):
        for child in node.decorator_list:
            self.visit(child)
        self.visit(node.args)
        if node.returns:
            self.visit(node.returns)
        finder = OwnYieldFinder()
        for child in node.body:
            finder.visit(child)
        generator = asynchronous and finder.found
        if asynchronous:
            self.add(node, "async_generator_def" if generator else "async_def", "syntax", node.name,
                     "python_ast", {"async_protocol": node.name in PROTOCOL_METHODS}, expression=self.lines[node.lineno - 1])
        elif node.name in PROTOCOL_METHODS:
            self.add(node, "async_protocol_def", "syntax", node.name, "python_ast", expression=self.lines[node.lineno - 1])
        self.async_generator_stack.append(generator)
        self.enter_scope(node)
        self.async_generator_stack.pop()

    def visit_FunctionDef(self, node):
        self.function(node, False)

    def visit_AsyncFunctionDef(self, node):
        self.function(node, True)

    def visit_Lambda(self, node):
        self.visit(node.args)
        previous = self.scope
        self.scope = Scope(node, previous)
        self.visit(node.body)
        self.scope = previous

    def visit_Import(self, node):
        pass

    visit_ImportFrom = visit_Import

    def visit_Await(self, node):
        self.add(node, "await", "syntax", "await", "python_ast")
        self.generic_visit(node)

    def visit_AsyncWith(self, node):
        self.add(node, "async_with", "syntax", "async with", "python_ast", {"items": len(node.items)}, expression=self.lines[node.lineno - 1])
        self.visit_With(node)

    def visit_AsyncFor(self, node):
        self.add(node, "async_for", "syntax", "async for", "python_ast", expression=self.lines[node.lineno - 1])
        self.generic_visit(node)

    def visit_Yield(self, node):
        if self.async_generator_stack and self.async_generator_stack[-1]:
            self.add(node, "async_yield", "syntax", "yield in async generator", "python_ast")
        self.generic_visit(node)

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
                     "lexical_import_resolution" if not name.startswith("builtins.") else "unshadowed_builtin",
                     {"access": type(node.ctx).__name__.lower()})

    def visit_Name(self, node):
        self.native_reference(node)

    def visit_Attribute(self, node):
        self.native_reference(node)
        self.generic_visit(node)

    def infer(self, node):
        if isinstance(node, ast.Await):
            return self.infer(node.value)
        if not isinstance(node, ast.Call):
            return self.scope.instance(dotted(node))
        name = self.resolve(node.func)
        inferred = name if name in CONSTRUCTORS else RETURN_TYPES.get(name)
        if inferred:
            return {"type": inferred, "evidence": "constructor_or_known_factory", "line": node.lineno, "expression": self.expression(node)}
        if isinstance(node.func, ast.Attribute):
            receiver = self.infer(node.func.value)
            if receiver:
                owner, method = receiver["type"], node.func.attr
                result = None
                if owner == "multiprocessing.context.BaseContext" and "multiprocessing." + method in CONSTRUCTORS:
                    result = "multiprocessing." + method
                elif owner == "asyncio.AbstractEventLoop" and method in {"create_task", "create_future", "run_in_executor"}:
                    result = {"create_task": "asyncio.Task", "create_future": "asyncio.Future", "run_in_executor": "asyncio.Future"}[method]
                elif owner.startswith("concurrent.futures.") and method == "submit":
                    result = "concurrent.futures.Future"
                if result:
                    return {"type": result, "evidence": "known_factory_on_inferred_receiver", "line": node.lineno, "expression": self.expression(node)}
        return None

    def bind_instance(self, target, value):
        key = dotted(target)
        evidence = self.infer(value)
        if key and evidence:
            self.scope.instances[key] = evidence
            if key.startswith(("self.", "cls.")):
                scope = self.scope.parent
                while scope and scope.kind != "class":
                    scope = scope.parent
                if scope:
                    scope.instances[key] = evidence
        elif key:
            self.scope.instances.pop(key, None)

    def visit_Assign(self, node):
        self.visit(node.value)
        for target in node.targets:
            self.bind_instance(target, node.value)
            self.visit(target)

    def visit_AnnAssign(self, node):
        self.visit(node.annotation)
        if node.value:
            self.visit(node.value)
            self.bind_instance(node.target, node.value)
        else:
            name = self.resolve(node.annotation)
            if name in CONSTRUCTORS:
                self.scope.instances[dotted(node.target)] = {"type": name, "evidence": "annotation", "line": node.lineno, "expression": self.expression(node.annotation)}
        self.visit(node.target)

    def visit_With(self, node):
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars:
                self.bind_instance(item.optional_vars, item.context_expr)
                self.visit(item.optional_vars)
        for child in node.body:
            self.visit(child)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr in CANDIDATE_METHODS:
            name = self.resolve(node.func)
            if not name:
                evidence = self.infer(node.func.value)
                self.add(node.func, "instance_candidate", "candidates", node.func.attr,
                         "inferred_receiver_candidate" if evidence else "unresolved_receiver_candidate",
                         {"receiver": self.expression(node.func.value), "receiver_evidence": evidence,
                          "resolved_non_native_name": name})
        self.generic_visit(node)

    def comprehension(self, node):
        previous = self.scope
        # Only target bindings are local here; the first iterable uses outer scope.
        self.visit(node.generators[0].iter)
        scope = Scope(ast.Lambda(args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]), body=ast.Constant(None)), previous)
        scope.symbol = previous.symbol + ".<comprehension>"
        for generator in node.generators:
            scope.locals.update(target_names(generator.target))
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
        # Broad imports like os/typing alone do not make a file concurrent.
        used = {event["category"] for event in self.events if event["kind"] not in {"import", "instance_candidate"}}
        self.events = [event for event in self.events if not (
            event["kind"] == "import" and event["details"].get("selective_module_import") and event["category"] not in used)]
        relevant = any(event["kind"] != "instance_candidate" for event in self.events)
        if not relevant:
            self.events = []
        return self.events


class OwnYieldFinder(ast.NodeVisitor):
    def __init__(self):
        self.found = False

    def visit_Yield(self, node):
        self.found = True

    visit_YieldFrom = visit_Yield

    def visit_FunctionDef(self, node):
        pass

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef


def counts(events):
    kinds = collections.Counter(event["kind"] for event in events)
    return {
        "total_static_occurrences": len(events), "imports": kinds["import"],
        "direct_native_api_occurrences": kinds["api_call"] + kinds["api_reference"],
        "syntax_occurrences": sum(value for key, value in kinds.items() if key not in {"import", "api_call", "api_reference", "instance_candidate"}),
        "instance_candidates": kinds["instance_candidate"],
        "by_kind": {kind: kinds[kind] for kind in KIND_ORDER},
    }


def json_bytes(data):
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def md_cell(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("`", "&#96;").replace("\n", " ⏎ ")


def render_category(category, events, head):
    lines = [f"# {category}", "", CATEGORY_DESCRIPTIONS[category], "",
             f"固定源码版本：`{head}`。本表共 **{len(events)}** 条静态出现记录；不是运行次数。", "",
             "同一个直接 API 表达式只记为 `api_call` 或 `api_reference` 中的一类。实例候选不计入直接原生 API 总数。", "",
             "[总览](../README.md) · [完整文件索引](../FILES.md) · [JSON](../inventory.json) · [TSV](../inventory.tsv)", "",
             "| ID | 位置 / 快照 | 所属符号 | 种类 | API / 语法 | 来源判定 | 源码行 |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for event in events:
        source = f"[{event['file']}:{event['line']}]({event['source_url']}) · [快照](../{event['snapshot']})"
        evidence = event["details"].get("receiver_evidence")
        provenance = event["provenance"] + ("; " + evidence["type"] + " @ L" + str(evidence["line"]) if evidence else "")
        lines.append("| " + " | ".join([
            event["id"], source, md_cell(event["symbol"]), event["kind"], md_cell(event["name"]),
            md_cell(provenance), md_cell(event["source_line"]),
        ]) + " |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_statistics(summary, events):
    lines = ["# 静态出现次数统计", "", f"源码版本：`{summary['source_head']}`。", "",
             f"扫描全部 **{summary['tracked_python_files']}** 个 Git 跟踪 Python 文件，**{summary['relevant_python_files']}** 个文件含目标记录；解析错误 **{summary['parse_error_count']}** 个。", "",
             "计数单位是源码中的静态出现位置，不是执行次数。导入、直接调用、非调用引用、语法、实例候选五组分别计数。调用的函数表达式不再重复记为非调用引用。", "",
             "[总览](README.md) · [全部文件](FILES.md) · [机器可读统计](summary.json)", "",
             "## 按记录种类", "", "| 种类 | 次数 |", "| --- | ---: |"]
    for kind, amount in summary["by_kind"].items():
        lines.append(f"| {kind} | {amount} |")
    lines.extend([f"| **全部记录** | **{summary['total_static_occurrences']}** |", "",
                  f"`async def` 总数为 **{summary['async_definitions_total']}** = 普通协程函数 **{summary['by_kind']['async_def']}** + 异步生成器函数 **{summary['by_kind']['async_generator_def']}**。`async_yield` 另记生成器内部的 yield 位置。", "",
                  f"直接目标标准库 API 合计 **{summary['direct_native_api_occurrences']}** = 调用 **{summary['by_kind']['api_call']}** + 非调用引用 **{summary['by_kind']['api_reference']}**，包含下表明确标出的邻接机制。**{summary['instance_candidates']}** 条实例候选不并入此数。", "",
                  "## 按类别", "", "| 类别（完整位置表） | 导入 | 调用 | 非调用引用 | 语法 | 候选 | 全部记录 |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for category, group in summary["by_category"].items():
        kind = group["by_kind"]
        lines.append(f"| [{category}](usage-categories/{category}.md) | {group['imports']} | {kind['api_call']} | {kind['api_reference']} | {group['syntax_occurrences']} | {group['instance_candidates']} | {group['total_static_occurrences']} |")
    lines.extend(["", "## 按直接 API", "", "只包含 `api_call` 与 `api_reference`；导入和实例候选不在此表。", "",
                  "| API | 类别 | 调用 | 非调用引用 | 合计 |", "| --- | --- | ---: | ---: | ---: |"])
    for name, group in summary["by_api"].items():
        category = category_for(name)
        kind = group["by_kind"]
        lines.append(f"| {md_cell(name)} | [{category}](usage-categories/{category}.md) | {kind['api_call']} | {kind['api_reference']} | {group['direct_native_api_occurrences']} |")
    candidates = [event for event in events if event["kind"] == "instance_candidate"]
    inferred = collections.Counter(event["details"]["receiver_evidence"]["type"] for event in candidates if event["details"]["receiver_evidence"])
    lines.extend(["", "## 实例候选：证据分组", "", "以下仅是简单构造、已知工厂或注解给出的接收者线索，不等于运行时类型证明。未获得线索的方法也完整保留在候选表。", "",
                  "| 接收者线索 | 候选数 |", "| --- | ---: |"])
    for name, amount in sorted(inferred.items()):
        lines.append(f"| {name} | {amount} |")
    lines.append(f"| 未获得接收者线索 | {len(candidates) - sum(inferred.values())} |")
    lines.append(f"| **候选合计** | **{len(candidates)}** |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def build(root):
    root = root.resolve()
    top = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    if root != top:
        raise ValueError("SOURCE_ROOT must be the Git repository root")
    head = git(root, "rev-parse", "HEAD")
    paths = sorted(p for p in git(root, "ls-files", "-z").split("\0") if p.endswith(".py"))
    events, files, errors, snapshots = [], [], [], {}
    for filename in paths:
        raw = (root / filename).read_bytes()
        metadata = {"file": filename, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        try:
            encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
            source = raw.decode(encoding)
            tree = ast.parse(source, filename=filename, type_comments=True)
            visitor = InventoryVisitor(filename, source, head)
            visitor.visit(tree)
            found = visitor.finish()
            events.extend(found)
            metadata.update(counts(found))
            metadata["parse_status"] = "ok"
            if found:
                snapshots["source_snapshot/" + filename + ".txt"] = raw
        except (SyntaxError, UnicodeError) as error:
            errors.append({"file": filename, "error": str(error)})
            metadata.update(counts([]))
            metadata["parse_status"] = "error"
        files.append(metadata)
    events.sort(key=lambda event: (event["file"], event["line"], event["col"], KIND_ORDER[event["kind"]], event["name"]))
    for index, event in enumerate(events, 1):
        event["id"] = f"occ-{index:06d}"
    by_category = {category: counts([event for event in events if event["category"] == category]) for category in CATEGORY_DESCRIPTIONS}
    api_groups = collections.defaultdict(list)
    for event in events:
        if event["kind"] in {"api_call", "api_reference"}:
            api_groups[event["name"]].append(event)
    summary = {
        "schema_version": SCHEMA_VERSION, "source_head": head,
        "tracked_python_files": len(paths), "relevant_python_files": len(snapshots),
        "parse_error_count": len(errors), **counts(events),
        "async_definitions_total": sum(event["kind"] in {"async_def", "async_generator_def"} for event in events),
        "by_category": by_category,
        "by_file": {item["file"]: {key: value for key, value in item.items() if key not in {"file", "sha256", "bytes", "parse_status"}} for item in files},
        "by_api": {name: counts(group) for name, group in sorted(api_groups.items())},
    }
    source_info = {
        "repository": UPSTREAM, "head": head, "scope": "git ls-files: every tracked path ending in .py",
        "working_tree_policy": "Read current tracked file bytes; record every SHA-256; ignore untracked files.",
        "tracked_python_changes_from_head": git(root, "diff", "HEAD", "--name-only", "--", "*.py").splitlines(),
        "tracked_python_file_count": len(paths), "parse_errors": errors, "files": files,
    }
    inventory = {
        "schema_version": SCHEMA_VERSION, "source": source_info,
        "counting_policy": {
            "unit": "static source occurrence, never runtime executions",
            "direct_api": "One maximal resolved symbol expression: api_call for a Call.func, otherwise api_reference (including attribute loads, stores and deletes); mutually exclusive.",
            "imports": "One imported alias; broad selective-module imports retained only when targeted APIs occur in the same file.",
            "syntax": "Each AST node; async_def excludes async_generator_def. async_yield separately records yield nodes inside async generators.",
            "candidates": "Call method names in relevant files; excluded from direct native API totals, including inferred receivers.",
            "columns": "Zero-based UTF-8 byte offsets from Python AST; lines are one-based.",
        },
        "limitations": [
            "Static lexical import resolution, not execution, type checking, or full data-flow analysis.",
            "Function parameters/local assignments shadow imported bindings; conflicting reassigned import names are conservatively unresolved.",
            "Imports in conditional branches are not proven reachable; cross-module re-exports, star imports, dynamic imports and getattr are not resolved.",
            "Assignments and known factories provide candidate evidence only; branches, mutations, containers, parameter flow and runtime monkey-patching are not proven.",
            "Candidate names may belong to third-party/custom objects; their presence never establishes native ownership. Already resolved non-target imported APIs are excluded from candidates.",
            "Only tracked .py files are parsed; Markdown/shell/notebook examples, untracked files, string-contained code and installed dependencies are outside this inventory.",
            "A pinned GitHub URL describes HEAD; if tracked_python_changes_from_head is nonempty, local snapshots and hashes describe the scanned working tree instead.",
        ],
        "summary": summary, "occurrences": events,
    }
    output = {"inventory.json": json_bytes(inventory), "summary.json": json_bytes(summary), **snapshots}
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=TSV_FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for event in events:
        writer.writerow({**event, "details": json.dumps(event["details"], ensure_ascii=False, sort_keys=True)})
    output["inventory.tsv"] = stream.getvalue().encode("utf-8")
    for category in CATEGORY_DESCRIPTIONS:
        output["usage-categories/" + category + ".md"] = render_category(category, [event for event in events if event["category"] == category], head)
    output["STATISTICS.md"] = render_statistics(summary, events)
    lines = ["# 全部受检 Python 文件", "", f"版本 `{head}`；全部 **{len(files)}** 个 Git 跟踪 `.py` 文件，相关文件 **{len(snapshots)}** 个。", "",
             "零记录也列出，以便核对扫描范围。只有有记录的文件保存逐字节快照。", "",
             "[总览](README.md) · [完整 JSON](inventory.json) · [统计 JSON](summary.json)", "",
             "| 文件 | 总记录 | 导入 | 直接 API | 语法 | 候选 | SHA-256 |", "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for item in files:
        filename = item["file"]
        link = f"[{filename}](source_snapshot/{filename}.txt)" if item["total_static_occurrences"] else f"[{filename}]({UPSTREAM}/blob/{head}/{filename})"
        lines.append(f"| {link} | {item['total_static_occurrences']} | {item['imports']} | {item['direct_native_api_occurrences']} | {item['syntax_occurrences']} | {item['instance_candidates']} | {item['sha256']} |")
    output["FILES.md"] = ("\n".join(lines) + "\n").encode("utf-8")
    return output, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--check", action="store_true", help="Compare every generated byte and snapshot hash without writing.")
    args = parser.parse_args()
    try:
        output, summary = build(args.source_root)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    managed = {"inventory.json", "inventory.tsv", "summary.json", "FILES.md", "STATISTICS.md"}
    for directory in ("source_snapshot", "usage-categories"):
        managed.update(str(path.relative_to(OUTPUT_ROOT)) for path in (OUTPUT_ROOT / directory).rglob("*") if path.is_file())
    stale = sorted(managed - output.keys())
    differences = [name for name, raw in output.items() if not (OUTPUT_ROOT / name).is_file() or (OUTPUT_ROOT / name).read_bytes() != raw]
    if args.check:
        for name in differences:
            print("DIFF " + name)
        for name in stale:
            print("STALE " + name)
        if differences or stale:
            return 1
        print(f"OK: {summary['tracked_python_files']} tracked Python files; {summary['relevant_python_files']} exact snapshots; {summary['total_static_occurrences']} static occurrences; no generated drift.")
    else:
        for name, raw in output.items():
            target = OUTPUT_ROOT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        for name in stale:
            (OUTPUT_ROOT / name).unlink()
        print(json.dumps({key: summary[key] for key in ("source_head", "tracked_python_files", "relevant_python_files", "parse_error_count", "total_static_occurrences", "imports", "direct_native_api_occurrences", "syntax_occurrences", "instance_candidates", "by_kind")}, ensure_ascii=False, indent=2))
    return 1 if summary["parse_error_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
