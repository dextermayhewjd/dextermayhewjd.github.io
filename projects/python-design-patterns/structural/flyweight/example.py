"""
Flyweight - Python 3.12+ Example: PEP 695 Generic Flyweight Pool
"""
from collections.abc import Hashable
from dataclasses import dataclass


class FlyweightPool[K: Hashable, V]:
    def __init__(self, factory) -> None:
        self._factory = factory
        self._pool: dict[K, V] = {}

    def get(self, key: K) -> V:
        if key not in self._pool:
            # 只有键首次出现时创建共享对象；之后直接复用。
            self._pool[key] = self._factory(key)
        return self._pool[key]


@dataclass(frozen=True, slots=True)
class FontStyle:
    font_family: str
    size: int


if __name__ == "__main__":
    pool = FlyweightPool[tuple[str, int], FontStyle](
        factory=lambda k: FontStyle(k[0], k[1])
    )
    f1 = pool.get(("Helvetica", 12))
    f2 = pool.get(("Helvetica", 12))
    print(f"Cached font shared: {f1 is f2}, font: {f1}")
