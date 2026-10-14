"""Check the Lock lesson with contention and both cancellation positions."""

import asyncio
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest


BUNDLE = Path(__file__).resolve().parents[1] / 'content/projects/python-async-concurrency/19-async-lock'


def load_example(name):
    spec = importlib.util.spec_from_file_location('lock_lesson_' + name, BUNDLE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PythonAsyncLock(unittest.IsolatedAsyncioTestCase):
    async def test_both_lock_forms_preserve_all_updates_in_either_start_order(self):
        for name in ('example', 'manual'):
            lesson = load_example(name)
            for order in (tuple(range(6)), tuple(reversed(range(6)))):
                with self.subTest(example=name, order=order):
                    state, lock = {'count': 0}, asyncio.Lock()
                    with contextlib.redirect_stdout(io.StringIO()):
                        async with asyncio.TaskGroup() as group:
                            for number in order:
                                group.create_task(lesson.increment(str(number), state, lock))
                    self.assertEqual(state['count'], 6)
                    self.assertFalse(lock.locked())

    async def test_cancelled_waiter_does_not_release_the_holders_lock(self):
        lesson = load_example('example')
        state, lock = {'count': 0}, asyncio.Lock()
        async with lock:
            with contextlib.redirect_stdout(io.StringIO()):
                task = asyncio.create_task(lesson.increment('waiting', state, lock))
                await asyncio.sleep(0)
                self.assertFalse(task.done())
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            self.assertTrue(lock.locked())
            self.assertEqual(state['count'], 0)
        self.assertFalse(lock.locked())

    async def test_cancelled_holder_finishes_cleanup_before_reacquisition(self):
        lesson = load_example('cancellation')
        lock = asyncio.Lock()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            task = asyncio.create_task(lesson.hold(lock))
            await asyncio.sleep(0)
            self.assertTrue(lock.locked())
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            await asyncio.wait_for(lock.acquire(), timeout=1)
            lock.release()
        self.assertEqual(output.getvalue().splitlines(), ['holder acquired', 'holder cleanup'])

    async def test_ordinary_exception_releases_the_lock(self):
        lesson = load_example('failure')
        lock = asyncio.Lock()
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, 'update failed'):
                await lesson.update(lock)
        await asyncio.wait_for(lock.acquire(), timeout=1)
        lock.release()


if __name__ == '__main__':
    unittest.main()
