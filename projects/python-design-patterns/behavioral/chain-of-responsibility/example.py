"""
Chain of Responsibility - Python 3.12+ Example: PEP 695 Generic Pipeline
"""
from collections.abc import Callable

type Step[Req, Res] = Callable[[Req], Res | None]


class Pipeline[Req, Res]:
    def __init__(self, steps: list[Step[Req, Res]]) -> None:
        self._steps = steps

    def execute(self, req: Req, fallback: Res) -> Res:
        for step in self._steps:
            res = step(req)
            # None 表示继续传递；首个非 None 结果结束处理。
            if res is not None:
                return res
        return fallback


if __name__ == "__main__":
    steps: list[Step[int, str]] = [
        lambda n: "Negative" if n < 0 else None,
        lambda n: "Zero" if n == 0 else None,
        lambda n: "Positive" if n > 0 else None,
    ]
    p = Pipeline(steps)
    print(p.execute(-5, "Unknown"))
    print(p.execute(42, "Unknown"))
