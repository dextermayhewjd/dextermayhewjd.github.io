"""Validate the Event lesson at notification, reset, and cancellation boundaries."""

import asyncio
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest


BUNDLE = Path(__file__).resolve().parents[1] / 'content/projects/python-async-concurrency/20-async-event'


def load_example(name):
    spec = importlib.util.spec_from_file_location('event_lesson_' + name, BUNDLE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PythonAsyncEvent(unittest.IsolatedAsyncioTestCase):
    async def test_set_wakes_all_without_running_them_inline(self):
        lesson = load_example('broadcast')
        ready = asyncio.Event()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            tasks = [asyncio.create_task(lesson.wait_for_start(name, ready)) for name in ('A', 'B')]
            await asyncio.sleep(0)
            self.assertEqual(output.getvalue().splitlines(), ['A waiting', 'B waiting'])
            ready.set()
            self.assertTrue(all(not task.done() for task in tasks))
            self.assertNotIn('continued', output.getvalue())
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=1)
        self.assertEqual(set(output.getvalue().splitlines()[2:]), {'A continued', 'B continued'})
        self.assertTrue(ready.is_set())

    async def test_clear_does_not_retract_an_existing_wakeup(self):
        ready = asyncio.Event()
        first = asyncio.create_task(ready.wait())
        await asyncio.sleep(0)
        ready.set()
        ready.clear()
        self.assertTrue(await asyncio.wait_for(first, timeout=1))
        self.assertFalse(ready.is_set())

        second = asyncio.create_task(ready.wait())
        await asyncio.sleep(0)
        self.assertFalse(second.done())
        ready.set()
        self.assertTrue(await asyncio.wait_for(second, timeout=1))

    async def test_cancelling_one_waiter_does_not_notify_or_cancel_its_peer(self):
        lesson = load_example('cancellation')
        ready = asyncio.Event()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            first = asyncio.create_task(lesson.wait_for_start('A', ready))
            second = asyncio.create_task(lesson.wait_for_start('B', ready))
            await asyncio.sleep(0)
            first.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await first
            self.assertFalse(ready.is_set())
            self.assertFalse(second.done())
            self.assertIn('A cleanup', output.getvalue())
            ready.set()
            await asyncio.wait_for(second, timeout=1)
        self.assertNotIn('A continued', output.getvalue())
        self.assertIn('B continued\nB cleanup', output.getvalue())

    async def test_set_before_wait_and_repeated_wait_leave_the_flag_set(self):
        ready = asyncio.Event()
        self.assertFalse(ready.is_set())
        ready.set()
        ready.set()
        for _ in range(3):
            self.assertTrue(await ready.wait())
            self.assertTrue(ready.is_set())
        ready.clear()
        self.assertFalse(ready.is_set())


if __name__ == '__main__':
    unittest.main()
