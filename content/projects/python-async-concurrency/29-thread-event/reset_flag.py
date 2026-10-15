import threading


def main():
    # 独立实验：下面全部由主线程执行，不创建工作线程。
    event = threading.Event()  # 新建通知对象，初始标志为 False。
    event.set()  # 修改标志：设为 True。
    # timeout=0 表示不花时间等待；已有通知，立即返回 True。
    print("after set", event.wait(timeout=0))
    event.clear()  # 修改标志：恢复为 False。
    # 现在没有通知，等待时间又为零，立即超时并返回 False。
    print("after clear", event.wait(timeout=0))


if __name__ == "__main__":
    main()
