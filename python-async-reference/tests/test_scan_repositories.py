"""Regression checks for conservative, reproducible repository inventories."""

import hashlib
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


SCANNER_PATH = Path(__file__).resolve().parents[1] / "tools" / "scan_repositories.py"
if SCANNER_PATH.exists():
    SPEC = importlib.util.spec_from_file_location("reference_scanner", SCANNER_PATH)
    SCANNER = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(SCANNER)
else:
    SCANNER = None


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(SCANNER, "The repository scanner is not implemented")

    def scan(self, source):
        return SCANNER.scan_source(textwrap.dedent(source), "slime/example.py")

    def calls(self, source):
        return [item for item in self.scan(source)
                if item["kind"] in {"api_call", "inferred_method", "instance_candidate"}]

    def test_aliases_are_resolved_but_shadowed_parameters_are_not_native(self):
        calls = self.calls("""
            import asyncio as aio
            from asyncio import gather as collect
            collect(aio.sleep(0))
            def f(aio):
                aio.create_task(job())
            def g():
                collect = custom
                collect()
        """)
        self.assertEqual([row["canonical_name"] for row in calls],
                         ["asyncio.gather", "asyncio.sleep", None])
        self.assertEqual(calls[-1]["resolution"], "unresolved")

    def test_reassigned_global_and_nonlocal_imports_are_not_native(self):
        rows = self.calls("""
            import asyncio
            def f():
                global asyncio
                asyncio = custom
                asyncio.gather()
            def outer():
                import asyncio as aio
                def inner():
                    nonlocal aio
                    aio = custom
                    aio.gather()
        """)
        self.assertEqual(rows, [])

    def test_taskgroup_context_and_task_factory_keep_inference_separate(self):
        calls = self.calls("""
            import asyncio
            async def main():
                async with asyncio.TaskGroup() as tg:
                    task = tg.create_task(work())
                    task.cancel()
        """)
        self.assertEqual([(row["canonical_name"], row["kind"], row["resolution"])
                          for row in calls], [
            ("asyncio.TaskGroup", "api_call", "direct"),
            ("asyncio.TaskGroup.create_task", "inferred_method", "inferred"),
            ("asyncio.Task.cancel", "inferred_method", "inferred"),
        ])
        self.assertEqual(calls[1]["details"]["receiver_evidence"]["type"], "asyncio.TaskGroup")

    def test_annotations_and_awaited_factories_provide_method_evidence(self):
        calls = self.calls("""
            import asyncio
            async def read(reader: asyncio.StreamReader, task: 'asyncio.Task[int]'):
                await reader.readexactly(2)
                task.result()
                proc = await asyncio.create_subprocess_exec('true')
                await proc.wait()
                loop = asyncio.get_running_loop()
                loop.call_soon(print)
                coroutine = asyncio.create_subprocess_exec('true')
                coroutine.wait()
        """)
        inferred = [row["canonical_name"] for row in calls if row["kind"] == "inferred_method"]
        self.assertEqual(inferred, ["asyncio.StreamReader.readexactly", "asyncio.Task.result",
                                   "asyncio.subprocess.Process.wait", "asyncio.AbstractEventLoop.call_soon"])
        self.assertEqual(calls[-1]["canonical_name"], None)

    def test_third_party_methods_remain_unresolved(self):
        rows = self.calls("""
            import ray
            import aiohttp
            import anyio
            ray.get(ref)
            session = aiohttp.ClientSession()
            session.get(url)
            anyio.create_task_group().create_task(work())
        """)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["kind"] == "instance_candidate" for row in rows))
        self.assertTrue(all(row["canonical_name"] is None for row in rows))
        self.assertEqual(rows[0]["details"]["resolved_non_native_name"], "ray.get")

    def test_reassignment_and_local_shadowing_invalidate_old_type_evidence(self):
        rows = self.calls("""
            import asyncio
            queue = asyncio.Queue()
            def shadow(queue):
                queue.get()
            async def main():
                task = asyncio.create_task(work())
                task = third_party
                task.cancel()
                local: asyncio.Queue
                local = custom
                local.get()
        """)
        candidates = [row for row in rows if row["kind"] == "instance_candidate"]
        self.assertEqual([row["expression"] for row in candidates],
                         ["queue.get", "task.cancel", "local.get"])
        self.assertTrue(all(row["canonical_name"] is None for row in candidates))

    def test_self_attributes_do_not_leak_between_classes_or_methods(self):
        rows = self.calls("""
            import asyncio
            class A:
                def __init__(self):
                    self.queue = asyncio.Queue()
                    self.queue.put_nowait(1)
                def later(self):
                    self.queue.get()
            class B:
                def get(self):
                    self.queue.get()
        """)
        self.assertEqual([row["canonical_name"] for row in rows],
                         ["asyncio.Queue", "asyncio.Queue.put_nowait", None, None])

    def test_branch_and_loop_assignments_do_not_claim_definite_types(self):
        rows = self.calls("""
            import asyncio
            def f(condition):
                if condition:
                    obj = asyncio.Queue()
                obj.get()
                task = asyncio.create_task(work())
                for task in other_tasks:
                    task.cancel()
                task.cancel()
        """)
        candidates = [row for row in rows if row["kind"] == "instance_candidate"]
        self.assertEqual([row["expression"] for row in candidates],
                         ["obj.get", "task.cancel", "task.cancel"])

    def test_exception_and_pattern_bindings_shadow_existing_objects(self):
        rows = self.calls("""
            import asyncio
            def f(value):
                obj = asyncio.Queue()
                try:
                    risky()
                except Exception as obj:
                    obj.get()
                match value:
                    case {'data': obj}:
                        obj.get()
                obj.get()
        """)
        self.assertEqual([row["canonical_name"] for row in rows],
                         ["asyncio.Queue", None, None, None])

    def test_methods_must_belong_to_inferred_type_and_tuple_results_are_unpacked(self):
        rows = self.calls("""
            import asyncio
            async def f():
                lock = asyncio.Lock()
                lock.join()
                reader, writer = await asyncio.open_connection('localhost', 80)
                await reader.readexactly(4)
                await writer.drain()
        """)
        self.assertEqual([row["canonical_name"] for row in rows],
                         ["asyncio.Lock", None, "asyncio.open_connection",
                          "asyncio.StreamReader.readexactly", "asyncio.StreamWriter.drain"])

    def test_context_manager_result_must_not_be_assumed_to_be_its_lock(self):
        rows = self.calls("""
            import asyncio
            async def f():
                async with asyncio.Lock() as acquired:
                    acquired.release()
        """)
        self.assertEqual([row["canonical_name"] for row in rows], ["asyncio.Lock", None])

    def test_match_capture_shadows_imported_module(self):
        rows = self.calls("""
            import asyncio
            def f(value):
                match value:
                    case {'module': asyncio}:
                        asyncio.sleep(0)
        """)
        self.assertEqual([row["canonical_name"] for row in rows], [])

    def test_rebinding_receiver_or_defining_name_discards_previous_evidence(self):
        rows = self.calls("""
            import asyncio
            def f(holder):
                holder.queue = asyncio.Queue()
                holder = external
                holder.queue.get()
                queue = asyncio.Queue()
                def queue():
                    pass
                queue.get()
        """)
        self.assertEqual([row["canonical_name"] for row in rows],
                         ["asyncio.Queue", None, "asyncio.Queue", None])

    def test_try_handlers_and_loop_bodies_do_not_reuse_overwritten_values(self):
        rows = self.calls("""
            import asyncio
            def f():
                task = asyncio.create_task(work())
                try:
                    task = external
                    risky()
                except Exception:
                    task.cancel()
                queue = asyncio.Queue()
                while condition:
                    queue.get()
                    queue = external
        """)
        self.assertEqual([row["canonical_name"] for row in rows],
                         ["asyncio.create_task", None, "asyncio.Queue", None])

    def test_every_syntax_kind_is_counted_without_double_counting_calls(self):
        rows = self.scan("""
            import asyncio
            async def gen(items, cm):
                async with cm:
                    async for item in items:
                        yield await asyncio.sleep(0)
                values = [x async for x in items]
            async def coro():
                return 1
        """)
        summary = SCANNER.summarize(rows)
        self.assertEqual(summary["syntax_occurrences"], 7)
        self.assertEqual(summary["by_kind"]["async_generator_def"], 1)
        self.assertEqual(summary["by_kind"]["async_def"], 1)
        self.assertEqual(summary["direct_calls"], 1)
        self.assertEqual(summary["references"], 0)

    def test_new_asyncio_submodules_are_recognized_without_symbol_whitelist(self):
        rows = self.calls("""
            import asyncio.graph as graph
            from asyncio.tools import future_helper
            graph.capture_call_graph()
            future_helper()
        """)
        self.assertEqual([row["canonical_name"] for row in rows],
                         ["asyncio.graph.capture_call_graph", "asyncio.tools.future_helper"])

    def test_concurrency_io_clocks_testing_and_builtin_errors_are_not_missed(self):
        rows = self.scan("""
            import selectors
            import time
            import inspect
            from unittest.mock import AsyncMock
            selectors.DefaultSelector()
            time.monotonic()
            time.perf_counter()
            inspect.markcoroutinefunction(work)
            mock = AsyncMock()
            try:
                raise ExceptionGroup('failed', [])
            except TimeoutError:
                pass
        """)
        observed = {row["canonical_name"] for row in rows if row["kind"] in {"api_call", "api_reference"}}
        self.assertEqual(observed, {"selectors.DefaultSelector", "time.monotonic",
                                    "time.perf_counter", "inspect.markcoroutinefunction",
                                    "unittest.mock.AsyncMock", "builtins.ExceptionGroup", "builtins.TimeoutError"})

    def test_builtin_errors_respect_aliasing_and_parameter_shadowing(self):
        rows = self.scan("""
            import builtins as b
            def f(TimeoutError):
                raise TimeoutError()
            def g():
                raise b.ExceptionGroup('failed', [])
        """)
        self.assertEqual([row["canonical_name"] for row in rows if row["kind"] == "api_call"],
                         ["builtins.ExceptionGroup"])

    def test_selector_and_asyncmock_methods_keep_receiver_evidence(self):
        rows = self.calls("""
            import selectors
            from unittest.mock import AsyncMock
            selector = selectors.DefaultSelector()
            selector.register(sock, selectors.EVENT_READ)
            mock = AsyncMock()
            mock.assert_awaited_once()
        """)
        inferred = [row["canonical_name"] for row in rows if row["kind"] == "inferred_method"]
        self.assertEqual(inferred, ["selectors.BaseSelector.register",
                                   "unittest.mock.AsyncMock.assert_awaited_once"])

    def test_generic_network_reflection_errors_and_clocks_are_out_of_scope(self):
        rows = self.scan("""
            import socket
            import time
            import inspect
            from unittest.mock import Mock
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            time.time()
            time.process_time()
            inspect.getmembers(object)
            Mock()
            Exception()
            ValueError()
        """)
        self.assertEqual([row for row in rows if row["kind"] in {"api_call", "api_reference"}], [])


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(SCANNER, "The repository scanner is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.git("init", "-q")
        self.raw = b"# coding: latin-1\r\n# caf\xe9\r\nimport asyncio\r\nasyncio.run(main())\r\n"
        self.write("slime/native.py", self.raw)
        self.write("slime/quiet.py", b"value = 1\n")
        self.write("tests/test_native.py", b"import asyncio\nasyncio.sleep(0)\n")
        self.write("examples/demo.py", b"await\n")
        self.write("tools/script.py", b"pass\n")
        self.git("add", ".")
        self.git("-c", "user.name=Scanner Test", "-c", "user.email=scanner@example.invalid",
                 "commit", "-qm", "fixture")
        self.write("untracked.py", b"import asyncio\nasyncio.run(main())\n")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args]).decode().strip()

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def test_complete_manifest_scopes_hashes_parse_errors_and_exact_snapshots(self):
        artifacts, inventory = SCANNER.build_repository("slime", self.root)
        source = inventory["source"]
        self.assertEqual(source["head"], self.git("rev-parse", "HEAD"))
        self.assertEqual(source["tracked_python_changes_from_head"], [])
        self.assertEqual(source["tracked_python_file_count"], 5)
        self.assertEqual(source["repository"], "https://github.com/THUDM/slime")
        files = {row["file"]: row for row in source["files"]}
        self.assertEqual(files["slime/native.py"]["scope"], "core")
        self.assertEqual(files["tests/test_native.py"]["scope"], "tests")
        self.assertEqual(files["examples/demo.py"]["scope"], "examples")
        self.assertEqual(files["tools/script.py"]["scope"], "other")
        self.assertEqual(files["slime/native.py"]["sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(files["examples/demo.py"]["parse_status"], "error")
        self.assertEqual(files["slime/quiet.py"]["total_static_occurrences"], 0)
        self.assertEqual(artifacts["source_snapshot/slime/native.py.txt"], self.raw)
        self.assertNotIn("untracked.py", files)
        self.assertEqual(json.loads(artifacts["inventory.json"]), inventory)
        for row in inventory["occurrences"]:
            self.assertIn(row["snapshot"], artifacts)
            self.assertIn(source["head"], row["source_url"])

    def test_check_compares_bytes_without_changing_output_or_source(self):
        # Keep this CLI fixture valid so a parse-error exit does not mask drift.
        self.write("examples/demo.py", b"pass\n")
        output = Path(self.temp.name) / "output"
        arguments = ["--repo", f"slime={self.root}", "--output", str(output)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(SCANNER.main(arguments), 0)
            self.assertEqual(SCANNER.main(arguments + ["--check"]), 0)
        target = output / "slime" / "source_snapshot" / "slime" / "native.py.txt"
        target.write_bytes(b"tampered\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(SCANNER.main(arguments + ["--check"]), 1)
        self.assertEqual(target.read_bytes(), b"tampered\n")
        self.assertEqual((self.root / "slime/native.py").read_bytes(), self.raw)
        self.assertEqual(self.git("status", "--porcelain"),
                         "M examples/demo.py\n?? untracked.py")

    def test_output_inside_source_repository_is_rejected_without_writes(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            SCANNER.main(["--repo", f"slime={self.root}", "--output", str(self.root / "reports")])
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse((self.root / "reports").exists())


if __name__ == "__main__":
    unittest.main()
