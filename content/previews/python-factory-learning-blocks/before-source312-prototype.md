---
title: "原型 · Prototype"
description: "基于已有对象，复制并调整少量状态。"
weight: 40
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [创建型](../)

## 1. 要解决什么问题

**Prototype 是“基于已有实例创建新实例”的方式；底层仍然可以调用构造方法。**

**使用心智模型：**先有一个完整的 `proto` → 把它作为模板，调用 `clone(color="blue")` → 得到新对象 `clone1`。创建数据主要沿用旧实例，只覆盖需要变化的字段；原来的 `proto` 保留。

直接从外部克隆对象不仅需要知道该对象的具体类，且对象私有成员无法直接访问，此外如果对象有复杂的依赖关系，手动复制十分繁琐。

## 2. 在 Python 中怎样表达

Metadata 用 type 声明字典类型别名，clone 用 Self 描述同类返回值。dataclasses.replace 创建新实例并覆盖指定字段；未替换的字段值继续复用，因此它不等同于 deepcopy。

**运行前先观察：**新实例改了哪些字段，哪些可变字段仍与原实例共享？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

这一主例沿用先前的业务场景，更新为 Python 3.12 的类型写法；变化以类型表达为主，创建与调用关系保持一致。

```python
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
```

运行输出：

```text
Original: GraphicElement(shape='circle', color='red', metadata={'layer': '1'})
Cloned:   GraphicElement(shape='circle', color='blue', metadata={'layer': '1'})
```

## 4. 使用边界

复制的深浅必须按字段判断；独立修改嵌套列表或字典前，需要决定是否深拷贝。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Prototype - Python 3.10+ Example: Dataclass Cloning & dataclasses.replace
"""
from dataclasses import dataclass, field, replace


@dataclass
class GraphicElement:
    shape: str
    color: str
    metadata: dict[str, str] = field(default_factory=dict)

    def clone(self, **overrides) -> "GraphicElement":
        return replace(self, **overrides)


if __name__ == "__main__":
    proto = GraphicElement(shape="circle", color="red", metadata={"layer": "1"})
    clone1 = proto.clone(color="blue")
    print(f"Original: {proto}")
    print(f"Cloned:   {clone1}")
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Prototype - Conceptual Example (Classic GoF)
"""
import copy
from typing import Any


class SelfReferencingEntity:
    def __init__(self) -> None:
        self.parent: Any = None

    def set_parent(self, parent: Any) -> None:
        self.parent = parent


class SomeComponent:
    def __init__(self, some_int: int, some_list_of_objects: list[Any], some_circular_ref: SelfReferencingEntity) -> None:
        self.some_int = some_int
        self.some_list_of_objects = some_list_of_objects
        self.some_circular_ref = some_circular_ref

    def __copy__(self) -> "SomeComponent":
        some_list_of_objects = copy.copy(self.some_list_of_objects)
        some_circular_ref = copy.copy(self.some_circular_ref)

        new = self.__class__(
            self.some_int, some_list_of_objects, some_circular_ref
        )
        new.__dict__.update(self.__dict__)
        return new

    def __deepcopy__(self, memo: dict | None = None) -> "SomeComponent":
        if memo is None:
            memo = {}

        some_list_of_objects = copy.deepcopy(self.some_list_of_objects, memo)
        some_circular_ref = copy.deepcopy(self.some_circular_ref, memo)

        new = self.__class__(
            self.some_int, some_list_of_objects, some_circular_ref
        )
        new.__dict__ = copy.deepcopy(self.__dict__, memo)
        return new


if __name__ == "__main__":
    list_of_objects = [1, {1, 2, 3}, [1, 2, 3]]
    circular_ref = SelfReferencingEntity()
    component = SomeComponent(23, list_of_objects, circular_ref)
    circular_ref.set_parent(component)

    shallow_copied_component = copy.copy(component)
    deep_copied_component = copy.deepcopy(component)
    print("Prototype components cloned successfully.")
```

</details>

<details>
<summary>本地项目的另一份 Python 3.12 原例</summary>

这份原例使用另一业务场景，作为可选参考；上方主例继续沿用已经讨论的对象与接口。

```python
"""
Prototype - Python 3.12+ Example: typing.Self Type-Safe Cloning
"""
from dataclasses import dataclass, replace
from typing import Self

type Properties = dict[str, str | int]


@dataclass(frozen=True)
class DocumentTemplate:
    title: str
    content: str
    properties: Properties

    def clone_with(self, **changes) -> Self:
        return replace(self, **changes)


if __name__ == "__main__":
    base_doc = DocumentTemplate(
        title="Report Template",
        content="Standard body text",
        properties={"version": 1, "status": "draft"},
    )
    custom_doc = base_doc.clone_with(title="Q4 Financial Report")
    print(f"Base: {base_doc.title}")
    print(f"Copy: {custom_doc.title}")
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 需要复制一些对象，同时又希望代码独立于这些对象的所属类时
- 如果子类的区别仅在于其对象的初始化方式，希望通过克隆预设原型避免子类激增时

### 收益

- 克隆预生成原型，避免重复繁重的初始化逻辑
- 更方便地生成复杂对象
- 可以用继承以外的方式来处理复杂对象的不同配置

### 代价

- 克隆包含循环引用的复杂对象可能会非常棘手

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / prototype](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/creational/prototype.py)，快照 `42e623b8f6d9`。

本站保留已讨论的业务场景，迁移为 Python 3.12 的类型表达。工厂主例继续使用具名函数；抽象工厂使用泛型 Protocol，Builder 与 Prototype 使用 Self。对应的两份原例保留在本页对照区。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
