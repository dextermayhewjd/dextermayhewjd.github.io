"""
Composite - Python 3.12+ Example: PEP 695 Generic Tree & Pattern Matching
"""
from dataclasses import dataclass, field

type Tree[T] = Leaf[T] | Group[T]


@dataclass
class Leaf[T]:
    value: T

    def render(self) -> str:
        return f"Leaf({self.value})"


@dataclass
class Group[T]:
    children: list[Tree[T]] = field(default_factory=list)

    def add(self, child: Tree[T]) -> None:
        self.children.append(child)

    def render(self) -> str:
        # 子节点可以是叶子或分组，都通过 render 取得结果。
        inner = ", ".join(c.render() for c in self.children)
        return f"Group([{inner}])"


if __name__ == "__main__":
    root: Group[int] = Group()
    sub: Group[int] = Group()
    sub.add(Leaf(10))
    sub.add(Leaf(20))
    root.add(sub)
    root.add(Leaf(30))
    print(root.render())
