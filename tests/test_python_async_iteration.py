"""Check lazy production and consumer-driven progress, not just printed output."""
import asyncio
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest

BUNDLE = Path(__file__).resolve().parents[1] / 'content/projects/python-async-concurrency/22-async-iteration'


class PythonAsyncIteration(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        path = BUNDLE / 'example.py'
        if not path.exists():
            raise AssertionError('The next lesson needs a standalone example.py')
        spec = importlib.util.spec_from_file_location('async_iteration_lesson', path)
        cls.lesson = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.lesson)

    async def test_creation_does_not_start_producing_and_wrong_consumption_does_not_advance(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            stream = self.lesson.ensure_async_iterator([10, 11])
            self.assertEqual(output.getvalue(), '')
            with self.assertRaises(TypeError):
                await stream
            with self.assertRaises(TypeError):
                iter(stream)
            self.assertEqual(output.getvalue(), '')
            await stream.aclose()

    async def test_consumer_finishes_its_body_before_requesting_the_next_item(self):
        entered = asyncio.Event()
        release = asyncio.Event()
        seen = []
        output = io.StringIO()

        async def consume():
            async for item in self.lesson.ensure_async_iterator([10, 11]):
                seen.append(item)
                if item == 10:
                    entered.set()
                    await release.wait()

        with contextlib.redirect_stdout(output):
            task = asyncio.create_task(consume())
            try:
                await asyncio.wait_for(entered.wait(), 1)
                self.assertEqual(seen, [10])
                self.assertIn('source yield 10', output.getvalue())
                self.assertNotIn('source resumed 10', output.getvalue())
                self.assertNotIn('source preparing 11', output.getvalue())
            finally:
                release.set()
                await task
        self.assertEqual(seen, [10, 11])

    async def test_empty_input_and_exhausted_object_do_not_restart(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual([item async for item in self.lesson.ensure_async_iterator([])], [])
            stream = self.lesson.ensure_async_iterator([10, 11])
            self.assertEqual([item async for item in stream], [10, 11])
            self.assertEqual([item async for item in stream], [])


if __name__ == '__main__':
    unittest.main()
