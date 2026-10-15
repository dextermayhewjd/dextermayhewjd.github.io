import queue
import threading


def consumer(inbox):
    while True:
        item = inbox.get()
        if item is None:
            print("consumer stopped")
            return
        print("received", item)


def main():
    inbox = queue.Queue(maxsize=1)
    inbox.put(10)
    try:
        inbox.put(11, block=False)
    except queue.Full:
        print("queue full")
    thread = threading.Thread(target=consumer, args=(inbox,))
    thread.start()
    inbox.put(None)
    thread.join()
    print("consumer joined")
    try:
        inbox.get_nowait()
    except queue.Empty:
        print("queue empty")


if __name__ == "__main__":
    main()
