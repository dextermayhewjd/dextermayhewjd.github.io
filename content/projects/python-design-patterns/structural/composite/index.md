---
title: "组合 · Composite"
description: "用一致的方式处理单个元素和嵌套容器。"
weight: 30
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [结构型](../)

## 1. 要解决什么问题

**用一致的方式处理单个元素和嵌套容器。**

当核心模型呈现树状结构（例如图形界面节点、组织架构、文件系统或嵌套菜单）时，如果对简单对象和复合容器采用不同的方法处理，客户端代码将充斥大量的类型检查和多层嵌套循环。

## 2. 在 Python 中怎样表达

Leaf[T] 保存叶子值，Group[T] 保存子节点；type Tree[T] = Leaf[T] | Group[T] 描述两种节点的联合类型。render 递归组合子节点的结果。

**运行前先观察：**Group 中再放入 Group 时，render 如何继续取得其中 Leaf 的结果？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
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
```

运行输出：

```text
Group([Group([Leaf(10), Leaf(20)]), Leaf(30)])
```

## 4. 使用边界

这是树形结构的简化例子；如果允许循环引用，遍历需要另行处理循环。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Composite - Python 3.10+ Example: Dataclass Tree & Recursive Generator Traversal
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass
class Item:
    name: str
    price: float

    def total(self) -> float:
        return self.price

    def all_items(self) -> Iterator[str]:
        yield f"{self.name} (${self.price:.2f})"


@dataclass
class Box:
    name: str
    children: list[Item | Box] = field(default_factory=list)

    def add(self, child: Item | Box) -> Box:
        self.children.append(child)
        return self

    def total(self) -> float:
        return sum(child.total() for child in self.children)

    def all_items(self) -> Iterator[str]:
        yield f"Box: {self.name}"
        for child in self.children:
            yield from child.all_items()


if __name__ == "__main__":
    order = Box("Order #100")
    electronics = Box("Electronics")
    electronics.add(Item("Phone", 699.0)).add(Item("Headphones", 149.0))
    order.add(electronics).add(Item("Sticker Pack", 4.99))

    print(f"Total: ${order.total():.2f}")
    for entry in order.all_items():
        print(f" - {entry}")
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Composite - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class Component(ABC):
    @property
    def parent(self) -> "Component | None":
        return getattr(self, "_parent", None)

    @parent.setter
    def parent(self, parent: "Component | None") -> None:
        self._parent = parent

    def add(self, component: "Component") -> None:
        pass

    def remove(self, component: "Component") -> None:
        pass

    def is_composite(self) -> bool:
        return False

    @abstractmethod
    def operation(self) -> str:
        pass


class Leaf(Component):
    def operation(self) -> str:
        return "Leaf"


class Composite(Component):
    def __init__(self) -> None:
        self._children: list[Component] = []

    def add(self, component: Component) -> None:
        self._children.append(component)
        component.parent = self

    def remove(self, component: Component) -> None:
        self._children.remove(component)
        component.parent = None

    def is_composite(self) -> bool:
        return True

    def operation(self) -> str:
        results = [child.operation() for child in self._children]
        return f"Branch({'+'.join(results)})"


def client_code(component: Component) -> str:
    return f"RESULT: {component.operation()}"


if __name__ == "__main__":
    simple = Leaf()
    print("Client: I've got a simple component:")
    print(client_code(simple))

    tree = Composite()
    branch1 = Composite()
    branch1.add(Leaf())
    branch1.add(Leaf())

    branch2 = Composite()
    branch2.add(Leaf())

    tree.add(branch1)
    tree.add(branch2)
    print("\nClient: Now I've got a composite tree:")
    print(client_code(tree))
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 需要实现树状对象结构时
- 希望客户端代码以统一方式处理简单和复杂对象时

### 收益

- 可以利用多态和递归机制更方便地使用复杂树结构
- 开闭原则：无需更改现有代码，即可在应用中添加新元素类型

### 代价

- 对于功能差异较大的类，提供公共接口可能会使接口过泛，难以进行类型限制

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / composite](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/structural/composite.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
