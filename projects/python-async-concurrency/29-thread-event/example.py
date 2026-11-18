import threading


def worker(stop):
    # 工作线程：等待主线程发出退出通知。
    # 如果通知已经发出，这里会直接继续。
    stop.wait()
    # 收到通知后收尾；函数返回，这条工作线程就结束。
    print("worker cleanup")


def main():
    # 主线程执行这里：启动工作线程、通知退出，再等它结束。
    # 1. 创建通知对象；此时标志为 False，还没有退出通知。
    stop = threading.Event()
    # 2. 创建线程对象，把同一个 stop 交给 worker 使用。
    thread = threading.Thread(
        target=worker,
        args=(stop,),
    )
    thread.start()  # 启动工作线程，执行 worker(stop)。

    # 3. 主线程决定结束后台工作，设置退出通知。
    print("main requests stop")
    stop.set()  # 标志变为 True，允许 stop.wait() 返回。

    # 4. 等工作线程收尾并结束，主线程才继续往下走。
    thread.join()
    print("joined", thread.is_alive())  # False：工作线程已经结束。


if __name__ == "__main__":
    main()
