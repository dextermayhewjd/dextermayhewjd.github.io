"""Offline checks for the Python documentation snapshot collector."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from urllib.request import Request


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "collect_docs.py"
if SCRIPT.exists():
    SPEC = importlib.util.spec_from_file_location("collect_docs", SCRIPT)
    collector = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(collector)
else:
    collector = None


FIXTURE = """<!doctype html><html><head>
<title>Tasks &amp; coroutines — Python 3.16.0a1 documentation</title>
<script>unwanted script text</script></head><body>
<div class="related">unwanted navigation</div>
<div class="body" role="main"><section id="coroutines-and-tasks">
<h1>Tasks &amp; coroutines<a class="headerlink" href="#coroutines-and-tasks">¶</a></h1>
<p>Run concurrent work with <code>await</code>.</p>
<dl class="py function"><dt class="sig sig-object py" id="asyncio.create_task">
<span class="sig-prename descclassname">asyncio.</span><span class="sig-name descname">create_task</span><span class="sig-paren">(</span><em>coro</em>, *, name=None<span class="sig-paren">)</span>
<a class="headerlink" href="#asyncio.create_task">¶</a></dt>
<dd><p>Schedule a coroutine.</p>
<dl class="py method"><dt class="sig sig-object py" id="loop.create_task">loop.create_task(coro)<a class="headerlink">¶</a></dt><dd>Nested method.</dd></dl>
</dd></dl>
<dl class="py class"><dt class="sig sig-object py" id="asyncio.Task">class asyncio.Task(coro)</dt><dd>Task.</dd></dl>
<dl class="py attribute"><dt class="sig sig-object py" id="asyncio.Task.name">asyncio.Task.name</dt><dd>Name.</dd></dl>
<dl class="py data"><dt class="sig sig-object py" id="asyncio.ALL_COMPLETED">asyncio.ALL_COMPLETED</dt><dd>Constant.</dd></dl>
<dl><dt id="not-an-api">Ordinary definition</dt><dd>Text.</dd></dl>
<section id="awaitables"><h2>Awaitables<a class="headerlink">¶</a></h2><p>Await futures.</p></section>
<a href="asyncio-eventloop.html#loop.create_task">Loop</a>
<a href="../reference/expressions.html#await">Await</a>
<a href="https://docs.python.org/3/library/asyncio-task.html">Stable docs</a>
<a href="https://docs.python.org.evil.example/3.16/library/asyncio-task.html">Offsite</a>
</section></div><footer>unwanted footer</footer></body></html>"""


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(collector, "The documentation collector must exist")

    def test_extracts_official_ids_kinds_signatures_and_body(self):
        result = collector.parse_document(
            FIXTURE, "https://docs.python.org/3.16/library/asyncio-task.html"
        )
        self.assertEqual(result["title"], "Tasks & coroutines — Python 3.16.0a1 documentation")
        symbols = {symbol["name"]: symbol for symbol in result["symbols"]}
        self.assertEqual(set(symbols), {
            "asyncio.create_task", "loop.create_task", "asyncio.Task",
            "asyncio.Task.name", "asyncio.ALL_COMPLETED",
        })
        self.assertEqual(symbols["asyncio.create_task"], {
            "name": "asyncio.create_task", "kind": "function",
            "url": "https://docs.python.org/3.16/library/asyncio-task.html#asyncio.create_task",
            "signature": "asyncio.create_task(coro, *, name=None)",
        })
        self.assertEqual(symbols["loop.create_task"]["kind"], "method")
        self.assertEqual(symbols["asyncio.Task"]["kind"], "class")
        self.assertEqual(symbols["asyncio.Task.name"]["kind"], "attribute")
        self.assertEqual(symbols["asyncio.ALL_COMPLETED"]["kind"], "data")
        self.assertIn("Run concurrent work with await.", result["text"])
        self.assertNotIn("unwanted", result["text"])
        self.assertNotIn("¶", result["text"])
        self.assertIn({"id": "awaitables", "title": "Awaitables"}, result["sections"])

    def test_links_and_discovery_cannot_escape_version_or_asyncio_scope(self):
        base = "https://docs.python.org/3.16/library/asyncio.html"
        parsed = collector.parse_document(FIXTURE, base)
        self.assertEqual(parsed["links"], [
            base + "#coroutines-and-tasks",
            base + "#asyncio.create_task",
            "https://docs.python.org/3.16/library/asyncio-eventloop.html#loop.create_task",
            "https://docs.python.org/3.16/reference/expressions.html#await",
        ])
        discovered = collector.discover_asyncio_urls([parsed])
        self.assertEqual(set(discovered), {
            base,
            "https://docs.python.org/3.16/library/asyncio-eventloop.html",
        })
        for invalid in (
            "https://docs.python.org/3/library/asyncio.html",
            "https://docs.python.org/3.160/library/asyncio.html",
            "https://docs.python.org.evil.example/3.16/library/asyncio.html",
            "http://docs.python.org/3.16/library/asyncio.html",
            "https://docs.python.org/3.16/_static/theme.css",
        ):
            with self.subTest(invalid=invalid):
                self.assertIsNone(collector.official_url(invalid, base))

    def test_snapshots_preserve_bytes_and_check_detects_tampering_and_missing_seed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            documents = []
            for url in collector.REQUESTED_URLS:
                document = collector.save_document(
                    root, url, FIXTURE.encode(), "asyncio", "User requested page.",
                    coverage="full_page",
                )
                documents.append(document)
            catalog = {
                "schema_version": 1,
                "requested_urls": collector.REQUESTED_URLS,
                "documents": documents,
            }
            manifest = root / "official/catalog.json"
            manifest.write_text(json.dumps(catalog), encoding="utf-8")
            self.assertEqual(collector.check_catalog(root), [])
            document = documents[0]
            self.assertEqual(document["sha256"], hashlib.sha256(FIXTURE.encode()).hexdigest())
            self.assertEqual((root / document["html_path"]).read_bytes(), FIXTURE.encode())
            self.assertEqual(document["id"], "asyncio-runner")
            (root / document["text_path"]).write_text("damaged", encoding="utf-8")
            self.assertTrue(any("text sha256 mismatch" in error for error in collector.check_catalog(root)))
            catalog["documents"] = documents[1:]
            manifest.write_text(json.dumps(catalog), encoding="utf-8")
            self.assertTrue(any("requested page missing" in error for error in collector.check_catalog(root)))

    def test_failed_fetch_is_recorded_and_offline_check_reports_failure(self):
        def unavailable(url):
            raise OSError("fixture unavailable")

        with tempfile.TemporaryDirectory() as directory:
            documents = collector.collect_documents(
                Path(directory), [{
                    "url": "https://docs.python.org/3.16/library/asyncio-task.html",
                    "category": "asyncio", "reason": "User requested page.",
                    "coverage": "full_page",
                }], fetcher=unavailable, workers=1,
            )
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["status"], "error")
        self.assertEqual(documents[0]["error"], "OSError: fixture unavailable")
        self.assertIsNone(documents[0]["html_path"])
        self.assertEqual(documents[0]["symbols"], [])

    def test_official_html_redirect_preserves_actual_page_and_requested_alias(self):
        old_url = "https://docs.python.org/3.16/library/functions.html"
        new_url = "https://docs.python.org/3.16/builtins/functions.html"
        pages = {
            old_url: b'<html><head><noscript><meta http-equiv="refresh" content="0; url=../builtins/functions.html"/></noscript></head></html>',
            new_url: b'<html><title>Built-in Functions</title><div class="body"><dl class="py function"><dt class="sig py" id="aiter">aiter(async_iterable)</dt></dl></div></html>',
        }
        with tempfile.TemporaryDirectory() as directory:
            document, = collector.collect_documents(Path(directory), [{
                "url": old_url, "category": "standard-library",
                "reason": "Asynchronous iteration built-ins.",
                "coverage": "matched_sections",
            }], fetcher=pages.__getitem__, workers=1)
            self.assertEqual(document["status"], "ok")
            self.assertEqual(document["id"], "builtins-functions")
            self.assertEqual(document["url"], new_url)
            self.assertEqual(document["requested_url"], old_url)
            self.assertEqual(document["redirect_chain"], [old_url, new_url])
            self.assertEqual(document["symbols"][0]["url"], new_url + "#aiter")

    def test_html_redirect_cannot_fetch_another_version(self):
        old_url = "https://docs.python.org/3.16/library/functions.html"

        def wrong_version(url):
            self.assertEqual(url, old_url)
            return b'<meta http-equiv="refresh" content="0; url=https://docs.python.org/3/library/functions.html">'

        with tempfile.TemporaryDirectory() as directory:
            document, = collector.collect_documents(Path(directory), [{
                "url": old_url, "category": "standard-library",
                "reason": "Asynchronous iteration built-ins.",
            }], fetcher=wrong_version, workers=1)
        self.assertEqual(document["status"], "error")
        self.assertIn("redirect outside Python 3.16", document["error"])

    def test_http_redirect_is_checked_before_following_it(self):
        handler = collector.OfficialRedirectHandler()
        request = Request("https://docs.python.org/3.16/library/functions.html")
        for target in (
            "https://docs.python.org/3/library/functions.html",
            "https://example.org/3.16/library/functions.html",
        ):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, "redirect outside Python 3.16"):
                    handler.redirect_request(request, None, 302, "Moved", {}, target)
        allowed = handler.redirect_request(
            request, None, 302, "Moved", {},
            "https://docs.python.org/3.16/builtins/functions.html",
        )
        self.assertEqual(allowed.full_url, "https://docs.python.org/3.16/builtins/functions.html")

    def test_optional_missing_history_warns_without_masking_required_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            documents = [collector.save_document(
                root, url, FIXTURE.encode(), "asyncio", "Requested page.",
            ) for url in collector.REQUESTED_URLS]
            documents.append({
                "id": "asyncio-policy", "url": "https://docs.python.org/3.16/library/asyncio-policy.html",
                "title": "", "category": "asyncio-historical-probe", "status": "error",
                "html_path": None, "text_path": None, "sha256": None,
                "fetched_at": "2026-10-13T00:00:00+00:00", "symbols": [], "links": [],
                "reason": "Optional historical-page probe.", "required": False,
                "error": "HTTPError: HTTP Error 404: Not Found",
            })
            manifest = root / "official/catalog.json"
            catalog = {"schema_version": 1, "requested_urls": collector.REQUESTED_URLS, "documents": documents}
            manifest.write_text(json.dumps(catalog), encoding="utf-8")
            warnings = []
            self.assertEqual(collector.check_catalog(root, warnings=warnings), [])
            self.assertEqual(len(warnings), 1)
            self.assertIn("asyncio-policy", warnings[0])
            documents[0].update(status="error", required=False, error="Required page unavailable")
            manifest.write_text(json.dumps(catalog), encoding="utf-8")
            self.assertTrue(any("Required page unavailable" in error for error in collector.check_catalog(root)))

    def test_selected_pages_exclude_general_apis_from_the_symbol_catalog(self):
        for identifier, included, excluded in (
            ("builtins-functions", "anext", "print"),
            ("inspect", "inspect.isawaitable", "inspect.signature"),
            ("contextlib", "contextlib.AsyncExitStack.aclose", "contextlib.closing"),
            ("unittest.mock", "unittest.mock.AsyncMock", "unittest.mock.Mock"),
            ("reference-datamodel", "object.__await__", "object.__repr__"),
            ("os", "os.waitpid", "os.listdir"),
            ("fcntl", "fcntl.flock", "fcntl.ioctl"),
            ("time", "time.monotonic", "time.strftime"),
        ):
            with self.subTest(identifier=identifier):
                symbols = [{"name": included}, {"name": excluded}]
                self.assertEqual(collector.select_symbols(identifier, symbols), [{"name": included}])
        ordinary = [{"name": "threading.Thread"}, {"name": "threading.Lock"}]
        self.assertEqual(collector.select_symbols("threading", ordinary), ordinary)


if __name__ == "__main__":
    unittest.main()
