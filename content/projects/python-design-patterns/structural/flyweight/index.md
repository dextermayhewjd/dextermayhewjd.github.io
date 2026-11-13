---
title: "享元 · Flyweight"
description: "让大量对象共享可复用的状态。"
weight: 60
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [结构型](../)

## 1. 要解决什么问题

**让大量对象共享可复用的状态。**

当系统需要创建海量相似粒度较小的对象（如文字处理器的字符、地图瓦片、粒子特效、游戏内成千上万个NPC），每个对象重复存储大量不变数据会导致内存耗尽崩盘。

## 2. 在 Python 中怎样表达

FlyweightPool[K, V] 按键 K 缓存共享对象 V；首次遇到键时调用工厂创建 FontStyle，后续相同键直接复用。frozen、slots 的 dataclass 保存共享样式。

**运行前先观察：**两次使用相同字体名和字号获取的 FontStyle 是否是同一个对象？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Flyweight - Python 3.12+ Example: PEP 695 Generic Flyweight Pool
"""
from collections.abc import Hashable
from dataclasses import dataclass


class FlyweightPool[K: Hashable, V]:
    def __init__(self, factory) -> None:
        self._factory = factory
        self._pool: dict[K, V] = {}

    def get(self, key: K) -> V:
        if key not in self._pool:
            # 只有键首次出现时创建共享对象；之后直接复用。
            self._pool[key] = self._factory(key)
        return self._pool[key]


@dataclass(frozen=True, slots=True)
class FontStyle:
    font_family: str
    size: int


if __name__ == "__main__":
    pool = FlyweightPool[tuple[str, int], FontStyle](
        factory=lambda k: FontStyle(k[0], k[1])
    )
    f1 = pool.get(("Helvetica", 12))
    f2 = pool.get(("Helvetica", 12))
    print(f"Cached font shared: {f1 is f2}, font: {f1}")
```

运行输出：

```text
Cached font shared: True, font: FontStyle(font_family='Helvetica', size=12)
```

## 4. 使用边界

共享状态需要保持稳定；缓存键决定哪些实例可复用，缓存容量和生命周期也会影响内存占用。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Flyweight - Python 3.10+ Example: Frozen Slots Dataclass & lru_cache Factory
"""
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class TreeType:
    name: str
    color: str
    texture: str


@lru_cache(maxsize=128)
def get_tree_type(name: str, color: str, texture: str) -> TreeType:
    """Flyweight factory: returns cached immutable intrinsic state."""
    return TreeType(name=name, color=color, texture=texture)


@dataclass(slots=True)
class Tree:
    x: int
    y: int
    tree_type: TreeType

    def render(self) -> str:
        return f"Tree '{self.tree_type.name}' at ({self.x}, {self.y})"


if __name__ == "__main__":
    t1 = get_tree_type("Oak", "Green", "rough.png")
    t2 = get_tree_type("Oak", "Green", "rough.png")
    print(f"Flyweights identical: {t1 is t2}")

    forest = [Tree(i, i * 2, t1) for i in range(5)]
    print(f"Planted {len(forest)} trees using 1 flyweight instance.")
    print(forest[0].render())
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Flyweight - Conceptual Example (Classic GoF)
"""
import json


class Flyweight:
    def __init__(self, shared_state: list[str]) -> None:
        self._shared_state = shared_state

    def operation(self, unique_state: list[str]) -> str:
        s = json.dumps(self._shared_state)
        u = json.dumps(unique_state)
        return f"Flyweight: Displaying shared ({s}) and unique ({u}) state."


class FlyweightFactory:
    _flyweights: dict[str, Flyweight] = {}

    def __init__(self, initial_flyweights: list[list[str]]) -> None:
        for state in initial_flyweights:
            self._flyweights[self.get_key(state)] = Flyweight(state)

    def get_key(self, state: list[str]) -> str:
        return "_".join(sorted(state))

    def get_flyweight(self, shared_state: list[str]) -> Flyweight:
        key = self.get_key(shared_state)
        if key not in self._flyweights:
            print(f"FlyweightFactory: Can't find a flyweight, creating new one for {shared_state}.")
            self._flyweights[key] = Flyweight(shared_state)
        else:
            print("FlyweightFactory: Reusing existing flyweight.")
        return self._flyweights[key]

    def list_flyweights(self) -> str:
        count = len(self._flyweights)
        return f"FlyweightFactory: I have {count} flyweights: {list(self._flyweights.keys())}"


if __name__ == "__main__":
    factory = FlyweightFactory([
        ["Chevrolet", "Camaro2018", "pink"],
        ["Mercedes Benz", "C300", "black"],
        ["Mercedes Benz", "C500", "red"],
        ["BMW", "M5", "red"],
        ["BMW", "X6", "white"],
    ])
    print(factory.list_flyweights())

    flyweight = factory.get_flyweight(["BMW", "M5", "red"])
    print(flyweight.operation(["CL234IR", "James Doe"]))
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 仅在程序必须支持大量对象且没有足够的内存容量时使用享元模式

### 收益

- 如果程序中原本存在大量相似对象，使用享元可以极大程度节省内存空间

### 代价

- 牺牲了部分运行时间代码复杂度换取内存，代码逻辑变得更加晦涩
- 每次调用享元方法时需要重新计算或传递外部状态

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / flyweight](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/structural/flyweight.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
