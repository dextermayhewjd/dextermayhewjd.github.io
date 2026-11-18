import threading


def worker(rollout_id):
    # 工作线程启动后，实际执行的是这里的函数体。
    print("worker", rollout_id)


def main():
    # 1. 创建线程对象，记住要执行 worker(10)，此时还没启动。
    thread = threading.Thread(target=worker, args=(10,))

    # False 表示尚未启动，不是 thread 对象不能使用。
    print("before start", thread.is_alive())

    # 2. 启动工作线程，让它执行 worker(10)。
    thread.start()

    # 3. 等工作线程结束；未结束时，主线程会阻塞在这里。
    # 如果工作线程已经结束，join() 就直接返回。
    thread.join()

    # False 表示工作线程已结束；thread 对象仍然存在。
    print("after join", thread.is_alive())


if __name__ == "__main__":
    main()
