---
title: "工厂方法 · Factory Method"
description: "把创建对象的选择放到一个入口里。"
weight: 10
hideMeta: true
ShowToc: false
pythonVersion: "3.12"
---

[总览](../../) / [创建型](../)

## 1. 本页只先弄清一件事

**运行版本：Python 3.12。**

**调用方提供创建按钮的函数，Dialog 保存它，需要按钮时调用它，再使用返回的按钮。**

这里的工厂是承担“创建对象”职责的函数。`lambda` 是写函数的一种语法，`Callable` 是描述可调用接口的类型注解。这三者属于不同层次，可以分别复习。

## 2. 主例：先用具名函数走通 {#create-button-path}

这是原示例的 **Python 3.12 教学展开**：保留 `Button`、`create_button`、`Dialog` 和 `render_window`，用具名函数提供工厂，以 `type` 声明工厂类型别名。主线只展示显式传入工厂的路径；默认工厂分支保留在文末的[历史原例](/projects/python-design-patterns/creational/factory-method/#original-python-example)中。

```python
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Button:
    label: str
    action: str

    def render(self) -> str:
        return f"[{self.label} -> {self.action}]"


type ButtonFactory = Callable[[], Button]


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


def make_windows_button() -> Button:
    return create_button("windows")  # 调用本函数时才创建 Windows 配置的按钮。


def make_web_button() -> Button:
    return create_button("web")


class Dialog:
    def __init__(self, factory: ButtonFactory) -> None:
        self.factory = factory  # 保存函数，此处还没有调用它。

    def render_window(self) -> str:
        button = self.factory()  # 现在调用保存的函数，接收 Button 实例。
        return f"Dialog rendering: {button.render()}"


if __name__ == "__main__":
    win_dialog = Dialog(make_windows_button)  # 传函数本身。
    print(win_dialog.render_window())
    web_dialog = Dialog(make_web_button)
    print(web_dialog.render_window())
```

输出：

```text
Dialog rendering: [OK -> windows_click]
Dialog rendering: [Submit -> http_post]
```

**本例范围：**三种配置都使用同一个 `Button` 类。`render()` 只返回字符串，不绘制真实窗口，也不执行 `action` 里的动作。

## 3. 从卡住的地方进入

读过主例后，再用下面的表定位疑问。不必把每块都展开；若展开后发现前置关系还不清楚，再沿链接回查。

| 当前疑问 | 对应知识块 | 读完要能判断 |
| --- | --- | --- |
| `make_windows_button` 和 `make_windows_button()` 有什么区别？ | [A · 函数对象与函数调用](#function-value) | 当前交出去的是函数还是按钮 |
| 函数放进 `self.factory` 后，为什么还能加括号？ | [B · 传入、保存与调用函数](#function-handoff) | 调用究竟发生在哪一行 |
| 为什么专门留一个 factory，不能直接创建按钮吗？ | [C · 工厂职责与使用职责](#factory-role) | 谁决定创建方式，谁使用结果 |
| `Callable[[], Button]` 的括号怎么读？ | [D · 可调用对象的类型注解](#callable-annotation) | 参数列表与返回类型分别是什么 |
| `lambda: create_button("windows")` 到底是什么？ | [E · 用 lambda 写短函数](#lambda-expression) | 它与具名函数的对应关系 |

主线依赖是 **A → B → C**。D 为这条主线补上类型说明，E 为已经认识的函数提供更短的写法；D 和 E 不必成为理解工厂职责的入口门槛。

### 3.1 知识点：按需展开 {#factory-callable}

每块只解释一个主要关系。块内代码片段复用上面的主例；类型注解块还会单独注明新增的导入。

<details id="function-value">
<summary>A · 函数对象与调用：f 和 f() 分别是什么？</summary>

**前置：**认识函数定义和返回值。

**一句结论：**函数名可以指向一个函数对象；给它加调用括号，才执行函数体并取得结果。

```python
saved = make_windows_button  # saved 与原名字指向同一个函数，没有创建按钮。
button = saved()  # 调用该函数，现在才创建按钮。
```

这两行的结果不同：`saved` 是函数，`button` 是这个函数返回的按钮实例。把函数赋给新变量，不会改变函数本身。

**检查自己：**执行第一行以后，有没有进入 `create_button`？若能说明调用发生在哪一行，就可以回到主线。

</details>

<details id="function-handoff">
<summary>B · 函数的交接：为什么 self.factory() 能调用？</summary>

**前置：**[A · 函数对象与调用](#function-value)。

**一句结论：**函数对象可以作为参数传入，也可以保存为对象属性；通过这个属性仍然能调用原函数。

```python
dialog = Dialog(make_windows_button)  # 把函数传给 __init__ 的 factory 参数。
print(dialog.factory is make_windows_button)  # True：属性里保存的就是该函数。
button = dialog.factory()  # 通过属性取出函数并调用，得到按钮。
```

`factory` 不是 Python 的特殊关键字。这里的 `self.factory()` 能执行，是因为保存到该属性中的值可以调用；换一个属性名字也一样。

`Dialog(make_windows_button())` 则会先创建按钮，再把按钮实例传给 `Dialog`。本例的按钮实例不能直接加括号调用，所以后续的 `self.factory()` 会报错。

**检查自己：**`Dialog(make_windows_button)` 和 `dialog.factory()` 两行，哪一行创建 Dialog，哪一行创建 Button？

</details>

<details id="factory-role">
<summary>C · 工厂职责：为什么把“创建按钮”交给外部函数？</summary>

**前置：**[B · 函数的交接](#function-handoff)。

**一句结论：**调用方提供创建规则，`render_window` 使用创建结果；两处可以分别变化。

| 位置 | 本例承担的职责 |
| --- | --- |
| `create_button(dialog_type)` | 按类别选择字段并创建 Button |
| `make_windows_button()` | 固定本次使用的类别，提供无参数创建入口 |
| `Dialog(make_windows_button)` | 把选好的创建入口交给窗口 |
| `render_window()` | 调用创建入口，再使用返回的按钮 |

直接在 `render_window` 中写 `Button(...)` 或 `create_button("windows")` 也能工作。这个例子增加的能力是：外部可以为不同窗口提供不同的创建函数，而窗口的使用流程保持一致。

这里的 `match` 负责选择，传入函数负责让使用者接受外部的创建规则。它们是两件配合的事。本例更接近参数化工厂与函数注入；经典 GoF 工厂方法通过子类重写创建方法，组织方式另见文末的[传统写法](/projects/python-design-patterns/creational/factory-method/#classic-example)。

本例每次调用 `render_window()` 都调用一次工厂，每次都会新建按钮。是否缓存或复用对象，由工厂实现决定。

**检查自己：**如果下一次想让窗口使用 Web 配置，需要改 `render_window`，还是更换传入的创建函数？

</details>

<details id="callable-annotation">
<summary>D · Callable：int、str、Any、[] 和 ... 有什么区别？</summary>

**前置：**[A · 函数对象与调用](#function-value)；了解类型注解用于描述接口。

**一句结论：**`Callable[[], Button]` 描述“调用时不传参数，返回 Button 实例”的可调用对象。

```python
from collections.abc import Callable

factory: Callable[[], Button] = make_windows_button  # 给已有的函数值补上接口说明。
button = factory()  # 零个参数；返回值是 Button 实例。
```

| 函数 | 调用方式 | 类型说明 |
| --- | --- | --- |
| `create_button` | `create_button("windows")` | `Callable[[str], Button]` |
| `make_windows_button` | `make_windows_button()` | `Callable[[], Button]` |

第一个方括号列表描述参数，最后的 `Button` 描述返回类型。空的 `[]` 表示零个参数，不表示返回空列表。注解不会创建函数，也不会让原本不能调用的对象变得可调用。

#### Python 3.12 的 type 别名

主例用 `type ButtonFactory = Callable[[], Button]` 给这个接口起一个名字。因此，参数上的 `factory: ButtonFactory` 仍然表示“接收一个无参数、返回 Button 的可调用对象”；`type` 不会创建按钮，也不会调用工厂。

#### 指定类型、任意类型与零个参数

| 类型注解 | 怎样描述参数 | 怎样描述返回值 |
| --- | --- | --- |
| `Callable[[int], Button]` | 一个参数，类型为整数 `int` | `Button` 实例 |
| `Callable[[str], Button]` | 一个参数，类型为字符串 `str` | `Button` 实例 |
| `Callable[[int, str], Button]` | 两个参数，依次为整数、字符串 | `Button` 实例 |
| `Callable[[Any], Button]` | 一个参数，此处不约束其具体类型 | `Button` 实例 |
| `Callable[[], Button]` | 零个参数 | `Button` 实例 |
| `Callable[..., Button]` | 这份注解不描述具体参数列表 | `Button` 实例 |
| `Callable[[int], Any]` | 一个整数参数 | 此处不约束返回值的具体类型 |

`int`、`str` 写明具体类型；`Any` 表示此处不做具体类型约束，写法区分大小写，需要导入：

```python
from typing import Any
```

注意区分这三个问题：

- **参数是什么类型？** 用 `int`、`str` 或 `Any` 等表示。
- **参数有几个？** `[Any]` 仍表示一个参数，`[int, str]` 表示两个，`[]` 表示零个。
- **是否描述参数列表？** `...` 表示这份注解没有指定参数列表；它不改变函数本身，实际调用仍要遵守函数定义。

因此，`Any` 不等于“没有参数”，也不等于“任意数量的参数”。类型注解不会自动把传入值转成整数或字符串，也不保证运行时会检查类型。

原代码中的 `Callable[[], Button] | None = None` 另外允许省略工厂，然后走默认工厂分支；它属于参数默认值的问题，可以在主线清楚后再看。

**检查自己：**`Callable[[Any], Button]` 和 `Callable[[], Button]`，哪一个描述的是需要传入一个参数的函数？如果接收两个整数、返回字符串，完整注解又该怎样写？

</details>

<details id="lambda-expression">
<summary>E · lambda：先看无参数、一个参数、多个参数，再回到工厂</summary>

**前置：**[A · 函数对象与调用](#function-value)和[B · 函数的交接](#function-handoff)。

**一句结论：**`lambda` 创建一个短函数；它可以不接收参数，也可以接收一个或多个参数，调用时返回表达式的结果。

#### E.1 先认清三种参数形式

基本形式是 `lambda 参数: 返回值表达式`。先看冒号前面，再看冒号后面：

| 参数形式 | 函数写法 | 调用例子与结果 |
| --- | --- | --- |
| 无参数 | `f = lambda: 10` | `f()` 返回 `10` |
| 一个参数 | `f = lambda x: x * 2` | `f(3)` 返回 `6` |
| 多个参数 | `f = lambda x, y: x + y` | `f(2, 3)` 返回 `5` |

这三行都先创建函数并交给 `f`，之后调用 `f(...)` 才计算冒号后面的表达式。参数个数由冒号前面的定义决定；`lambda` 并不固定为无参数函数。

#### E.2 无参数：把一次创建留到以后执行

复用本页的 `create_button`：

```python
factory = lambda: create_button("windows")  # 创建函数，尚未创建按钮。
button = factory()  # 现在调用函数，创建并返回 Button 实例。
print(button.render())
```

输出：

```text
[OK -> windows_click]
```

这个函数不需要调用方再传参数，因为 `"windows"` 已写在函数体里。这里借助的是“保存函数，稍后调用”的能力。

#### E.3 一个参数：告诉排序函数按什么取值

商品表示为 `(名称, 价格)`，其中 `item[1]` 是价格：

```python
items = [("苹果", 5), ("香蕉", 3)]

result = sorted(items, key=lambda item: item[1])  # 每次接收一个商品，返回其价格。
print(result)
```

输出：

```text
[('香蕉', 3), ('苹果', 5)]
```

这里由 `sorted` 调用这个函数，把商品逐个交给它，用返回的价格作为排序依据。**遍历和排序由 `sorted` 负责，`lambda` 只负责从一个商品中取出价格。**

#### E.4 多个参数：计算并返回结果

```python
add = lambda x, y: x + y  # 创建一个接收两个参数的函数。
print(add(2, 3))  # 调用时把 2、3 分别交给 x、y，返回相加结果。
```

输出：

```text
5
```

这个例子可以用具名函数表达：

```python
def add(x, y):
    return x + y
```

#### E.5 共同规则，再接回工厂

1. **先产生函数对象。** 写出 `lambda ...: ...`，得到的是一个函数，可以赋给变量，也可以作为参数传递。
2. **调用时才计算结果。** 冒号前面写参数，冒号后面是一个表达式；调用函数时，表达式的结果自动成为返回值，不写 `return`。
3. **函数体只能是一个表达式。** 多步骤逻辑、需要起清楚名字或重复使用的逻辑，通常写成 `def` 更便于阅读和调试。

回到原例的 `Dialog(lambda: create_button("windows"))`：它只是把 E.2 的无参数函数直接交给 `Dialog`，之后由 `render_window` 中的 `self.factory()` 调用。理解工厂职责不要求使用 `lambda`，本页主例的具名函数同样可以完成工作。

这三种参数形式是基本例子，并不是所有签名规则的清单；默认参数等写法可以在需要时再补。

**检查自己：**工厂例子由谁调用保存的函数，排序例子又由谁调用传入的函数？两处的 `lambda` 各接收几个参数？

</details>

## 4. 用一句话总结 {#factory-in-one-sentence}

**工厂把“对象怎么创建”封装在创建入口里，让使用者通过这个入口取得对象，再完成自己的工作。**

对应本例：调用方传入 `make_windows_button` → Dialog 保存函数 → `render_window()` 调用它 → `create_button("windows")` 创建 Button → 窗口调用 `button.render()` 取得字符串。

如果还卡住，回到上面对应的问题块即可。这里没有把“看完了所有折叠”当作已经理解的标准；可以先把当前缺的一处关系补清楚。

## 5. 按需对照与来源

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

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
        button = self.factory()
        return f"Dialog rendering: {button.render()}"


if __name__ == "__main__":
    win_dialog = Dialog(lambda: create_button("windows"))
    print(win_dialog.render_window())
    web_dialog = Dialog()
    print(web_dialog.render_window())
```

</details>

<details id="classic-example">
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
<summary>本地项目的另一份 Python 3.12 原例</summary>

这份原例使用另一业务场景，作为可选参考；上方主例继续沿用已经讨论的对象与接口。

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

本站保留已讨论的业务场景，迁移为 Python 3.12 的类型表达。工厂主例继续使用具名函数；抽象工厂使用泛型 Protocol，Builder 与 Prototype 使用 Self。对应的两份原例保留在本页对照区。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
