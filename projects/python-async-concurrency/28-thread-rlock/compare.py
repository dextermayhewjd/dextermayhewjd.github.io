import threading


def main():
    for name, lock in [("Lock", threading.Lock()), ("RLock", threading.RLock())]:
        first = lock.acquire(blocking=False)  # 不等待；空闲锁第一次获取成功。
        second = False
        try:
            second = lock.acquire(blocking=False)  # 同一线程再次尝试，不等待，避免演示卡住。
            print(f"{name}: first={first}, second={second}")
        finally:
            if second:
                lock.release()  # 只有第二次也成功，才释放第二次获取。
            if first:
                lock.release()  # 配对释放第一次获取。


if __name__ == "__main__":
    main()
