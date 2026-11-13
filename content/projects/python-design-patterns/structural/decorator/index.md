---
title: "装饰器 · Decorator"
description: "在现有行为外面逐层添加功能。"
weight: 40
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [结构型](../)

## 1. 要解决什么问题

**在现有行为外面逐层添加功能。**

如果采用继承来扩展对象行为，类继承是在编译时静态绑定的，子类无法在运行时动态添加或移除功能，且不同特性的任意排列组合会导致子类数量爆炸。

## 2. 在 Python 中怎样表达

logged 接收函数并返回 wrapper，functools.wraps 保留原函数的元信息。def logged[**P, R] 用 Python 3.12 的类型参数保留参数列表 P 和返回类型 R。

**运行前先观察：**包装函数在调用原函数之前和之后分别做了什么？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Decorator - Python 3.12+ Example: PEP 695 Generic Decorator with ParamSpec
"""
from collections.abc import Callable
import functools


def logged[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling: {func.__name__}")
        # 保持原参数调用被包装函数，并保存它的返回结果。
        res = func(*args, **kwargs)
        print(f"Finished: {func.__name__}")
        return res
    return wrapper


@logged
def greet(name: str) -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    msg = greet("World")
    print(msg)
```

运行输出：

```text
Calling: greet
Finished: greet
Hello, World!
```

## 4. 使用边界

GoF 装饰模式是一种组合思路，Python 的 @ 是应用装饰器的语法，两者相关但不完全等同；叠加顺序会影响行为。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Decorator - Python 3.10+ Example: Pythonic Function & Method Decorators
"""
from collections.abc import Callable
import functools
import time
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def timer(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        print(f"[{func.__name__}] executed in {duration:.6f}s")
        return result
    return wrapper


def retry(times: int = 3):
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_err = None
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
            raise RuntimeError(f"Failed after {times} attempts: {last_err}")
        return wrapper
    return decorator


@timer
@retry(times=2)
def calculate_metrics(count: int) -> int:
    return sum(i * i for i in range(count))


if __name__ == "__main__":
    res = calculate_metrics(1000)
    print(f"Result: {res}")
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Decorator - Conceptual Example (Classic GoF)
"""


class Component:
    def operation(self) -> str:
        return "ConcreteComponent"


class Decorator(Component):
    def __init__(self, component: Component) -> None:
        self._component = component

    @property
    def component(self) -> Component:
        return self._component

    def operation(self) -> str:
        return self._component.operation()


class ConcreteDecoratorA(Decorator):
    def operation(self) -> str:
        return f"ConcreteDecoratorA({self.component.operation()})"


class ConcreteDecoratorB(Decorator):
    def operation(self) -> str:
        return f"ConcreteDecoratorB({self.component.operation()})"


def client_code(component: Component) -> str:
    return f"RESULT: {component.operation()}"


if __name__ == "__main__":
    simple = Component()
    print("Client: I've got a simple component:")
    print(client_code(simple))

    decorator1 = ConcreteDecoratorA(simple)
    decorator2 = ConcreteDecoratorB(decorator1)
    print("\nClient: Now I've got a decorated component:")
    print(client_code(decorator2))
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 在无需修改代码的情况下即可使用对象，且希望在运行时为对象新增额外行为时
- 如果用继承来扩展对象行为的方案难以实现或者根本不可行时

### 收益

- 无需创建新子类即可扩展对象的行为
- 可以在运行时添加或删除职责
- 用多个装饰封装对象来组合几种行为
- 单一职责原则：可以将大类中各个不同职责拆分为小类

### 代价

- 在装饰栈中删除特定装饰器比较困难
- 代码的外观会充满大量小类，配置和调试排查调用栈相对复杂

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / decorator](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/structural/decorator.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
