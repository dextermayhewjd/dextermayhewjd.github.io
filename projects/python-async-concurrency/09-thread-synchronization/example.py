import threading

lock = threading.Lock()
ready = threading.Event()
state = {"count": 0}

def worker():
    ready.wait()
    for _ in range(1000):
        with lock:
            state["count"] += 1

if __name__ == "__main__":
    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    ready.set()
    for thread in threads:
        thread.join()
    print("count", state["count"])
