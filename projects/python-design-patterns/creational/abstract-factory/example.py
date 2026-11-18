"""
Abstract Factory - Python 3.12+ Example: PEP 695 Generic Family Factory
"""
from dataclasses import dataclass
from typing import Protocol

type ComponentPair[B, C] = tuple[B, C]


@dataclass(frozen=True)
class Button:
    label: str


@dataclass(frozen=True)
class Checkbox:
    checked: bool


class Factory[B: Button, C: Checkbox](Protocol):
    def create_button(self) -> B: ...
    def create_checkbox(self) -> C: ...


class StandardFactory:
    def create_button(self) -> Button:
        return Button(label="Standard")

    def create_checkbox(self) -> Checkbox:
        return Checkbox(checked=True)


def build_ui[B: Button, C: Checkbox](factory: Factory[B, C]) -> ComponentPair[B, C]:
    # 同一个工厂分别创建两种产品，作为一个元组返回。
    return factory.create_button(), factory.create_checkbox()


if __name__ == "__main__":
    b, c = build_ui(StandardFactory())
    print(f"UI Created: {b}, {c}")
