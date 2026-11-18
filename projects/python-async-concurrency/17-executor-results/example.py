"""Observe executor futures without depending on sleep or worker speed."""

import threading
from concurrent.futures import (
    FIRST_COMPLETED,
    CancelledError,
    ThreadPoolExecutor,
    as_completed,
    wait,
)


def read_file(rel_path, started, release):
    # API experiment: replace disk I/O with an explicitly controlled boundary.
    started.set()
    release.wait()
    if rel_path == "broken":
        raise ValueError("cannot read broken")
    return rel_path


def main():
    started, release, callback_done = (threading.Event() for _ in range(3))
    callback_results = []

    def on_done(future):
        callback_results.append(future.result())
        callback_done.set()

    with ThreadPoolExecutor(max_workers=1) as executor:
        running = executor.submit(read_file, "first", started, release)
        started.wait()
        queued = executor.submit(read_file, "queued", started, release)
        print("running", running.running(), "done", running.done())
        print("cancel running", running.cancel())
        print("cancel queued", queued.cancel(), "done", queued.done())
        try:
            queued.result()
        except CancelledError:
            print("queued result CancelledError")
        try:
            running.result(timeout=0)
        except TimeoutError:
            print("result timeout; work still running", running.running())

        running.add_done_callback(on_done)
        release.set()
        print("result", running.result())
        callback_done.wait()  # result() alone does not promise callback completion.
        print("callback", callback_results)
        print("success exception", running.exception())

        failed = executor.submit(read_file, "broken", started, release)
        try:
            failed.result()
        except ValueError as error:
            print("raised", str(error))
        print("stored exception", type(failed.exception()).__name__)
        print("map", list(executor.map(abs, [-3, -1, -2])))

    executor = ThreadPoolExecutor(max_workers=2)
    slow_started, fast_started = threading.Event(), threading.Event()
    slow_release, fast_release = threading.Event(), threading.Event()
    try:
        slow = executor.submit(read_file, "slow", slow_started, slow_release)
        fast = executor.submit(read_file, "fast", fast_started, fast_release)
        slow_started.wait()
        fast_started.wait()
        fast_release.set()
        done, pending = wait([slow, fast], return_when=FIRST_COMPLETED)
        print("first completed", [future.result() for future in done])
        print("pending", len(pending))

        completed = as_completed([slow, fast])
        print("as_completed", next(completed).result())
        slow_release.set()
        print("as_completed", next(completed).result())
    finally:
        # Also unblock workers if an assertion or print fails during the demo.
        slow_release.set()
        fast_release.set()
        executor.shutdown(wait=True, cancel_futures=True)
    print("shutdown finished")


if __name__ == "__main__":
    main()
