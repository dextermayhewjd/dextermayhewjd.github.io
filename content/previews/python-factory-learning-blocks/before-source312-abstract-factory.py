"""Abstract Factory - Python 3.12, preserving the dark/light teaching scenario."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Button:
    theme: str

    def render(self) -> str:
        return f"[{self.theme} Button]"


@dataclass(frozen=True)
class Checkbox:
    theme: str

    def render(self) -> str:
        return f"[{self.theme} Checkbox]"


class GUIFactory[B, C](Protocol):
    """B and C describe the two kinds of products returned by a factory."""

    def create_button(self) -> B: ...
    def create_checkbox(self) -> C: ...


class DarkThemeFactory:
    def create_button(self) -> Button:
        return Button(theme="Dark")

    def create_checkbox(self) -> Checkbox:
        return Checkbox(theme="Dark")


class LightThemeFactory:
    def create_button(self) -> Button:
        return Button(theme="Light")

    def create_checkbox(self) -> Checkbox:
        return Checkbox(theme="Light")


def get_factory(theme: str) -> GUIFactory[Button, Checkbox]:
    match theme:
        case "dark":
            return DarkThemeFactory()
        case "light":
            return LightThemeFactory()
        case _:
            raise ValueError(f"Unknown theme: {theme}")


if __name__ == "__main__":
    factory = get_factory("dark")  # 同一个工厂提供同一主题的两种产品。
    print(factory.create_button().render(), factory.create_checkbox().render())
