"""Prototype - Python 3.12, preserving the GraphicElement teaching scenario."""

from dataclasses import dataclass, field, replace
from typing import Self

type Metadata = dict[str, str]


@dataclass
class GraphicElement:
    shape: str
    color: str
    metadata: Metadata = field(default_factory=dict)

    def clone(self, **overrides: str | Metadata) -> Self:
        # 创建同类新实例；未覆盖的 metadata 仍复用原字典。
        return replace(self, **overrides)


if __name__ == "__main__":
    proto = GraphicElement(shape="circle", color="red", metadata={"layer": "1"})
    clone1 = proto.clone(color="blue")
    print(f"Original: {proto}")
    print(f"Cloned:   {clone1}")
