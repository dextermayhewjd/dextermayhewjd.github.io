from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples):
    # 工作线程执行这里，返回一份样本列表。
    return list(range(num_samples))


def main():
    # 主线程创建线程池；最多使用两个工作线程，按需创建或复用。
    with ThreadPoolExecutor(max_workers=2) as executor:
        # 提交两次函数调用；first、second 各自保存一份 Future。
        first = executor.submit(get_samples, 3)
        second = executor.submit(get_samples, 2)
        # 主线程取第一份结果；未完成就阻塞等待，完成后返回列表。
        print("first", first.result())
        # 再取第二份结果；这时它可能已经完成，无需再等。
        print("second", second.result())
        # 第一份结果已经取到，因此 done() 为 True。
        print("done", first.done())
        # 第一份工作正常完成，没有保存的异常，因此返回 None。
        print("exception", first.exception())
    # 离开 with 前，线程池已等完工作并完成关闭。
    print("pool closed")


if __name__ == "__main__":
    main()
