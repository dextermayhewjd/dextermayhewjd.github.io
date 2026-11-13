---
title: "外观 · Facade"
description: "为一组子系统提供一个方便的调用入口。"
weight: 50
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [结构型](../)

## 1. 要解决什么问题

**为一组子系统提供一个方便的调用入口。**

当需要与数十个内部依赖复杂、调用次序严格的子系统对象协作时，客户端代码会与子系统细节深度绑定，导致维护、排错和测试极其困难。

## 2. 在 Python 中怎样表达

PipelineFacade[In, Out] 把两个处理步骤收进一个 execute 入口：先将输入交给 step1，再将中间字符串交给 step2。Stage[T, U] 描述每个步骤的输入输出。

**运行前先观察：**execute 的原始输入、中间字符串和最终输出分别交给哪一步？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Facade - Python 3.12+ Example: PEP 695 Generic Pipeline Facade
"""
from collections.abc import Callable

type Stage[T, U] = Callable[[T], U]


class PipelineFacade[In, Out]:
    def __init__(self, step1: Stage[In, str], step2: Stage[str, Out]) -> None:
        self._step1 = step1
        self._step2 = step2

    def execute(self, payload: In) -> Out:
        # 先取得中间字符串，再交给第二步。
        intermediate = self._step1(payload)
        return self._step2(intermediate)


if __name__ == "__main__":
    pipeline = PipelineFacade[dict[str, int], int](
        step1=lambda d: f"Length={len(d)}",
        step2=lambda s: len(s),
    )
    result = pipeline.execute({"a": 1, "b": 2})
    print(f"Pipeline Facade output: {result}")
```

运行输出：

```text
Pipeline Facade output: 8
```

## 4. 使用边界

外观可以简化入口，但不应把所有不相干的业务都集中进同一个大类。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Facade - Python 3.10+ Example: Dataclass Facade & Multi-Subsystem Coordination
"""
from dataclasses import dataclass, field


class AuthSubsystem:
    def verify_token(self, token: str) -> bool:
        return token == "valid-token"


class PaymentSubsystem:
    def charge(self, amount: float) -> str:
        return f"Charged ${amount:.2f}"


class NotificationSubsystem:
    def send_receipt(self, email: str, details: str) -> str:
        return f"Receipt sent to {email}: {details}"


@dataclass
class CheckoutFacade:
    auth: AuthSubsystem = field(default_factory=AuthSubsystem)
    payment: PaymentSubsystem = field(default_factory=PaymentSubsystem)
    notifier: NotificationSubsystem = field(default_factory=NotificationSubsystem)

    def process_order(self, token: str, email: str, amount: float) -> str:
        if not self.auth.verify_token(token):
            raise PermissionError("Invalid authentication token")
        receipt = self.payment.charge(amount)
        notify_res = self.notifier.send_receipt(email, receipt)
        return f"Order processed: {receipt} | {notify_res}"


if __name__ == "__main__":
    facade = CheckoutFacade()
    result = facade.process_order("valid-token", "user@example.com", 99.99)
    print(result)
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Facade - Conceptual Example (Classic GoF)
"""


class Subsystem1:
    def operation1(self) -> str:
        return "Subsystem1: Ready!"

    def operation_n(self) -> str:
        return "Subsystem1: Go!"


class Subsystem2:
    def operation1(self) -> str:
        return "Subsystem2: Get ready!"

    def operation_z(self) -> str:
        return "Subsystem2: Fire!"


class Facade:
    def __init__(self, subsystem1: Subsystem1 | None = None, subsystem2: Subsystem2 | None = None) -> None:
        self._subsystem1 = subsystem1 or Subsystem1()
        self._subsystem2 = subsystem2 or Subsystem2()

    def operation(self) -> str:
        results = []
        results.append("Facade initializes subsystems:")
        results.append(self._subsystem1.operation1())
        results.append(self._subsystem2.operation1())
        results.append("Facade orders subsystems to perform the action:")
        results.append(self._subsystem1.operation_n())
        results.append(self._subsystem2.operation_z())
        return "\n".join(results)


def client_code(facade: Facade) -> str:
    return facade.operation()


if __name__ == "__main__":
    facade = Facade()
    print(client_code(facade))
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 需要为一个复杂子系统提供一个简单接口时
- 需要将子系统组织为多层结构，通过外观定义每层的入口点以减少层级间依赖时

### 收益

- 让自己的代码独立于复杂子系统的细枝末节
- 降低整个系统的耦合度，提高模块复用性

### 代价

- 外观很容易成为与程序中所有类都耦合的“上帝对象（God Object）”

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / facade](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/structural/facade.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
