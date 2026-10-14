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
        self.assertEqual(owners["asyncio.wait"], 7)
        self.assertEqual(owners["multiprocessing.Process.kill"], 41)

    def test_syntax_prerequisite_precedes_taskgroup(self):
        self.assertEqual(len(self.plan['lessons']), 41)
        syntax = self.plan['lessons'][3]
        taskgroup = self.plan['lessons'][4]
        self.assertEqual(syntax['source_lessons'], ['04-with-async-with'])
        self.assertEqual(syntax['introduces'], [])
        self.assertEqual(syntax['syntax'], ['async with'])
        self.assertEqual(taskgroup['source_lessons'], ['04-taskgroup'])
        self.assertIn(4, taskgroup['depends_on'])
        owners = CURRICULUM.validate_plan(self.plan, self.scope)
        self.assertEqual(owners['asyncio.timeout'], 15)
        self.assertEqual(owners['asyncio.shield'], 16)

    def test_revisiting_an_api_does_not_replace_teaching_it(self):
        plan = deepcopy(self.plan)
        lesson = next(row for row in plan['lessons'] if 'asyncio.TaskGroup' in row['introduces'])
        lesson['introduces'].remove("asyncio.TaskGroup")
        with self.assertRaisesRegex(ValueError, "API coverage mismatch"):
            CURRICULUM.validate_plan(plan, self.scope)

    def test_sublessons_preserve_the_parent_number_and_next_unit(self):
        lesson = self.plan['lessons'][9]
        self.assertIn('parts', lesson)
        self.assertEqual([part['label'] for part in lesson['parts']], ['10.1', '10.2'])
        self.assertEqual(lesson['source_lessons'], [
            '15-gather-failures', '15-gather-exceptions',
        ])
        self.assertEqual(lesson['parts'][1]['depends_on'], ['10.1'])
        self.assertEqual(self.plan['lessons'][10]['number'], 11)
        self.assertIn(10, self.plan['lessons'][10]['depends_on'])
        owners = CURRICULUM.validate_plan(self.plan, self.scope)
        self.assertEqual(len(owners), 82)
        self.assertEqual(owners['asyncio.gather'], 6)
        manifest = json.loads((ROOT / 'python-async-concurrency/project-manifest.json').read_text())
        rendered = CURRICULUM.render_body(self.plan, manifest, web=True)
        self.assertIn('| 10.1 · asyncio.gather', rendered)
        self.assertIn('| 10.2 · return_exceptions=True', rendered)

    def test_failure_units_follow_cancellation_before_completion_order(self):
        pages = [
            row['source_lessons'][0]
            for unit in self.plan['lessons'][:16]
            for row in CURRICULUM.display_lessons(unit)
        ]
        self.assertEqual(pages[8:], [
            '09-task-cancellation',
            '15-gather-failures', '15-gather-exceptions',
            '11-taskgroup-failures', '11-exception-groups',
            '08-as-completed', '10-wait-for', '11-time-budget',
            '12-timeout-scope', '13-shield',
        ])
        owners = CURRICULUM.validate_plan(self.plan, self.scope)
        process_cleanup = self.plan['lessons'][38]
        self.assertIn(owners['asyncio.Task.cancel'], process_cleanup['depends_on'])
        self.assertIn(owners['asyncio.wait_for'], process_cleanup['depends_on'])

    def test_exception_group_syntax_belongs_to_second_sublesson(self):
        parts = CURRICULUM.display_lessons(self.plan['lessons'][10])
        self.assertEqual(len(parts), 2, 'The TaskGroup failure unit needs two sublessons')
        first, second = parts
        self.assertEqual(first['syntax'], [])
        self.assertEqual(first['exception_types'], [])
        self.assertEqual(second['syntax'], ['except*'])
        self.assertEqual(second['exception_types'], ['builtins.ExceptionGroup'])
        document = CURRICULUM.build_outputs()[MATERIAL / 'curriculum.md']
        self.assertIn('| 语法 | `except*` | 11.2 |', document)
        self.assertIn('| 异常类型 | `builtins.ExceptionGroup` | 11.2 |', document)

    def test_sublesson_order_and_mapping_are_validated(self):
        plan = deepcopy(self.plan)
        lesson = plan['lessons'][9]
        lesson['parts'] = [{
            'label': '10.2',
            'title': lesson['title'],
            'question': lesson['question'],
            'takeaway': lesson['takeaway'],
            'check': lesson['check'],
            'source_lessons': ['15-gather-failures'],
        }]
        with self.assertRaisesRegex(ValueError, 'sublesson'):
            CURRICULUM.validate_plan(plan, self.scope)

        for case in ('empty', 'source_mapping', 'future_prerequisite'):
            with self.subTest(case=case):
                plan = deepcopy(self.plan)
                lesson = plan['lessons'][9]
                if case == 'empty':
                    lesson['parts'] = []
                elif case == 'source_mapping':
                    lesson['parts'][1]['source_lessons'] = ['15-gather-failures']
                else:
                    lesson['parts'][0]['depends_on'] = ['10.2']
                with self.assertRaisesRegex(ValueError, 'sublesson'):
                    CURRICULUM.validate_plan(plan, self.scope)

    def test_future_prerequisite_is_rejected(self):
        plan = deepcopy(self.plan)
        plan["lessons"][5]["depends_on"].append(7)
        with self.assertRaisesRegex(ValueError, "prerequisite"):
            CURRICULUM.validate_plan(plan, self.scope)

    def test_exception_boundaries_cannot_be_omitted(self):
        plan = deepcopy(self.plan)
        lesson = next(row for row in plan['lessons'] if 'asyncio.CancelledError' in row['exception_types'])
        lesson['exception_types'].remove("asyncio.CancelledError")
        with self.assertRaisesRegex(ValueError, "exception_types"):
            CURRICULUM.validate_plan(plan, self.scope)

    def test_generated_curriculum_is_current(self):
        for path, expected in CURRICULUM.build_outputs().items():
            self.assertEqual(path.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
