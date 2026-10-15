from concurrent.futures import ThreadPoolExecutor
import threading


# 两份工作共用的通知：11 打印完成日志后，才允许 10 继续。
second_finished = threading.Event()


def generate(rollout_id):
    if rollout_id == 10:
        second_finished.wait()  # 执行 10 的工作线程在这里等通知。
    # 这是工作线程打印的日志；函数还要继续到下面的 return。
    print("finished", rollout_id)
    if rollout_id == 11:
        second_finished.set()  # 11 已打印，通知 10 可以继续。
    return rollout_id  # 交给 map 保存，随后由主线程取出。


def main():
    second_finished.clear()  # 每次运行实验前，先把通知复位为 False。
    # 本例需要两个工作线程，让 10 等待时，11 仍能执行。
    with ThreadPoolExecutor(max_workers=2) as executor:
        # 提交 generate(10)、generate(11)，返回结果迭代器。
        results = executor.map(generate, [10, 11])
        # 主线程按输入顺序取结果：先取 10，再取 11；必要时等待。
        for result in results:
            print("received", result)


if __name__ == "__main__":
    main()
