"""
Iterator - Python 3.12+ Example: PEP 695 Generic Generator & Iterable Protocol
"""
from collections.abc import Iterator


def batch_stream[T](items: list[T], batch_size: int) -> Iterator[list[T]]:
    for i in range(0, len(items), batch_size):
        # 每次交出一批元素，然后暂停等待下一次取值。
        yield items[i : i + batch_size]


class PipelineSource[T]:
    def __init__(self, data: list[T]) -> None:
        self._data = data

    def __iter__(self) -> Iterator[T]:
        yield from self._data


if __name__ == "__main__":
    src: PipelineSource[int] = PipelineSource([1, 2, 3, 4, 5])
    print(f"Pipelined items: {list(src)}")
    batches = list(batch_stream(["a", "b", "c", "d"], batch_size=2))
    print(f"Batches: {batches}")
