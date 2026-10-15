import threading


def worker(lock, state):
    for _ in range(1000):
        with lock:
            current = state["count"]
            state["count"] = current + 1


def main():
    lock = threading.Lock()
    state = {"count": 0}
    threads = [threading.Thread(target=worker, args=(lock, state)) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print("count", state["count"])


if __name__ == "__main__":
    main()
