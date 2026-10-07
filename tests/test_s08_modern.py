"""Offline regression checks for the blog's S08 teaching example."""

import copy
import importlib.util
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "static/examples/s08-modern/code.py"


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.counts = []
        self.responses = []
        self.fail_compaction = False
        self.summary = {"type": "compaction", "content": "Goal and pending work.",
                        "signature": "test-only-signature"}

    def count_tokens(self, system, tools, messages):
        self.counts.append(copy.deepcopy((system, tools, messages)))
        return 100

    def generate(self, system, tools, messages, compaction=None):
        self.calls.append(copy.deepcopy({"messages": messages, "system": system,
                                         "tools": tools, "compaction": compaction}))
        if compaction is not None:
            if self.fail_compaction:
                return {"stop_reason": "max_tokens", "content": []}
            return {"stop_reason": "compaction", "content": [copy.deepcopy(self.summary)]}
        return self.responses.pop(0)


class ModernCompactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = None
        if SOURCE.exists():
            spec = importlib.util.spec_from_file_location("s08_modern_example", SOURCE)
            cls.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.module)

    def setUp(self):
        self.assertIsNotNone(self.module, "S08 runnable example has not been created")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.api = FakeAPI()
        self.session = self.module.AgentSession(
            self.api, self.root, budget=1000, emit=lambda text: None,
            restore=lambda: [{"role": "user", "content": "Fresh project context"}],
        )
        self.session.append("user", "Fix the bug, preserve the public API.")

    def test_signed_summary_is_first_and_unchanged(self):
        self.session.append("assistant", [{"type": "text", "text": "Investigating."}])
        self.session.compact("Preserve unverified work")
        self.assertEqual(self.session.history[0],
                         {"role": "assistant", "content": [self.api.summary]})
        self.assertEqual(self.session.history[1]["content"], "Fresh project context")
        self.assertIn("Preserve unverified work", self.api.calls[0]["compaction"]["instructions"])
        self.assertEqual(self.api.calls[0]["system"], self.session.system)
        self.assertEqual(self.api.calls[0]["tools"], self.module.TOOLS)

    def test_missing_summary_keeps_the_original_history(self):
        self.api.fail_compaction = True
        before = copy.deepcopy(self.session.history)
        with self.assertRaises(self.module.CompactionError):
            self.session.compact()
        self.assertEqual(self.session.history, before)

    def test_unfinished_tool_call_cannot_be_compacted(self):
        self.session.append("assistant", [{"type": "tool_use", "id": "a",
                                           "name": "read_file", "input": {"path": "x"}}])
        with self.assertRaises(ValueError):
            self.session.compact()
        self.assertEqual(self.api.calls, [])

    def test_orphan_tool_result_is_rejected(self):
        with self.assertRaises(ValueError):
            self.module.validate_history([
                {"role": "user", "content": [{"type": "tool_result",
                                                "tool_use_id": "missing", "content": "x"}]},
            ])

    def test_all_tools_finish_before_requested_compaction(self):
        (self.root / "sample.txt").write_text("Current file evidence.", encoding="utf-8")
        self.api.responses = [
            {"stop_reason": "tool_use", "content": [
                {"type": "tool_use", "id": "compact-a", "name": "compact",
                 "input": {"focus": "Keep the current constraint"}},
                {"type": "tool_use", "id": "read-b", "name": "read_file",
                 "input": {"path": "sample.txt"}},
            ]},
            {"stop_reason": "end_turn", "content": [{"type": "text", "text": "Done reading."}]},
        ]
        self.assertEqual(self.session.run("Read the file and compact."), "Done reading.")
        compact_call = next(c for c in self.api.calls if c["compaction"] is not None)
        results = compact_call["messages"][-1]["content"]
        self.assertEqual([r["tool_use_id"] for r in results], ["compact-a", "read-b"])
        self.assertIn("Current file evidence.", results[1]["content"])
        self.module.validate_history(compact_call["messages"])
        self.module.validate_history(self.session.history)

    def test_counting_includes_system_tools_and_current_history(self):
        self.api.responses = [{"stop_reason": "end_turn", "content": [{"type": "text", "text": "Answer"}]}]
        self.session.run("Continue.")
        system, tools, messages = self.api.counts[0]
        self.assertEqual(system, self.session.system)
        self.assertEqual(tools, self.module.TOOLS)
        self.assertEqual(messages[-1]["content"], "Continue.")

    def test_restoration_over_budget_does_not_overwrite_history(self):
        self.session.budget = 50
        before = copy.deepcopy(self.session.history)
        with self.assertRaises(self.module.BudgetError):
            self.session.compact()
        self.assertEqual(self.session.history, before)

    def test_project_context_is_read_again_after_file_change(self):
        rules = self.root / "CLAUDE.md"
        rules.write_text("Original rule", encoding="utf-8")
        context = self.module.FileContext(self.api, self.root)
        rules.write_text("Current rule", encoding="utf-8")
        restored = context.restore()[0]["content"]
        self.assertIn("Current rule", restored)
        self.assertNotIn("Original rule", restored)

    def test_large_file_is_restored_as_a_reference(self):
        source = self.root / "big.txt"
        source.write_text("Large body", encoding="utf-8")
        context = self.module.FileContext(self.api, self.root)
        context.remember(source)
        self.api.count_tokens = lambda *args: 6000
        restored = context.restore()[0]["content"]
        self.assertIn("big.txt", restored)
        self.assertNotIn("Large body", restored)

    def test_archive_preserves_messages_that_left_active_context(self):
        self.session.compact()
        archive = self.session.transcript.read_text(encoding="utf-8")
        self.assertIn("preserve the public API", archive)
        self.assertNotIn("Fix the bug", str(self.session.history))

    def test_tool_cannot_read_outside_workspace(self):
        result = self.session.execute({"id": "outside", "name": "read_file",
                                       "input": {"path": "../not-allowed"}})
        self.assertTrue(result["is_error"])
        self.assertIn("outside", result["content"].lower())

    def test_output_limit_is_not_treated_as_task_completion(self):
        self.api.responses = [{"stop_reason": "max_tokens", "content": [{"type": "text", "text": "Partial"}]}]
        with self.assertRaises(RuntimeError):
            self.session.run("Continue.")

    def test_automatic_compaction_runs_before_the_next_task_request(self):
        self.api.count_tokens = lambda system, tools, messages: (
            100 if messages[0]["role"] == "assistant" else 2000
        )
        self.api.responses = [{"stop_reason": "end_turn", "content": [{"type": "text", "text": "Continue"}]}]
        self.session.run("Continue the original task.")
        self.assertIsNotNone(self.api.calls[0]["compaction"])
        self.assertIsNone(self.api.calls[1]["compaction"])
        self.assertEqual(self.api.calls[1]["messages"][0]["content"], [self.api.summary])

    def test_long_read_keeps_the_full_snapshot_outside_the_excerpt(self):
        original = "0123456789" * 1000
        (self.root / "long.txt").write_text(original, encoding="utf-8")
        result = self.session.execute({"id": "long-read", "name": "read_file",
                                       "input": {"path": "long.txt", "limit": 16}})
        saved = list((self.root / ".s08-modern/outputs").glob("*.txt"))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].read_text(encoding="utf-8"), original)
        self.assertIn("0123456789012345", result["content"])
        self.assertLess(len(result["content"]), len(original))

    def test_context_restoration_does_not_require_git_to_be_installed(self):
        with patch.object(self.module.subprocess, "run", side_effect=FileNotFoundError):
            restored = self.module.FileContext(self.api, self.root).restore()
        self.assertIn("unavailable", restored[0]["content"])


if __name__ == "__main__":
    unittest.main()
