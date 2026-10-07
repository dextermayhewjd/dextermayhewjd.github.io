import asyncio
import unittest

from src.normalize import normalize_first
from src.counter import increment


class InputContract(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(normalize_first([]), "")

    def test_non_empty_input(self):
        self.assertEqual(normalize_first([" hello "]), "hello")


class CounterContract(unittest.IsolatedAsyncioTestCase):
    async def test_two_updates_are_not_lost(self):
        state = {"count": 0}
        await asyncio.gather(increment(state), increment(state))
        self.assertEqual(state["count"], 2)


if __name__ == "__main__":
    unittest.main()
