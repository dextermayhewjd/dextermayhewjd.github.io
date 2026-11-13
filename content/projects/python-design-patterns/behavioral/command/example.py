"""
Command - Python 3.12+ Example: PEP 695 Generic Command & typing.Self
"""
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Action[T]:
    payload: T
    forward: Callable[[T], None]
    backward: Callable[[T], None]

    def apply(self) -> None:
        # 执行之前保存的动作，将 payload 交给正向函数。
        self.forward(self.payload)

    def revert(self) -> None:
        self.backward(self.payload)


class TextBuffer:
    def __init__(self) -> None:
        self.content: list[str] = []

    def make_append_action(self, text: str) -> Action[str]:
        return Action(
            payload=text,
            forward=lambda t: self.content.append(t),
            backward=lambda _: self.content.pop() if self.content else None,
        )


if __name__ == "__main__":
    buf = TextBuffer()
    act = buf.make_append_action("Hello Python 3.12")
    act.apply()
    print(f"Buffer: {buf.content}")
    act.revert()
    print(f"Buffer after revert: {buf.content}")
