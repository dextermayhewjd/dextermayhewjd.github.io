---
title: "抽象工厂 · Abstract Factory"
description: "一次选择一整套相互匹配的对象。"
weight: 20
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [创建型](../)

## 1. 要解决什么问题

**一次选择一整套相互匹配的对象。**

当代码需要与多个不同系列的相关产品协同工作，但你不希望代码依赖于这些产品的具体类时，硬编码构造会导致系列对象不匹配且难以替换整个产品族。

## 2. 在 Python 中怎样表达

GUIFactory[B, C] 用 Python 3.12 的类型参数描述工厂返回的两种产品，具体工厂仍负责创建暗色或亮色的按钮和复选框。Protocol 说明接口，不负责创建对象。

**运行前先观察：**更换主题时，按钮和复选框是否一起变化？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

这一主例沿用先前的业务场景，更新为 Python 3.12 的类型写法；变化以类型表达为主，创建与调用关系保持一致。

```python
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
```

运行输出：

```text
[Dark Button] [Dark Checkbox]
```

### 3.1 和上一节的工厂究竟有什么不同？ {#factory-comparison}

对比[上一节的 Python 示例](/projects/python-design-patterns/creational/factory-method/)：**上节替换“创建按钮”的入口；本节替换“创建一套按钮和复选框”的工厂。**

| 产品种类 | 暗色产品族：DarkThemeFactory | 亮色产品族：LightThemeFactory |
| --- | --- | --- |
| 按钮 Button | 创建暗色按钮 | 创建亮色按钮 |
| 复选框 Checkbox | 创建暗色复选框 | 创建亮色复选框 |

**行是产品种类，列是一套配套方案。** `get_factory("dark")` 选中暗色这一列，再通过同一个工厂的两个创建方法，分别获得 Button 和 Checkbox 实例。换成 `"light"`，使用方的两个方法调用不变。

判断是否需要抽象工厂，看的是**多种相关产品是否需要随同一套方案一起切换**。共有 `theme` 字段只是本例的表达方式；普通工厂也可以按主题创建按钮。

**一句话：抽象工厂把一组配套产品的创建规则组织在一起，让调用方可以整体更换这套创建方案。**

## 4. 使用边界

只有一个产品时，通常不需要抽象工厂；当多个产品必须配套时，这层组织才有意义。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Abstract Factory - Python 3.10+ Example: Protocols & Dataclass Product Families
"""
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


class GUIFactory(Protocol):
    def create_button(self) -> Button: ...
    def create_checkbox(self) -> Checkbox: ...


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


def get_factory(theme: str) -> GUIFactory:
    match theme:
        case "dark":
            return DarkThemeFactory()
        case "light":
            return LightThemeFactory()
        case _:
            raise ValueError(f"Unknown theme: {theme}")


if __name__ == "__main__":
    factory = get_factory("dark")
    print(factory.create_button().render(), factory.create_checkbox().render())
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Abstract Factory - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class AbstractProductA(ABC):
    @abstractmethod
    def useful_function_a(self) -> str:
        pass


class ConcreteProductA1(AbstractProductA):
    def useful_function_a(self) -> str:
        return "The result of the product A1."


class ConcreteProductA2(AbstractProductA):
    def useful_function_a(self) -> str:
        return "The result of the product A2."


class AbstractProductB(ABC):
    @abstractmethod
    def useful_function_b(self) -> str:
        pass

    @abstractmethod
    def another_useful_function_b(self, collaborator: AbstractProductA) -> str:
        pass


class ConcreteProductB1(AbstractProductB):
    def useful_function_b(self) -> str:
        return "The result of the product B1."

    def another_useful_function_b(self, collaborator: AbstractProductA) -> str:
        result = collaborator.useful_function_a()
        return f"The result of the B1 collaborating with the ({result})"


class ConcreteProductB2(AbstractProductB):
    def useful_function_b(self) -> str:
        return "The result of the product B2."

    def another_useful_function_b(self, collaborator: AbstractProductA) -> str:
        result = collaborator.useful_function_a()
        return f"The result of the B2 collaborating with the ({result})"


class AbstractFactory(ABC):
    @abstractmethod
    def create_product_a(self) -> AbstractProductA:
        pass

    @abstractmethod
    def create_product_b(self) -> AbstractProductB:
        pass


class ConcreteFactory1(AbstractFactory):
    def create_product_a(self) -> AbstractProductA:
        return ConcreteProductA1()

    def create_product_b(self) -> AbstractProductB:
        return ConcreteProductB1()


class ConcreteFactory2(AbstractFactory):
    def create_product_a(self) -> AbstractProductA:
        return ConcreteProductA2()

    def create_product_b(self) -> AbstractProductB:
        return ConcreteProductB2()


def client_code(factory: AbstractFactory) -> str:
    product_a = factory.create_product_a()
    product_b = factory.create_product_b()
    return f"{product_b.useful_function_b()} | {product_b.another_useful_function_b(product_a)}"


if __name__ == "__main__":
    print(client_code(ConcreteFactory1()))
    print(client_code(ConcreteFactory2()))
```

</details>

<details>
<summary>本地项目的另一份 Python 3.12 原例</summary>

这份原例使用另一业务场景，作为可选参考；上方主例继续沿用已经讨论的对象与接口。

```python
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
    return factory.create_button(), factory.create_checkbox()


if __name__ == "__main__":
    b, c = build_ui(StandardFactory())
    print(f"UI Created: {b}, {c}")
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 如果代码需要与多个不同系列的相关产品交互，但是由于无法预知对象确切类别而无法直接依赖具体产品时
- 如果有一个基于一组工厂方法实现的类，并且其职责变得过重时

### 收益

- 确保同一工厂产出的产品相互兼容
- 避免客户端和具体产品之间的紧密耦合
- 单一职责原则：产品生成代码抽取到单一接口
- 开闭原则：引入新产品族时无需修改客户端代码

### 代价

- 在引入新产品类型（增加新的产品等级结构）时，需要修改抽象工厂接口及其所有子类实现

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / abstract-factory](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/creational/abstract_factory.py)，快照 `42e623b8f6d9`。

本站保留已讨论的业务场景，迁移为 Python 3.12 的类型表达。工厂主例继续使用具名函数；抽象工厂使用泛型 Protocol，Builder 与 Prototype 使用 Self。对应的两份原例保留在本页对照区。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
