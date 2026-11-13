"""
Facade - Python 3.12+ Example: PEP 695 Generic Pipeline Facade
"""
from collections.abc import Callable

type Stage[T, U] = Callable[[T], U]


class PipelineFacade[In, Out]:
    def __init__(self, step1: Stage[In, str], step2: Stage[str, Out]) -> None:
        self._step1 = step1
        self._step2 = step2

    def execute(self, payload: In) -> Out:
        # 先取得中间字符串，再交给第二步。
        intermediate = self._step1(payload)
        return self._step2(intermediate)


if __name__ == "__main__":
    pipeline = PipelineFacade[dict[str, int], int](
        step1=lambda d: f"Length={len(d)}",
        step2=lambda s: len(s),
    )
    result = pipeline.execute({"a": 1, "b": 2})
    print(f"Pipeline Facade output: {result}")
