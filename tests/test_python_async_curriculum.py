"""Guard curriculum coverage and prerequisites, rather than lesson prose."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / "python-async-reference"
SPEC = importlib.util.spec_from_file_location("async_curriculum", MATERIAL / "tools/build_curriculum.py")
CURRICULUM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CURRICULUM)


class PythonAsyncCurriculum(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((MATERIAL / "curriculum.json").read_text())
        self.scope = json.loads((MATERIAL / "current-api-plan.json").read_text())

    def test_all_apis_have_one_formal_introduction(self):
        owners = CURRICULUM.validate_plan(self.plan, self.scope)
        self.assertEqual(len(owners), 82)
        self.assertEqual(owners["asyncio.run"], 1)
        self.assertEqual(owners["asyncio.wait"], 6)
        self.assertEqual(owners["multiprocessing.Process.kill"], 40)

    def test_revisiting_an_api_does_not_replace_teaching_it(self):
        plan = deepcopy(self.plan)
        plan["lessons"][3]["introduces"].remove("asyncio.TaskGroup")
        with self.assertRaisesRegex(ValueError, "API coverage mismatch"):
            CURRICULUM.validate_plan(plan, self.scope)

    def test_future_prerequisite_is_rejected(self):
        plan = deepcopy(self.plan)
        plan["lessons"][5]["depends_on"].append(7)
        with self.assertRaisesRegex(ValueError, "prerequisite"):
            CURRICULUM.validate_plan(plan, self.scope)

    def test_exception_boundaries_cannot_be_omitted(self):
        plan = deepcopy(self.plan)
        plan["lessons"][8]["exception_types"].remove("asyncio.CancelledError")
        with self.assertRaisesRegex(ValueError, "exception_types"):
            CURRICULUM.validate_plan(plan, self.scope)

    def test_generated_curriculum_is_current(self):
        for path, expected in CURRICULUM.build_outputs().items():
            self.assertEqual(path.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
