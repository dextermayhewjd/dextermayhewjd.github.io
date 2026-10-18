# AsyncPacer extracted from Slime, commit 22a89f96835969a47055a659c588f46151f8b07a.
# Original class behavior retained; only three print observations and the driver are added.
import asyncio
from collections import deque


class AsyncPacer:
    """Reduce asyncio scheduling pressure by resuming waiting tasks in batches.

    At high concurrency, waking many tasks at once floods the loop's ready
    queue with callbacks, delaying socket I/O and timers. Release at most 64
    waiters per tick, with a 1 ms delay between batches, to spread that work
    across loop iterations. This paces task starts without limiting in-flight
    concurrency or waiting for previously released tasks to finish.

    Use each instance within a single event loop.
    """

    def __init__(self):
        self.pending = deque()
        self.scheduled = False

    async def wait(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending.append(future)
        if not self.scheduled:
            self.scheduled = True
            print("schedule call_soon")  # 教学观察：原源码没有这行输出。
            loop.call_soon(self._release)
        await future

    def _release(self):
        print("release", min(64, len(self.pending)))  # 教学观察：本批放行数量。
        for _ in range(min(64, len(self.pending))):
            future = self.pending.popleft()
            if not future.done():
                future.set_result(None)
        if self.pending:
            # Let socket callbacks and timers run before waking more tasks.
            print("schedule call_later")  # 教学观察：原源码没有这行输出。
            asyncio.get_running_loop().call_later(0.001, self._release)
        else:
            self.scheduled = False


async def exercise():
    pacer = AsyncPacer()
    tasks = [asyncio.create_task(pacer.wait()) for _ in range(65)]  # 比真实每批 64 个多一个。
    await asyncio.gather(*tasks)  # 等 65 个等待者都被放行。
    print("finished", len(tasks))


if __name__ == "__main__":
    asyncio.run(exercise())
