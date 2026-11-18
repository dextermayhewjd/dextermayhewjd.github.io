from concurrent.futures import ThreadPoolExecutor, TimeoutError
import threading


def blocked_read(entered, release):
    entered.set()  # 工作线程通知主线程：已经开始执行。
    release.wait()  # 等主线程放行后，才允许返回结果。
    return 10


def broken_read():
    # 第二份独立工作：用固定错误观察 result 和 exception 的区别。
    raise ValueError("read failed")


def main():
    # 两个标志各管一件事：entered 确认开始，release 允许结束。
    entered = threading.Event()
    release = threading.Event()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(blocked_read, entered, release)
        entered.wait()  # 主线程先确认工作已进入，再检查未完成状态。
        try:
            # 尚未发出 release 通知，工作不能返回，所以是 False。
            print("done before release", future.done())
            try:
                # 不等待；结果尚未就绪，抛出 TimeoutError。
                future.result(timeout=0)
            except TimeoutError:
                print("wait timed out")
        finally:
            release.set()  # 即使检查过程出错，也要放行，避免线程一直等。
        # 等待同一份工作结束并读取 10；没有重新提交。
        print("result after release", future.result())

        # 下面换成另一份会报错的工作，仍使用同一个线程池。
        failed = executor.submit(broken_read)
        try:
            failed.result()  # 等待后，重新抛出工作函数中的 ValueError。
        except ValueError as error:
            print("result raised", str(error))
        # 工作已经结束，这次直接读取保存的异常对象。
        print("stored exception", type(failed.exception()).__name__)


if __name__ == "__main__":
    main()
