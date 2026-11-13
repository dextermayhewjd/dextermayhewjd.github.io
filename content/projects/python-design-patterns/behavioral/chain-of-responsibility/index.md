---
title: "责任链 · Chain of Responsibility"
description: "让请求依次经过多个可选择处理的环节。"
weight: 10
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [行为型](../)

## 1. 要解决什么问题

**让请求依次经过多个可选择处理的环节。**

当需要按特定顺序对请求执行多个过滤或处理步骤（例如顺序检查身份验证、角色权限限制、缓存、限流与数据净化），把所有逻辑塞进一个巨大的请求处理方法中会导致方法难以扩展，任何条件变动都会牵一发而动全身。

## 2. 在 Python 中怎样表达

Pipeline[Req, Res] 依次调用 Step[Req, Res] 列表，None 表示继续传递，首个非 None 结果结束处理；全部未处理时返回 fallback。

**运行前先观察：**哪个返回值表示继续传递，哪个返回值会终止处理？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Chain of Responsibility - Python 3.12+ Example: PEP 695 Generic Pipeline
"""
from collections.abc import Callable

type Step[Req, Res] = Callable[[Req], Res | None]


class Pipeline[Req, Res]:
    def __init__(self, steps: list[Step[Req, Res]]) -> None:
        self._steps = steps

    def execute(self, req: Req, fallback: Res) -> Res:
        for step in self._steps:
            res = step(req)
            # None 表示继续传递；首个非 None 结果结束处理。
            if res is not None:
                return res
        return fallback


if __name__ == "__main__":
    steps: list[Step[int, str]] = [
        lambda n: "Negative" if n < 0 else None,
        lambda n: "Zero" if n == 0 else None,
        lambda n: "Positive" if n > 0 else None,
    ]
    p = Pipeline(steps)
    print(p.execute(-5, "Unknown"))
    print(p.execute(42, "Unknown"))
```

运行输出：

```text
Negative
Positive
```

## 4. 使用边界

先约定清楚继续、拒绝和完成分别如何表示；处理顺序通常也是业务规则的一部分。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Chain of Responsibility - Python 3.10+ Example: Functional Pipeline & Match-Case
"""
from collections.abc import Callable
from dataclasses import dataclass

HandlerFn = Callable[[str], str | None]


def auth_handler(request: str) -> str | None:
    match request:
        case "auth_fail":
            return "AuthHandler: Access Denied"
        case _:
            return None


def rate_limit_handler(request: str) -> str | None:
    match request:
        case "rate_exceeded":
            return "RateLimitHandler: 429 Too Many Requests"
        case _:
            return None


def business_handler(request: str) -> str | None:
    match request:
        case "valid_order":
            return "BusinessHandler: Order Processed Successfully"
        case _:
            return None


@dataclass
class HandlerPipeline:
    handlers: list[HandlerFn]

    def handle(self, request: str) -> str:
        for handler in self.handlers:
            result = handler(request)
            if result is not None:
                return result
        return "Pipeline: Request unhandled"


if __name__ == "__main__":
    pipeline = HandlerPipeline([auth_handler, rate_limit_handler, business_handler])
    print(pipeline.handle("rate_exceeded"))
    print(pipeline.handle("valid_order"))
    print(pipeline.handle("unknown"))
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Chain of Responsibility - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod
from typing import Any


class Handler(ABC):
    @abstractmethod
    def set_next(self, handler: "Handler") -> "Handler":
        pass

    @abstractmethod
    def handle(self, request: Any) -> str | None:
        pass


class AbstractHandler(Handler):
    _next_handler: Handler | None = None

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, request: Any) -> str | None:
        if self._next_handler:
            return self._next_handler.handle(request)
        return None


class MonkeyHandler(AbstractHandler):
    def handle(self, request: Any) -> str | None:
        if request == "Banana":
            return f"Monkey: I'll eat the {request}."
        return super().handle(request)


class SquirrelHandler(AbstractHandler):
    def handle(self, request: Any) -> str | None:
        if request == "Nut":
            return f"Squirrel: I'll eat the {request}."
        return super().handle(request)


class DogHandler(AbstractHandler):
    def handle(self, request: Any) -> str | None:
        if request == "MeatBall":
            return f"Dog: I'll eat the {request}."
        return super().handle(request)


def client_code(handler: Handler) -> None:
    for food in ["Nut", "Banana", "Cup of coffee"]:
        result = handler.handle(food)
        if result:
            print(f"  {result}")
        else:
            print(f"  {food} was left untouched.")


if __name__ == "__main__":
    monkey = MonkeyHandler()
    squirrel = SquirrelHandler()
    dog = DogHandler()

    monkey.set_next(squirrel).set_next(dog)
    client_code(monkey)
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 当程序需要使用不同方式处理不同种类请求，而且请求类型和顺序预先未知时
- 当必须按顺序执行多个处理者时
- 如果所需处理者及其顺序必须在运行时进行动态指定时

### 收益

- 你可以控制请求处理的顺序
- 单一职责原则：可以将发起操作和执行操作的类解耦
- 开闭原则：可以在不更改现有代码的情况下在应用中新增处理者

### 代价

- 部分请求可能未被任何处理者接收并处理（掉出链条末端）

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / chain-of-responsibility](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/behavioral/chain_of_responsibility.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
