from concurrent.futures import ThreadPoolExecutor


def generate(rollout_id):
    if rollout_id == 11:
        # 让输入 11 对应的工作固定失败。
        raise ValueError("failed 11")
    return rollout_id


def main():
    with ThreadPoolExecutor(max_workers=2) as executor:
        # 提交工作；这里得到迭代器，还没有取出每项结果。
        results = executor.map(generate, [10, 11])
        try:
            # 异常处理覆盖整个取结果过程，而不只包住 map()。
            for result in results:
                print("received", result)  # 先成功取到 10。
        except ValueError as error:
            # 主线程索取 11 的结果时，收到该工作保存的错误。
            print("iteration raised", str(error))


if __name__ == "__main__":
    main()
