"""
Proxy - Python 3.12+ Example: PEP 695 Generic Lazy Proxy
"""
from collections.abc import Callable


class HeavyResource:
    def fetch_data(self) -> str:
        return "Heavy payload data loaded"


class LazyProxy[T]:
    def __init__(self, factory: Callable[[], T]) -> None:
        self._factory = factory
        self._target: T | None = None

    @property
    def target(self) -> T:
        if self._target is None:
            # 第一次读取 target 时创建对象，后续读取复用。
            self._target = self._factory()
        return self._target

    def get_data(self) -> str:
        return getattr(self.target, "fetch_data")()


if __name__ == "__main__":
    proxy: LazyProxy[HeavyResource] = LazyProxy(HeavyResource)
    print("Proxy initialized without loading heavy resource.")
    print(proxy.get_data())
