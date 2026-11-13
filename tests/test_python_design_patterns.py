"""Check the published entry points and runnable Python pattern examples."""

from html.parser import HTMLParser
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASE = "/projects/python-design-patterns/"
PATTERNS = {
    "creational": "factory-method abstract-factory builder prototype singleton".split(),
    "structural": "adapter bridge composite decorator facade flyweight proxy".split(),
    "behavioral": (
        "chain-of-responsibility command iterator mediator memento observer "
        "state strategy template-method visitor"
    ).split(),
}


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = set()
        self.details = 0
        self.in_pre = False
        self.visible_examples = []
        self.disclosures = {}
        self.visible_text = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.add(attrs["href"])
        if tag == "details":
            self.details += 1
            if "id" in attrs:
                self.disclosures[attrs["id"]] = attrs
        if tag == "pre":
            self.in_pre = True
            if self.details == 0:
                self.visible_examples.append("")

    def handle_endtag(self, tag):
        if tag == "details":
            self.details -= 1
        if tag == "pre":
            self.in_pre = False

    def handle_data(self, data):
        if self.details == 0:
            self.visible_text.append(data)
        if self.in_pre and self.details == 0:
            self.visible_examples[-1] += data


@unittest.skipUnless(shutil.which("hugo"), "Hugo is required")
class PythonDesignPatterns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name)
        subprocess.run(
            ["hugo", "--destination", cls.temp.name, "--quiet"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )

    def page(self, url):
        path = self.output / url.lstrip("/") / "index.html"
        self.assertTrue(path.is_file(), f"Missing published page: {url}")
        return Page(path.read_text())

    def test_home_and_project_directory_link_to_patterns(self):
        self.assertIn(BASE, self.page("/").links)
        self.assertIn(BASE, self.page("/projects/").links)

    def test_all_patterns_are_reachable_from_their_category(self):
        overview = self.page(BASE)
        for category, patterns in PATTERNS.items():
            category_url = f"{BASE}{category}/"
            with self.subTest(category=category):
                self.assertIn(category_url, overview.links)
                category_page = self.page(category_url)
                for pattern in patterns:
                    self.assertIn(f"{category_url}{pattern}/", category_page.links)

    def test_primary_python_examples_execute_and_match_output(self):
        for category, patterns in PATTERNS.items():
            for pattern in patterns:
                with self.subTest(pattern=pattern):
                    page = self.page(f"{BASE}{category}/{pattern}/")
                    # The primary example and its output precede optional walkthrough snippets.
                    self.assertGreaterEqual(len(page.visible_examples), 2)
                    code = page.visible_examples[0]
                    result = subprocess.run(
                        [sys.executable, "-I", "-c", code], cwd=self.temp.name,
                        capture_output=True, text=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue(result.stdout.strip(), "Example should show a result")
                    if pattern != "decorator":
                        self.assertEqual(result.stdout.strip(), page.visible_examples[1].strip())

    def test_all_primary_lessons_target_python312(self):
        for category, patterns in PATTERNS.items():
            for pattern in patterns:
                with self.subTest(pattern=pattern):
                    page = self.page(f"{BASE}{category}/{pattern}/")
                    visible = "".join(page.visible_text)
                    self.assertIn("Python 3.12", visible)
                    self.assertNotIn("Python 3.10+ 完整示例", visible)

    def test_singleton_primary_example_shares_a_class_stored_instance(self):
        page = self.page(f"{BASE}creational/singleton/")
        code = page.visible_examples[0]
        self.assertIn("class ServiceRegistry", code)
        namespace = {"__name__": "singleton_test"}
        exec(code, namespace)
        registry = namespace["ServiceRegistry"]
        first = registry.get_instance()
        second = registry.get_instance()
        self.assertIs(first, second)
        self.assertIs(registry._instance, first)

    def test_primary_examples_match_the_local_python312_catalog(self):
        source = ROOT.parent / "back_to_design_pattern" / "src"
        if not source.exists():
            self.skipTest("Local design-pattern catalog is required for source comparison")
        probe = (
            "import ast,json,sys; sys.path.insert(0, sys.argv[1]); "
            "from design_patterns.catalog import ALL_PATTERNS; "
            "print(json.dumps({p.id: ast.dump(ast.parse(p.python312_code)) for p in ALL_PATTERNS}))"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", probe, str(source)],
            check=True, capture_output=True, text=True,
        )
        expected = json.loads(result.stdout)
        for category, patterns in PATTERNS.items():
            for pattern in patterns:
                with self.subTest(pattern=pattern):
                    page = self.page(f"{BASE}{category}/{pattern}/")
                    actual = ast.dump(ast.parse(page.visible_examples[0]))
                    self.assertEqual(actual, expected[pattern])

    def test_factory_publishes_original_python312_with_optional_knowledge(self):
        page = self.page(f"{BASE}creational/factory-method/")
        self.assertIn("class HTMLButton", page.visible_examples[0])
        self.assertIn("class Dialog[T: Button]", page.visible_examples[0])
        for key in (
            "function-value", "function-handoff", "factory-role",
            "callable-annotation", "lambda-expression", "original-python-example",
        ):
            with self.subTest(disclosure=key):
                self.assertIn(key, page.disclosures)
                self.assertNotIn("open", page.disclosures[key])


if __name__ == "__main__":
    unittest.main()
