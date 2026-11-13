"""
Strategy - Python 3.12+ Example: PEP 695 Generic Strategy
"""
from collections.abc import Callable

type Strategy[T, R] = Callable[[T], R]


class AlgorithmRunner[T, R]:
    def __init__(self, strategy: Strategy[T, R]) -> None:
        self.strategy = strategy

    def run(self, data: T) -> R:
        # 将输入交给保存的策略函数，返回它的计算结果。
        return self.strategy(data)


if __name__ == "__main__":
    runner = AlgorithmRunner[list[str], list[str]](strategy=lambda items: sorted(items, reverse=True))
    result = runner.run(["apple", "banana", "cherry"])
    print(f"Reversed sort: {result}")
