"""
Observer - Python 3.12+ Example: PEP 695 Generic EventSource
"""
from collections.abc import Callable

type Listener[T] = Callable[[T], None]


class EventSource[T]:
    def __init__(self) -> None:
        self._listeners: list[Listener[T]] = []

    def add_listener(self, listener: Listener[T]) -> None:
        self._listeners.append(listener)

    def emit(self, event: T) -> None:
        for listener in self._listeners:
            # 同步通知一个监听函数；返回后再通知下一个。
            listener(event)


if __name__ == "__main__":
    source: EventSource[dict[str, int]] = EventSource()
    source.add_listener(lambda payload: print(f"Listener received: {payload}"))
    source.emit({"temperature": 24, "humidity": 60})
