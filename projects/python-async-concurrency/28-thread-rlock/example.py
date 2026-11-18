import threading


def main():
    lock = threading.RLock()  # 同一线程可以重复取得这把锁。
    with lock:  # 第一次取得；退出外层时才完成最后一次释放。
        print("outer acquired")
        with lock:  # 当前线程第二次取得同一把锁，不会等待自己。
            print("inner acquired")
        print("inner released; outer still holds lock")
    print("outer released")


if __name__ == "__main__":
    main()
