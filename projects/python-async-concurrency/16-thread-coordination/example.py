"""Condition predicate, RLock recursion, and Timer lifecycle; Python 3.11+."""

import threading


def main():
    condition = threading.Condition()
    waiting = threading.Event()
    rechecked = threading.Event()
    notified = threading.Event()
    items = []
    received = []

    def has_data():
        # wait_for evaluates this while holding condition's lock.
        if not items:
            waiting.set()
            if notified.is_set():
                rechecked.set()
        return bool(items)

    def read():
        with condition:
            condition.wait_for(has_data)
            received.append(items.pop(0))

    reader = threading.Thread(target=read)
    reader.start()
    waiting.wait()
    with condition:
        notified.set()
        condition.notify_all()  # No data yet: the predicate stays false.
        print("notify while holding lock", not received)
    rechecked.wait()
    print("predicate still false", not received)
    with condition:
        items.append("sample")
        condition.notify_all()
    reader.join()
    print("received", received)

    lock = threading.RLock()
    lock.acquire()
    try:
        with lock:
            print("same thread entered twice")
        print("outer lock still held")
    finally:
        lock.release()

    called = threading.Event()
    timer = threading.Timer(0, called.set)
    timer.start()
    timer.join()
    print("timer called", called.is_set())

    cancelled_call = threading.Event()
    timer = threading.Timer(0, cancelled_call.set)
    # Cancel before start so this experiment cannot race with the callback.
    timer.cancel()
    timer.start()
    timer.join()
    print("cancelled timer called", cancelled_call.is_set())


if __name__ == "__main__":
    main()
