"""Check the resource lifecycle before entry and on each supported exit path."""

import asyncio
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest


BUNDLE = Path(__file__).resolve().parents[1] / 'content/projects/python-async-concurrency/21-async-contextmanager'
SPEC = importlib.util.spec_from_file_location('contextmanager_lesson', BUNDLE / 'example.py')
LESSON = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LESSON)


class PythonAsyncContextManager(unittest.IsolatedAsyncioTestCase):
    async def test_factory_does_not_prepare_until_entry_and_exit_closes_yielded_object(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            manager = LESSON.boot_agent_sandbox('image', 'normal')
            self.assertEqual(output.getvalue(), '')
            async with manager as sandbox:
                self.assertTrue(sandbox['open'])
                same_object = sandbox
            self.assertIs(sandbox, same_object)
            self.assertFalse(sandbox['open'])
        self.assertEqual(output.getvalue().splitlines(), [
            'boot image normal', 'closing normal', 'closed normal',
        ])

    async def test_body_exception_reaches_caller_after_cleanup(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with self.assertRaisesRegex(ValueError, 'body failed'):
                async with LESSON.boot_agent_sandbox('image', 'failure') as sandbox:
                    raise ValueError('body failed')
            self.assertFalse(sandbox['open'])
        self.assertIn('closed failure', output.getvalue())

    async def test_cancelled_body_waits_for_async_cleanup(self):
        entered = asyncio.Event()
        resources = []

        async def work():
            async with LESSON.boot_agent_sandbox('image', 'cancel') as sandbox:
                resources.append(sandbox)
                entered.set()
                await asyncio.sleep(3600)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            task = asyncio.create_task(work())
            await entered.wait()
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertFalse(resources[0]['open'])
        self.assertEqual(output.getvalue().splitlines()[-2:], ['closing cancel', 'closed cancel'])

    async def test_cancelled_preparation_never_enters_body_or_claims_to_close_uncreated_resource(self):
        entered = []

        async def work():
            async with LESSON.boot_agent_sandbox('image', 'before-entry'):
                entered.append(True)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            task = asyncio.create_task(work())
            await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(entered, [])
        self.assertEqual(output.getvalue().splitlines(), ['boot image before-entry'])


if __name__ == '__main__':
    unittest.main()
