---
title: "工厂方法 · Factory Method"
description: "把创建对象的选择放到一个入口里。"
weight: 10
hideMeta: true
ShowToc: true
---

[总览](../../) / [创建型](../)

## 1. 要解决什么问题

**把创建对象的选择放到一个入口里。**

直接在代码中使用具体类的构造函数会导致核心业务逻辑与具体类型强耦合，当需要新增产品类型或调整创建逻辑时必须修改现有业务代码。

## 2. 在 Python 中怎样表达

先看返回产品的工厂函数，以及接收工厂函数的调用方。对象仍然是类的实例；这里简化的是创建者层级。

**运行前先观察：**切换传入的工厂后，同一个调用方得到哪一种按钮？

## 3. Python 3.10+ 完整示例

复制下面代码保存为 `.py` 文件，在 Python 3.10 或更高版本中运行。示例只使用标准库。

```python
"""
Factory Method - Python 3.10+ Example: Registry & Match-Case Factory
"""
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Button:
    label: str
    action: str

    def render(self) -> str:
        return f"[{self.label} -> {self.action}]"


def create_button(dialog_type: str) -> Button:
    match dialog_type:
        case "windows":
            return Button(label="OK", action="windows_click")
        case "web":
            return Button(label="Submit", action="http_post")
        case "mobile":
            return Button(label="Tap", action="touch_event")
        case _:
            raise ValueError(f"Unknown dialog type: {dialog_type}")


class Dialog:
    def __init__(self, factory: Callable[[], Button] | None = None) -> None:
        self.factory = factory or (lambda: create_button("web"))

    def render_window(self) -> str:
        # 调用传入的工厂，创建当前窗口要使用的按钮。
        button = self.factory()
        return f"Dialog rendering: {button.render()}"


if __name__ == "__main__":
    win_dialog = Dialog(lambda: create_button("windows"))
    print(win_dialog.render_window())
    web_dialog = Dialog()
    print(web_dialog.render_window())
```

运行输出：

```text
Dialog rendering: [OK -> windows_click]
Dialog rendering: [Submit -> http_post]
```

### 3.1 为什么 `factory()` 可以直接调用？ {#factory-callable}

这里先沿用你已经指出的 `match` 分支，补上一个关系：**函数也可以作为值保存到变量或对象属性中，以后再调用。** `factory` 只是这个属性的名字，没有特殊语法。

主例子里的三个分支都执行 `Button(...)`：创建的是**同一个 `Button` 类的不同实例**，只是字段不同，并没有分别定义 WindowsButton、WebButton 和 MobileButton。

#### 先把 lambda 展开成普通 def

下面是对主例子这一行的等价展开片段，复用上方完整示例中的 `Button`、`create_button` 和 `Dialog`：

```python
# 原写法：把一个无参数函数传给 Dialog，此刻还不创建按钮。
win_dialog = Dialog(lambda: create_button("windows"))
```

可以改写为：

```python
def make_windows_button() -> Button:
    # 调用这个函数时，才把固定的 "windows" 交给 create_button。
    return create_button("windows")


win_dialog = Dialog(make_windows_button)  # 传入函数本身，这里没有调用它。
```

`lambda: create_button("windows")` 创建了一个不接收参数的函数。它的函数体等到这个函数被调用时才执行；固定的 `"windows"` 已经写在函数体中。

#### `Callable[[], Button]` 描述了什么？

`Callable` 的常见形式是 `Callable[[参数类型, ...], 返回类型]`。

| 注解的一部分 | 本例的意思 |
| --- | --- |
| `Callable` | 这是一个可以被调用的值，本例中就是函数 |
| `[]` | 调用时不需要传入参数 |
| `Button` | 调用后返回一个 `Button` 实例 |
| `\| None = None` | 也允许不传工厂；默认值为 `None`，构造函数随后选择默认的 Web 工厂 |

`[]` 描述的是参数列表，不表示这个函数返回列表。这个类型注解也不会自动制造一个函数；真正的函数对象来自传入的 `lambda` 或 `def`。

注意下面两个函数的签名不同：

| 函数 | 怎样调用 | 对应类型 |
| --- | --- | --- |
| `create_button` | `create_button("windows")` | `Callable[[str], Button]` |
| `make_windows_button` | `make_windows_button()` | `Callable[[], Button]` |

因此，本例不能直接把需要参数的 `create_button` 当成无参数工厂使用。`lambda` 或上面展开的 `def` 把具体类别提前固定，留下一个无参数入口。

#### 从传入函数跟到 `render_window`

构造函数保存函数对象：

```python
self.factory = factory  # 在传入普通函数的这条路径中，保存的就是那个函数。
```

之后，方法里的两行分两步执行：

```python
button = self.factory()  # 调用保存的函数，拿到它返回的 Button 实例。
return f"Dialog rendering: {button.render()}"  # 调用该实例的方法，拼出窗口描述字符串。
```

本次调用沿着下面这条路径推进：

1. `Dialog(make_windows_button)` 保存函数；此时还没有执行 `make_windows_button`。
2. `win_dialog.render_window()` 开始执行窗口的处理流程。
3. `self.factory()` 调用保存的 `make_windows_button`。
4. 函数内部执行 `create_button("windows")`，得到 `Button(label="OK", action="windows_click")`。
5. `button.render()` 得到字符串 `[OK -> windows_click]`。
6. `render_window()` 最后返回 `Dialog rendering: [OK -> windows_click]`。

这里的 `render()` 只是读取字段并返回字符串；不会绘制真实窗口，也不会执行 `action` 中写着的动作。

#### 为什么保存函数，而不是立刻保存一个按钮？

直接保存一个已经创建的按钮当然也能满足一些需求。本例选择保存创建函数，是让 `Dialog` **在需要按钮时再调用创建入口**，而调用方决定这个入口怎样创建按钮。这样 `render_window` 只需要知道“调用工厂会得到一个有 `render` 方法的按钮”。

| 表达式 | 得到或传递的是什么 |
| --- | --- |
| `make_windows_button` | 函数对象，可以留到以后调用 |
| `make_windows_button()` | 立即调用后得到的 `Button` 实例 |
| `Dialog(make_windows_button)` | 符合本例接口，把函数交给 Dialog 保存 |
| `Dialog(make_windows_button())` | 把按钮实例传给期望函数的位置；之后执行 `self.factory()` 时会因该实例不可调用而报错 |

另一个可观察的结果是：本例每次调用 `render_window()` 都会再次调用工厂；由于这个工厂每次执行 `Button(...)`，就会重新创建按钮。**是否复用对象取决于工厂实现，Callable 本身不负责缓存。**

可以先检查一个区别：`Dialog(make_windows_button)` 执行完以后，创建按钮的工作已经发生了吗？判断依据是调用括号究竟加在 `Dialog` 后，还是 `make_windows_button` 后。

## 4. 使用边界

只有少数固定类型时，普通函数和清楚的分支已经足够。类工厂适合创建过程需要保存状态或通过继承扩展的场景。

## 5. 按需对照

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Factory Method - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class Product(ABC):
    @abstractmethod
    def operation(self) -> str:
        pass


class ConcreteProduct1(Product):
    def operation(self) -> str:
        return "{Result of ConcreteProduct1}"


class ConcreteProduct2(Product):
    def operation(self) -> str:
        return "{Result of ConcreteProduct2}"


class Creator(ABC):
    @abstractmethod
    def factory_method(self) -> Product:
        pass

    def some_operation(self) -> str:
        product = self.factory_method()
        return f"Creator: The same creator's code has just worked with {product.operation()}"


class ConcreteCreator1(Creator):
    def factory_method(self) -> Product:
        return ConcreteProduct1()


class ConcreteCreator2(Creator):
    def factory_method(self) -> Product:
        return ConcreteProduct2()


def client_code(creator: Creator) -> str:
    return creator.some_operation()


if __name__ == "__main__":
    print(client_code(ConcreteCreator1()))
    print(client_code(ConcreteCreator2()))
```

</details>

<details>
<summary>Python 3.12+ 示例</summary>

请在 Python 3.12 或更高版本运行。重点看类型表达与组合方式的变化；不要只按版本高低选择写法。

```python
"""
Factory Method - Python 3.12+ Example: PEP 695 Generic Factory & Type Alias
"""
from collections.abc import Callable
from dataclasses import dataclass
from typing import override

type Factory[T] = Callable[[], T]


@dataclass
class Button:
    label: str

    def render(self) -> str:
        return f"Button({self.label})"


class HTMLButton(Button):
    @override
    def render(self) -> str:
        return f"<button>{self.label}</button>"


class Dialog[T: Button]:
    def __init__(self, factory: Factory[T]) -> None:
        self._factory = factory

    def render(self) -> str:
        btn = self._factory()
        return f"Dialog container with: {btn.render()}"


if __name__ == "__main__":
    html_dialog = Dialog(lambda: HTMLButton("Submit"))
    print(html_dialog.render())
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 在编写代码的过程中，如果无法预知对象确切的类别及其依赖关系时
- 希望复用现有对象来节省系统资源，而不是每次都重新创建对象时
- 希望为库或框架的用户提供扩展其内部组件语言接口的方式时

### 收益

- 避免创建者和具体产品之间的紧密耦合
- 单一职责原则：可以将产品创建代码独立到单一位置
- 开闭原则：无需更改现有客户端代码即可引入新的产品类型

### 代价

- 应用工厂方法模式需要引入许多新的子类，代码可能会因此变得更复杂

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / factory-method](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/creational/factory_method.py)，快照 `42e623b8f6d9`。

本站补充了中文观察点、关键行注释、运行输出与使用边界；主例子保留原接口和行为。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
