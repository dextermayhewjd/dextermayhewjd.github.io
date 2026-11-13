"""
Bridge - Python 3.12+ Example: PEP 695 Generic Bridge & @override
"""
from dataclasses import dataclass
from typing import Protocol, override


class RenderBackend(Protocol):
    def draw_primitive(self, name: str) -> str: ...


class VectorRenderer:
    def draw_primitive(self, name: str) -> str:
        return f"Vector drawing of {name}"


class RasterRenderer:
    def draw_primitive(self, name: str) -> str:
        return f"Raster pixels for {name}"


@dataclass
class Shape[R: RenderBackend]:
    renderer: R

    def draw(self) -> str:
        return self.renderer.draw_primitive("generic_shape")


class Circle[R: RenderBackend](Shape[R]):
    @override
    def draw(self) -> str:
        # 圆形将绘制操作交给当前绑定的渲染器。
        return self.renderer.draw_primitive("circle")


if __name__ == "__main__":
    c = Circle(VectorRenderer())
    print(c.draw())
