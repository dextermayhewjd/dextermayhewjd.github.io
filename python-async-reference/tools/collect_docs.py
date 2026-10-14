#!/usr/bin/env python3
"""Snapshot a bounded set of Python 3.16 asynchronous-programming documents.

Only the standard library is required. Run normally to fetch documents, or use
``--check`` to validate the existing catalog and snapshots without networking.
``sha256`` is the digest of the original HTML bytes; ``text_sha256`` covers the
UTF-8 body-text snapshot. Broader reference pages are intentionally saved in full.
"""

import argparse
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


BASE = "https://docs.python.org/3.16/"
REQUESTED_URLS = [BASE + "library/" + name + ".html" for name in (
    "asyncio-runner", "asyncio-task", "asyncio-stream", "asyncio-sync",
    "asyncio-subprocess", "asyncio-queue", "asyncio-exceptions", "asyncio-graph",
    "asyncio-tools", "asyncio-eventloop", "asyncio-future", "asyncio-protocol",
)]
INDEX_URLS = [BASE + "library/" + name + ".html" for name in (
    "asyncio", "asyncio-api-index", "asyncio-llapi-index",
)]

# This explicit boundary prevents following the whole standard-library graph.
# Direct concurrency modules are retained in full; helper pages expose only
# selected async/concurrency APIs in the catalog while preserving source bytes.
SUPPLEMENTAL_PAGES = [
    ("howto/a-conceptual-overview-of-asyncio.html", "howto", "full_page",
     "Official conceptual overview linked from the asyncio landing page."),
    ("reference/compound_stmts.html", "language-reference", "matched_sections",
     "Language definitions of coroutine functions, async for and async with; full page retained."),
    ("reference/expressions.html", "language-reference", "matched_sections",
     "Await expressions, asynchronous comprehensions and asynchronous generator methods; full page retained."),
    ("reference/datamodel.html", "language-reference", "matched_sections",
     "Awaitable, coroutine, asynchronous iterator and asynchronous context-manager protocols; full page retained."),
    ("library/contextlib.html", "standard-library", "matched_sections",
     "asynccontextmanager, aclosing, AsyncExitStack and asynchronous resource cleanup; full module reference retained."),
    ("library/contextvars.html", "standard-library", "full_page",
     "Context-local state has native asyncio support and propagates across asynchronous tasks."),
    ("library/inspect.html", "standard-library", "matched_sections",
     "Coroutine/awaitable/asynchronous-generator detection, state and locals inspection; full module reference retained."),
    ("library/types.html", "standard-library", "matched_sections",
     "CoroutineType, AsyncGeneratorType and types.coroutine connect runtime objects and awaitable protocols; full page retained."),
    ("library/typing.html", "standard-library", "matched_sections",
     "Awaitable, Coroutine, AsyncIterable, AsyncIterator, AsyncGenerator and AsyncContextManager annotations; full page retained."),
    ("library/collections.abc.html", "standard-library", "matched_sections",
     "Awaitable, Coroutine, AsyncIterable, AsyncIterator and AsyncGenerator abstract base classes; full page retained."),
    ("library/functions.html", "standard-library", "matched_sections",
     "aiter and anext built-ins implement asynchronous iteration; full built-in reference retained."),
    ("library/exceptions.html", "standard-library", "matched_sections",
     "StopAsyncIteration, TimeoutError and exception groups appear in async iteration and structured concurrency; full hierarchy retained."),
    ("library/concurrent.futures.html", "standard-library", "full_page",
     "Executor and concurrent Future APIs interoperate with asyncio run_in_executor and wrap_future."),
    ("library/threading.html", "standard-library", "full_page",
     "Threading primitives and thread-local state provide the adjacent concurrency model and cross-thread boundary."),
    ("library/_thread.html", "standard-library", "full_page",
     "Low-level thread identifiers, locks and thread creation are the substrate of adjacent threading mechanisms."),
    ("library/queue.html", "standard-library", "full_page",
     "Thread-safe queues are an adjacent mechanism, distinct from asyncio.Queue."),
    ("library/multiprocessing.html", "standard-library", "full_page",
     "Process, pool and interprocess primitives provide adjacent parallelism and executor background."),
    ("library/multiprocessing.shared_memory.html", "standard-library", "full_page",
     "Shared memory is an adjacent interprocess data-sharing mechanism used alongside worker and executor processes."),
    ("library/os.html", "standard-library", "matched_sections",
     "Only process creation/control/waiting and interprocess-pipe APIs are in scope; general filesystem, path and environment APIs are excluded from catalog symbols."),
    ("library/fcntl.html", "standard-library", "matched_sections",
     "Only file-locking functions/constants are in scope; generic ioctl and unrelated file-descriptor operations are excluded from catalog symbols."),
    ("library/subprocess.html", "standard-library", "full_page",
     "Process and pipe semantics underpin asyncio subprocess facilities; synchronous APIs remain clearly separate."),
    ("library/signal.html", "standard-library", "full_page",
     "Signal handlers and platform/thread restrictions explain event-loop signal integration."),
    ("library/select.html", "standard-library", "full_page",
     "OS readiness polling is a low-level event-loop dependency."),
    ("library/selectors.html", "standard-library", "full_page",
     "High-level I/O readiness multiplexing underlies selector event loops."),
    ("library/time.html", "standard-library", "matched_sections",
     "Only waiting and concurrency timing APIs are in scope; calendar/time-zone/formatting conversion APIs are excluded from catalog symbols."),
    ("library/unittest.html", "standard-library", "matched_sections",
     "IsolatedAsyncioTestCase and asynchronous setup/cleanup support async tests; full framework reference retained."),
    ("library/unittest.mock.html", "standard-library", "matched_sections",
     "AsyncMock and asynchronous context-manager/iterator mocking support async tests; full reference retained."),
]

ASYNCIO_PATH = re.compile(r"^/3\.16/library/asyncio(?:-[a-z0-9-]+)?\.html$")
RELEVANT = re.compile(
    r"async|await|coroutin|context.?var|execution.context|executor|future|"
    r"event.loop|non.block|selector|signal|socket|thread|multiprocess|"
    r"subprocess|parallel|concurren|\baiter\b|\banext\b|aclosing|exception.group",
    re.IGNORECASE,
)
SECTION_RELEVANT = re.compile(RELEVANT.pattern + r"|generator|iterator", re.IGNORECASE)
SYMBOL_SELECTION = {
    "contextlib": r"contextlib\.(?:AbstractAsyncContextManager|asynccontextmanager|aclosing|AsyncContextDecorator|AsyncExitStack|nullcontext)(?:\.|$)",
    "inspect": r"inspect\.(?:iscoroutinefunction|markcoroutinefunction|iscoroutine|isawaitable|isasyncgenfunction|isasyncgen|getcoroutinestate|getasyncgenstate|getcoroutinelocals|getasyncgenlocals|CO_COROUTINE|CO_ITERABLE_COROUTINE|CO_ASYNC_GENERATOR)$",
    "types": r"types\.(?:CoroutineType|AsyncGeneratorType|coroutine)$",
    "typing": r"typing\.(?:Awaitable|Coroutine|AsyncIterable|AsyncIterator|AsyncGenerator|AsyncContextManager)(?:\.|$)",
    "collections.abc": r"collections\.abc\.(?:Awaitable|Coroutine|AsyncIterable|AsyncIterator|AsyncGenerator)(?:\.|$)",
    "builtins-functions": r"(?:aiter|anext)$",
    "builtins-exceptions": r"(?:StopAsyncIteration|StopIteration|GeneratorExit|TimeoutError|BaseExceptionGroup|ExceptionGroup)(?:\.|$)",
    "unittest": r"unittest\.IsolatedAsyncioTestCase(?:\.|$)",
    "unittest.mock": r"unittest\.mock\.AsyncMock(?:\.|$)",
    "reference-datamodel": r"(?:coroutine\.|object\.(?:__await__|__aiter__|__anext__|__aenter__|__aexit__)$)",
    "os": r"os\.(?:fork|forkpty|posix_spawn|posix_spawnp|spawn[lvep]+|exec[lvep]+|wait|waitid|waitpid|wait3|wait4|waitstatus_to_exitcode|pidfd_open|kill|killpg|abort|_exit|getpid|getppid|getpgid|getpgrp|setpgid|setpgrp|setsid|getsid|getpriority|setpriority|nice|sched_[a-z_]+|register_at_fork|pipe|pipe2|system|popen|eventfd(?:_[a-z]+)?|P_ALL|P_PID|P_PGID|P_PIDFD|W[A-Z0-9_]+|CLD_[A-Z_]+|POSIX_SPAWN_[A-Z_]+|SCHED_[A-Z_]+|PRIO_[A-Z_]+)$",
    "fcntl": r"fcntl\.(?:fcntl|flock|lockf|LOCK_[A-Z_]+|F_(?:GETLK|SETLK|SETLKW|OFD_GETLK|OFD_SETLK|OFD_SETLKW|RDLCK|WRLCK|UNLCK))$",
    "time": r"time\.(?:sleep|monotonic|monotonic_ns|perf_counter|perf_counter_ns)$",
}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCK_TAGS = {"p", "div", "section", "h1", "h2", "h3", "h4", "h5", "h6", "li", "dt", "dd", "pre", "tr", "blockquote"}
FetchResult = namedtuple("FetchResult", "url payload")


class Node:
    def __init__(self, tag, attrs=()):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def walk(node, ancestors=()):
    yield node, ancestors
    for child in node.children:
        if isinstance(child, Node):
            yield from walk(child, ancestors + (node,))


def node_text(node, blocks=False):
    classes = set(node.attrs.get("class", "").split())
    if node.tag in {"script", "style", "nav", "footer"} or classes & {"headerlink", "viewcode-link", "copybtn"}:
        return ""
    result = "".join(node_text(child, blocks) if isinstance(child, Node) else child for child in node.children)
    if blocks and node.tag in BLOCK_TAGS:
        return "\n" + result + "\n"
    if node.tag == "br":
        return "\n"
    return result


def clean_text(value):
    return " ".join(value.replace("¶", "").split())


def official_url(href, base=BASE):
    """Resolve an HTML content link, rejecting other hosts and versions."""
    parsed = urlsplit(urljoin(base, href))
    if parsed.scheme != "https" or parsed.netloc != "docs.python.org":
        return None
    if not parsed.path.startswith("/3.16/") or not parsed.path.endswith(".html"):
        return None
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", parsed.fragment))


class OfficialRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if official_url(newurl) != newurl:
            raise ValueError("HTTP redirect outside Python 3.16 documentation")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def parse_document(html, url):
    parser = DocumentParser()
    parser.feed(html)
    nodes = list(walk(parser.root))
    title = next((clean_text(node_text(node)) for node, _ in nodes if node.tag == "title"), "")
    body = next((node for node, _ in nodes if "body" in node.attrs.get("class", "").split()), None)
    if body is None:
        body = next((node for node, _ in nodes if node.attrs.get("role") == "main"), None)
    if body is None:
        raise ValueError("HTML has no Sphinx document body")
    body_nodes = list(walk(body))
    lines = [clean_text(line) for line in node_text(body, blocks=True).splitlines()]
    text = "\n".join(line for line in lines if line) + "\n"
    symbols, links, sections = [], [], []
    seen_symbols, seen_links, seen_sections = set(), set(), set()
    for node, ancestors in body_nodes:
        if node.tag == "a" and node.attrs.get("href"):
            link = official_url(node.attrs["href"], url)
            if link and link not in seen_links:
                seen_links.add(link)
                links.append(link)
        if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            section = next((parent for parent in reversed(ancestors) if parent.tag == "section" or "section" in parent.attrs.get("class", "").split()), None)
            anchor = node.attrs.get("id") or (section.attrs.get("id") if section else None)
            if anchor and anchor not in seen_sections:
                seen_sections.add(anchor)
                sections.append({"id": anchor, "title": clean_text(node_text(node))})
        if node.tag != "dt" or not node.attrs.get("id"):
            continue
        signature_classes = set(node.attrs.get("class", "").split())
        declaration = next((parent for parent in reversed(ancestors) if parent.tag == "dl"), None)
        declaration_classes = set(declaration.attrs.get("class", "").split()) if declaration else set()
        if "py" not in signature_classes or "py" not in declaration_classes:
            continue
        kind = next((candidate for candidate in ("class", "function", "method", "attribute", "data", "exception", "property", "decorator") if candidate in declaration_classes), None)
        if kind is None:
            continue
        kind = {"exception": "class", "property": "attribute", "decorator": "function"}.get(kind, kind)
        name = node.attrs["id"]
        if name in seen_symbols:
            continue
        seen_symbols.add(name)
        symbols.append({"name": name, "url": urldefrag(url)[0] + "#" + name,
                        "kind": kind, "signature": clean_text(node_text(node))})
    return {"title": title, "text": text, "symbols": symbols, "links": links, "sections": sections}


def html_redirect(payload, url):
    """Recognize Sphinx's legacy-page redirect, bounded to the same version."""
    parser = DocumentParser()
    parser.feed(payload.decode("utf-8"))
    for node, _ in walk(parser.root):
        if node.tag == "meta" and node.attrs.get("http-equiv", "").lower() == "refresh":
            match = re.match(r"^\s*\d+\s*;\s*url\s*=\s*['\"]?(.+?)['\"]?\s*$",
                             node.attrs.get("content", ""), re.IGNORECASE)
            if match:
                target = official_url(match.group(1), url)
                if target is None:
                    raise ValueError("HTML redirect outside Python 3.16 documentation")
                return urldefrag(target)[0]
    return None


def discover_asyncio_urls(documents):
    return sorted({urldefrag(link)[0] for document in documents for link in document["links"]
                   if ASYNCIO_PATH.fullmatch(urlsplit(link).path) and official_url(link)})


def document_id(url):
    path = urlsplit(url).path.removeprefix("/3.16/").removesuffix(".html")
    return path.removeprefix("library/").replace("/", "-")


def select_symbols(identifier, symbols):
    pattern = SYMBOL_SELECTION.get(identifier)
    return [symbol for symbol in symbols if re.match(pattern, symbol["name"])] if pattern else symbols


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_document(root, url, payload, category, reason, coverage="full_page", discovered_from=None, required=True):
    if official_url(url) != url:
        raise ValueError("Snapshot URL must be a canonical Python 3.16 HTML page")
    parsed = parse_document(payload.decode("utf-8"), url)
    if not parsed["title"] or not parsed["text"].strip():
        raise ValueError("Document title/body is empty")
    identifier = document_id(url)
    symbols = select_symbols(identifier, parsed["symbols"])
    html_path = "official/html/" + identifier + ".html"
    text_path = "official/text/" + identifier + ".txt"
    text_bytes = parsed["text"].encode("utf-8")
    for path, content in ((html_path, payload), (text_path, text_bytes)):
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    section_pattern = re.compile(r"async|await|coroutin", re.IGNORECASE) if coverage == "matched_sections" else SECTION_RELEVANT
    matches = [{**section, "url": url + "#" + section["id"]}
               for section in parsed["sections"] if section_pattern.search(section["id"] + " " + section["title"])]
    if coverage == "matched_sections":
        matches.extend({"id": symbol["name"], "title": symbol["signature"], "url": symbol["url"], "kind": "api"} for symbol in symbols)
    return {
        "id": identifier, "url": url, "title": parsed["title"], "category": category,
        "status": "ok", "html_path": html_path, "text_path": text_path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "text_sha256": hashlib.sha256(text_bytes).hexdigest(), "fetched_at": now(),
        "symbols": symbols, "links": parsed["links"], "reason": reason,
        "coverage": coverage, "matched_sections": matches,
        "required": required,
        "matched_symbols": [symbol["name"] for symbol in symbols],
        "snapshot_scope": "full_official_page",
        "symbol_scope": "selected_async_concurrency_apis" if identifier in SYMBOL_SELECTION else "full_page",
        "source_symbol_count": len(parsed["symbols"]),
        "discovered_from": discovered_from or [],
    }


def fetch_url(url, retries=3, timeout=35):
    if official_url(url) != url:
        raise ValueError("Only canonical docs.python.org/3.16 HTML URLs can be fetched")
    for attempt in range(retries):
        try:
            request = Request(url, headers={"User-Agent": "PythonAsyncReferenceSnapshot/1.0 (stdlib urllib)"})
            with build_opener(OfficialRedirectHandler()).open(request, timeout=timeout) as response:
                if official_url(response.geturl()) != response.geturl():
                    raise ValueError("Redirect escaped the Python 3.16 documentation")
                if "html" not in response.headers.get_content_type():
                    raise ValueError("Response is not HTML")
                return FetchResult(response.geturl(), response.read())
        except (HTTPError, URLError, TimeoutError) as error:
            if isinstance(error, HTTPError) and error.code not in {408, 429, 500, 502, 503, 504}:
                raise
            if attempt + 1 == retries:
                raise
            time.sleep(2 ** attempt)


def collect_documents(root, specifications, fetcher=fetch_url, workers=4):
    def collect_one(spec):
        try:
            target = spec["url"]
            chain = [target]
            for _ in range(5):
                fetched = fetcher(target)
                if isinstance(fetched, FetchResult):
                    payload = fetched.payload
                    if fetched.url != target:
                        target = fetched.url
                        chain.append(target)
                else:
                    payload = fetched
                redirected = html_redirect(payload, target)
                if redirected is None:
                    break
                if redirected in chain:
                    raise ValueError("HTML redirect cycle")
                target = redirected
                chain.append(target)
            else:
                raise ValueError("HTML redirect limit exceeded")
            current_spec = {**spec, "url": target}
            document = save_document(root, payload=payload, **current_spec)
            if len(chain) > 1:
                document["requested_url"] = spec["url"]
                document["redirect_chain"] = chain
            return document
        except Exception as error:
            return {
                "id": document_id(spec["url"]), "url": spec["url"], "title": "",
                "category": spec["category"], "status": "error", "html_path": None,
                "text_path": None, "sha256": None, "text_sha256": None,
                "fetched_at": now(), "symbols": [], "links": [], "reason": spec["reason"],
                "coverage": spec.get("coverage", "full_page"), "matched_sections": [],
                "required": spec.get("required", True),
                "matched_symbols": [], "discovered_from": spec.get("discovered_from", []),
                "error": type(error).__name__ + ": " + str(error),
            }
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(collect_one, spec) for spec in specifications]
        documents = [future.result() for future in as_completed(futures)]
    return sorted(documents, key=lambda document: document["url"])


def collect(root, workers=4):
    root = Path(root)
    initial = collect_documents(root, [
        {"url": url, "category": "asyncio", "coverage": "full_page",
         "reason": "Official asyncio discovery entry point."} for url in INDEX_URLS
    ], workers=workers)
    discovered = discover_asyncio_urls(initial)
    specifications = {}
    for url in sorted(set(discovered) | set(REQUESTED_URLS)):
        if url in INDEX_URLS:
            continue
        requested = url in REQUESTED_URLS
        specifications[url] = {
            "url": url, "category": "asyncio", "coverage": "full_page",
            "reason": "User-requested asyncio page." if requested else "Asyncio page linked by an official discovery entry point.",
            "discovered_from": [document["url"] for document in initial
                                if any(urldefrag(link)[0] == url for link in document["links"])],
        }
    for path, category, coverage, reason in SUPPLEMENTAL_PAGES:
        url = BASE + path
        specifications[url] = {"url": url, "category": category, "coverage": coverage, "reason": reason}
    policy_url = BASE + "library/asyncio-policy.html"
    if policy_url not in discovered:
        specifications[policy_url] = {
            "url": policy_url, "category": "asyncio-historical-probe", "coverage": "full_page",
            "required": False,
            "reason": "Explicit existence probe for the historical event-loop policy page; this page is not linked from the three Python 3.16 discovery entry points, so a fetch failure is retained and is not a missing requested seed.",
        }
    documents = sorted(initial + collect_documents(root, specifications.values(), workers=workers),
                       key=lambda document: (document["category"], document["id"]))
    scope_notes = [
        "Discovery follows asyncio*.html content links from asyncio.html, asyncio-api-index.html and asyncio-llapi-index.html only; supplemental pages are an explicit allowlist.",
        "The scope is asyncio and concurrency. General descriptor/logging/functional/socket tutorials and the general execution model are excluded. Helper pages expose only selected async/concurrency symbols; HTML/text preserve the full original page for provenance and must not be counted as additional in-scope APIs.",
        "sha256 hashes raw HTML bytes; text_sha256 hashes the UTF-8 extracted body. Symbols preserve Sphinx IDs; exception declarations use kind=class and properties use kind=attribute.",
        "Official redirects remain within docs.python.org/3.16. Redirected documents use the final content URL and preserve requested_url plus redirect_chain; in 3.16 the built-in functions/exceptions references moved from library/ to builtins/.",
        "The historical asyncio-policy existence probe is explicitly optional: its recorded HTTP 404 is a warning during offline integrity checks; requested seeds and snapshot corruption remain fatal.",
    ]
    if policy_url not in discovered:
        scope_notes.append("asyncio-policy.html was not linked from the three Python 3.16 discovery entry points. An explicit historical-page existence probe is included, with its actual success/error status preserved.")
    catalog = {"schema_version": 1, "requested_urls": REQUESTED_URLS, "documents": documents,
               "source_version": "3.16", "scope": "asyncio-and-concurrency",
               "collected_at": now(), "discovery_urls": INDEX_URLS,
               "scope_notes": scope_notes}
    manifest = root / "official/catalog.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return catalog


def check_catalog(root, warnings=None):
    """Return local integrity errors; append optional fetch failures to warnings."""
    root = Path(root)
    try:
        catalog = json.loads((root / "official/catalog.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return ["catalog unreadable: " + str(error)]
    errors = []
    if catalog.get("schema_version") != 1:
        errors.append("unsupported catalog schema_version")
    if catalog.get("requested_urls") != REQUESTED_URLS:
        errors.append("requested_urls does not preserve the 12 requested pages")
    documents = catalog.get("documents")
    if not isinstance(documents, list):
        return errors + ["documents must be a list"]
    urls, ids = set(), set()
    for document in documents:
        if not isinstance(document, dict):
            errors.append("document is not an object")
            continue
        identifier, url = document.get("id"), document.get("url")
        label = str(identifier)
        if not isinstance(url, str) or official_url(url) != url or urldefrag(url)[1]:
            errors.append(label + ": invalid Python 3.16 URL")
        if url in urls or identifier in ids:
            errors.append(label + ": duplicate document URL or id")
        urls.add(url)
        ids.add(identifier)
        required = {"id", "url", "title", "category", "status", "html_path", "text_path", "sha256", "fetched_at", "symbols", "links", "reason"}
        if missing := required - document.keys():
            errors.append(label + ": missing fields " + ", ".join(sorted(missing)))
        if document.get("status") != "ok":
            message = label + ": document fetch failed: " + document.get("error", "unknown failure")
            if document.get("status") == "error" and document.get("required") is False and url not in REQUESTED_URLS:
                if warnings is not None:
                    warnings.append(message)
            else:
                errors.append(message)
            continue
        for field, digest_field, folder, extension in (
            ("html_path", "sha256", "html", "html"),
            ("text_path", "text_sha256", "text", "txt"),
        ):
            expected_path = "official/" + folder + "/" + label + "." + extension
            if document.get(field) != expected_path or not re.fullmatch(r"[a-zA-Z0-9_.-]+", label):
                errors.append(label + ": unsafe or unexpected " + field)
                continue
            try:
                payload = (root / expected_path).read_bytes()
                if hashlib.sha256(payload).hexdigest() != document.get(digest_field):
                    errors.append(label + ": " + folder + " sha256 mismatch")
            except OSError as error:
                errors.append(label + ": snapshot unreadable: " + str(error))
        for symbol in document.get("symbols", []):
            if not isinstance(symbol, dict) or not all(symbol.get(key) for key in ("name", "url", "kind", "signature")):
                errors.append(label + ": malformed symbol")
            elif symbol["url"] != str(url) + "#" + symbol["name"]:
                errors.append(label + ": symbol URL does not match its official ID")
        if any(not official_url(link, str(url)) for link in document.get("links", [])):
            errors.append(label + ": out-of-scope content link")
    for url in REQUESTED_URLS:
        if url not in urls:
            errors.append("requested page missing: " + url)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=4)
    parser.add_argument("--check", action="store_true", help="validate local files only; never fetch")
    args = parser.parse_args(argv)
    if not args.check:
        catalog = collect(args.output_root, workers=args.workers)
        documents = catalog["documents"]
        print("Collected {} documents: {} ok, {} failed; {} API signatures".format(
            len(documents), sum(document["status"] == "ok" for document in documents),
            sum(document["status"] == "error" for document in documents),
            sum(len(document["symbols"]) for document in documents)))
    warnings = []
    errors = check_catalog(args.output_root, warnings=warnings)
    for warning in warnings:
        print("WARNING (optional page): " + warning, file=sys.stderr)
    for error in errors:
        print("ERROR: " + error, file=sys.stderr)
    if not errors:
        print("Offline snapshot and catalog integrity checks passed.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
