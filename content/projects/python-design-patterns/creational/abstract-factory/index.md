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

Factory[B, C] 声明两种创建方法，StandardFactory 分别创建 Button 和 Checkbox；build_ui 使用同一工厂取得两者，并返回 ComponentPair[B, C]。

**运行前先观察：**build_ui 接收的是产品还是工厂，返回的元组里又是什么？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

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
    # 同一个工厂分别创建两种产品，作为一个元组返回。
    return factory.create_button(), factory.create_checkbox()


if __name__ == "__main__":
    b, c = build_ui(StandardFactory())
    print(f"UI Created: {b}, {c}")
```

运行输出：

```text
UI Created: Button(label='Standard'), Checkbox(checked=True)
```

### 3.1 和上一节的工厂究竟有什么不同？ {#factory-comparison}

对比[上一节的 Python 示例](/projects/python-design-patterns/creational/factory-method/)：**上节给 Dialog 一个创建按钮的函数；本节给 build_ui 一个能创建两种产品的工厂对象。**

| 本节的对象或函数 | 创建或返回什么 |
| --- | --- |
| `StandardFactory.create_button()` | `Button(label="Standard")` |
| `StandardFactory.create_checkbox()` | `Checkbox(checked=True)` |
| `build_ui(StandardFactory())` | 通过同一工厂取得 `(Button, Checkbox)` 两个实例 |

`Factory[B, C]` 说明工厂提供两种创建方法，B、C 是返回产品的类型参数；`ComponentPair[B, C]` 表示两个产品组成的元组。

判断是否需要抽象工厂，看的是**多种相关产品是否需要采用同一套创建方案**，并不要求它们有共同字段。这个原例只有 StandardFactory，展示了统一创建产品对的接口结构；它没有实际演示两种产品族的切换，完整对照见文末传统写法。

**一句话：抽象工厂把一组配套产品的创建规则组织在一起，让调用方可以整体更换这套创建方案。**

### 3.2 看不懂类型写法时，先分开三个角色 {#abstract-factory-types}

**Factory 约定接口，StandardFactory 实现创建，build_ui 接收工厂实例并使用它。** 原来的 GUIFactory 也是 Protocol；新版增加的是类型参数，不是取消了具体工厂。

<details id="abstract-factory-roles">
<summary>A · Factory、StandardFactory 和小写 factory 分别是什么？</summary>

| 名称 | 本例中的角色 |
| --- | --- |
| `Factory[B, C]` | Protocol：约定需要提供两个创建方法，以及它们的返回类型 |
| `StandardFactory` | 具体类：方法内部执行 `Button(...)` 和 `Checkbox(...)` |
| `factory` | `build_ui` 的参数名：本次接收的是 `StandardFactory()` 实例 |

Protocol 中的方法体是 `...`，没有写具体创建步骤。真正的步骤在 StandardFactory 的方法里。

#### 先只理解 Protocol，暂时固定返回类型

下面只是拆解概念的对照片段，不替换上面的 Python 3.12 原例：

```python
class Factory(Protocol):
    def create_button(self) -> Button: ...
    def create_checkbox(self) -> Checkbox: ...
```

它是一份接口清单：能作为 Factory 使用的对象，需要提供这两个方法，分别返回 Button 和 Checkbox 实例。这里写的是返回实例的类型，不是要求方法返回类本身。

StandardFactory 没有显式继承 Factory，但它提供了相符的方法结构，因此可以满足这个 Protocol 的类型约定。这里不是运行时自动继承或自动生成方法。

**协议负责描述要求，具体工厂负责实现要求。** Protocol 并非工厂专属，也不强制每个工厂类都加一段这样的前缀。它可供类型检查器核对接口；这些注解不会自动完成创建或运行时校验。

原例中的 B、C 是再加上的泛型类型参数，用来保留具体产品类型。Protocol 可以不用泛型，泛型也可以用于普通类和函数；理解接口清单后再读 B 块即可。

</details>

<details id="abstract-product-types">
<summary>B · 为什么 B: Button、C: Checkbox 写在参数前面的方括号中？</summary>

**普通函数参数没有被搬到前面：它们仍在圆括号里。** 前面的方括号另行声明类型参数，是 Python 3.12 的泛型语法；只有需要这种泛型表达时才写，不是所有函数或工厂都必须写。

以原函数头为例：

```python
def build_ui[B: Button, C: Checkbox](factory: Factory[B, C]) -> ComponentPair[B, C]:
    ...  # 此处只展示声明结构；完整函数体见主例。
```

| 位置 | 声明什么 | 本例中的意思 |
| --- | --- | --- |
| `[B: Button, C: Checkbox]` | 两个类型参数 B、C | B 表示某种按钮类型，C 表示某种复选框类型 |
| `(factory: Factory[B, C])` | 一个普通函数参数 factory | 实际调用时传入工厂对象 |
| `-> ComponentPair[B, C]` | 返回值的类型关系 | 结果里的按钮、复选框对应前面同一组 B、C |

`B: Button` 给 B 设置类型上界：它可以是 Button，也可以是 Button 的子类。C 同理。这里没有声明名叫 B、C 的普通对象参数，也不会在运行时自动创建两个对象。

因此调用仍然是 `build_ui(StandardFactory())`，只传入一个工厂实例。类型检查器根据 StandardFactory 两个方法的返回类型，把本次调用理解为返回 Button 和 Checkbox 的组合；调用方不需要再把 B、C 作为普通参数传进去。

#### Protocol 类的方括号也是声明类型参数

```python
class Factory[B: Button, C: Checkbox](Protocol):
    def create_button(self) -> B: ...
    def create_checkbox(self) -> C: ...
```

类名后的 `[B: Button, C: Checkbox]` 同样声明两个类型参数；这里圆括号里的 `(Protocol)` 是基类，不是构造函数参数。

可以把这个接口读成：“一个能创建 B 类型按钮和 C 类型复选框的工厂。”`Factory[Button, Checkbox]` 则把两个类型位置指定为 Button、Checkbox。它是类型表达，不会创建工厂实例。

Factory 类和 build_ui 函数各自声明自己的 B、C，它们不是同一组全局变量。函数参数注解 `Factory[B, C]` 把函数里的类型参数与工厂接口的两个类型位置关联起来。

#### 方括号要区分“定义时起名字”和“使用时填类型”

| 写法 | 方括号在做什么 |
| --- | --- |
| `class Factory[B: Button, C: Checkbox](Protocol)` | 定义接口时，给两个类型位置起名 B、C，并约束其上界 |
| `Factory[Button, Checkbox]` | 使用接口时，向这两个位置填入具体类型 Button、Checkbox |
| `def build_ui[B: Button, C: Checkbox](...)` | 定义函数自己的两个类型参数 |
| 函数签名中的 `Factory[B, C]` | 使用接口时，填入当前函数的两个类型参数，把关系连起来 |

这些方括号里的内容都不是要求工厂实例拥有名为 B、C 的字段。

`Button(label="Standard")` 中的 `"Standard"` 是字段值，`Checkbox(checked=True)` 中的 `True` 也是字段值；它们不是名为 StandardButton 或 CheckedCheckbox 的新类型。

</details>

<details id="abstract-build-ui-signature">
<summary>C · 为什么输入工厂与输出元组都写 B、C？</summary>

把原签名分成三部分，它们在使用同一组函数类型参数：

| 部分 | 意思 |
| --- | --- |
| `build_ui[B: Button, C: Checkbox]` | 先起两个类型名字：B 是某种按钮类型，C 是某种复选框类型 |
| `factory: Factory[B, C]` | 输入要求：工厂的 create_button 返回 B 类型实例，create_checkbox 返回 C 类型实例 |
| `-> ComponentPair[B, C]` | 输出约定：元组第一项是同一个 B 类型，第二项是同一个 C 类型 |

**反复写 B、C，是为了保留“输入工厂能创建什么类型，输出就是什么类型”的对应关系。** 它没有要求 factory 拥有 B、C 两个属性，也没有声明额外的运行时参数。

`type ComponentPair[B, C] = tuple[B, C]` 只是给二元组类型起了别名。因此返回类型 `ComponentPair[B, C]` 可以读作 `tuple[B, C]`，它本身不会创建产品。

真正执行的是函数体这一行：

```python
return factory.create_button(), factory.create_checkbox()  # 调用两次创建方法，再组成元组。
```

本次 `build_ui(StandardFactory())` 得到 `(Button(label="Standard"), Checkbox(checked=True))`；外层的 `b, c = ...` 将两个实例分别交给 b 和 c。

对这次调用，依据 StandardFactory 的方法签名，类型检查器可以将函数的 B 理解为 Button、C 理解为 Checkbox：输入是这种工厂，输出是 `tuple[Button, Checkbox]`。实际运行仍然只传入一个 StandardFactory 实例，然后执行上面两次方法调用。

</details>

## 4. 使用边界

这个最小例子只提供 StandardFactory，展示产品对的统一创建，没有实际演示两套产品族之间的切换。完整产品族对照见传统写法。

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

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
