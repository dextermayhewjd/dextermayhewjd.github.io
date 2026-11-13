"""
Factory Method - Python 3.12+ Example: PEP 695 Generic Factory & Type Alias
"""
from collections.abc import Callable
from dataclasses import dataclass
from typing import override

type Factory[T] = Callable[[], T]


@dataclass
class Button:
    label: str

    def render(self) -> str:
        return f"Button({self.label})"


class HTMLButton(Button):
    @override
    def render(self) -> str:
        return f"<button>{self.label}</button>"


class Dialog[T: Button]:
    def __init__(self, factory: Factory[T]) -> None:
        self._factory = factory

    def render(self) -> str:
        # 调用保存的工厂函数，取得一个具体按钮实例。
        btn = self._factory()
        return f"Dialog container with: {btn.render()}"


if __name__ == "__main__":
    html_dialog = Dialog(lambda: HTMLButton("Submit"))
    print(html_dialog.render())
