import sys


def get_samples(num_samples):
    return list(range(num_samples))


if __name__ == "__main__":
    num_samples = int(sys.argv[1])  # 接收调用方传来的字符串 "3"，转为整数。
    print(get_samples(num_samples))  # 把列表打印成文字，经标准输出交给调用方。
