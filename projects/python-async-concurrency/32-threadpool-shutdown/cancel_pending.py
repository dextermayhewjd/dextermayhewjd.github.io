from concurrent.futures import CancelledError, ThreadPoolExecutor
import threading


def get_samples(num_samples, entered, release):
    entered.set()
    release.wait()
    return list(range(num_samples))


def main():
    entered = threading.Event()
    release = threading.Event()
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        running = executor.submit(get_samples, 3, entered, release)
        entered.wait()
        queued = executor.submit(get_samples, 2, entered, release)
        executor.shutdown(wait=False, cancel_futures=True)
        print("running done", running.done())
        try:
            queued.result()
        except CancelledError:
            print("queued result cancelled")
    finally:
        release.set()
        executor.shutdown(wait=True)
    print("running result", running.result())
    print("cleanup finished")


if __name__ == "__main__":
    main()
