"""Teaching extension of Slime's AsyncLoopThread; stdlib only."""
import asyncio
import threading


class AsyncLoopThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        finally:
            # Teaching addition: Slime's original class has no close method.
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.run_until_complete(self.loop.shutdown_default_executor())
            self.loop.close()
            asyncio.set_event_loop(None)

    def run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def close(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self._thread.join()


async def exercise():
    loop = asyncio.get_running_loop()
    current = asyncio.current_task()
    print('loop running', loop.is_running())
    print('current registered', current in asyncio.all_tasks())

    completed = []
    future = loop.create_future()
    future.add_done_callback(lambda done: completed.append(done.result()))
    loop.call_soon(future.set_result, 7)
    print('future result', await future)
    print('future callback', completed)

    failed = loop.create_future()
    loop.call_later(0, failed.set_exception, ValueError('bad value'))
    try:
        await failed
    except ValueError as error:
        print('future error', str(error))

    cancelled = loop.create_future()
    cancelled.cancel()
    print('future cancelled', cancelled.cancelled(), cancelled.done())

    task = asyncio.create_task(asyncio.sleep(0, result=9))
    await task
    print('task state', task.done(), task.result(), task.exception())
    print('task loop', task.get_loop() is loop)

    pending = asyncio.create_task(asyncio.sleep(60))
    pending.cancel()
    try:
        await pending
    except asyncio.CancelledError:
        print('task cancelled', pending.cancelled(), pending.done())


if __name__ == '__main__':
    worker = AsyncLoopThread()
    try:
        worker.run(exercise())
    finally:
        worker.close()
    print('thread stopped', not worker._thread.is_alive())
