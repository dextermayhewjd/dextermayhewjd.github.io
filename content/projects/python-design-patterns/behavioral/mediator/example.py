"""
Mediator - Python 3.12+ Example: PEP 695 Generic Event Mediator
"""
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class UIAction:
    widget_id: str
    payload: str


class Mediator[Msg]:
    def __init__(self) -> None:
        self._handlers: list[Callable[[Msg], None]] = []

    def register(self, handler: Callable[[Msg], None]) -> None:
        self._handlers.append(handler)

    def broadcast(self, message: Msg) -> None:
        for handler in self._handlers:
            # 中心将同一条消息同步交给每个处理函数。
            handler(message)


if __name__ == "__main__":
    mediator: Mediator[UIAction] = Mediator()
    mediator.register(lambda a: print(f"Handler 1 received action from {a.widget_id}: {a.payload}"))
    mediator.register(lambda a: print(f"Handler 2 logging {a.payload}"))
    mediator.broadcast(UIAction("btn_submit", "Click event triggered"))
