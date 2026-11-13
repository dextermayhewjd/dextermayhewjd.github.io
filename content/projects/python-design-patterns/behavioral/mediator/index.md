---
title: "中介者 · Mediator"
description: "把多个参与者之间的协作集中到一个中间角色。"
weight: 40
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [行为型](../)

## 1. 要解决什么问题

**把多个参与者之间的协作集中到一个中间角色。**

当多个对象之间存在复杂的网状交叉引用（例如表单中的各个输入框、校验器、复选框和提交按钮相互依赖），任何组件的小修改都会波及其他组件，导致难以复用。

## 2. 在 Python 中怎样表达

Mediator[Msg] 保存处理函数，broadcast 将同一个 UIAction 依次交给这些函数。参与者通过中心通信，Msg 描述消息类型。

**运行前先观察：**UIAction 先交给谁，再由谁调用登记的处理函数？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Mediator - Python 3.12+ Example: PEP 695 Generic Event Mediator
"""
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class UIAction:
    widget_id: str
    payload: str


class Mediator[Msg]:
    def __init__(self) -> None:
        self._handlers: list[Callable[[Msg], None]] = []

    def register(self, handler: Callable[[Msg], None]) -> None:
        self._handlers.append(handler)

    def broadcast(self, message: Msg) -> None:
        for handler in self._handlers:
            # 中心将同一条消息同步交给每个处理函数。
            handler(message)


if __name__ == "__main__":
    mediator: Mediator[UIAction] = Mediator()
    mediator.register(lambda a: print(f"Handler 1 received action from {a.widget_id}: {a.payload}"))
    mediator.register(lambda a: print(f"Handler 2 logging {a.payload}"))
    mediator.broadcast(UIAction("btn_submit", "Click event triggered"))
```

运行输出：

```text
Handler 1 received action from btn_submit: Click event triggered
Handler 2 logging Click event triggered
```

## 4. 使用边界

这里展示集中广播的最小结构，与观察者的示例接近。中介者是否承担协作调度，要看业务规则如何组织，不能仅凭类名判断。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Mediator - Python 3.10+ Example: Event-Driven Hub with Match-Case
"""
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Event:
    topic: str
    sender: str
    data: dict[str, str] = field(default_factory=dict)


class EventMediator:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[Event], None]]] = {}

    def subscribe(self, topic: str, listener: Callable[[Event], None]) -> None:
        self._listeners.setdefault(topic, []).append(listener)

    def publish(self, event: Event) -> None:
        match event.topic:
            case "auth:login":
                print(f"[Mediator Audit] User login triggered by {event.sender}")
            case "cart:checkout":
                print(f"[Mediator Audit] Checkout initiated with items {event.data}")
            case _:
                pass

        for listener in self._listeners.get(event.topic, []):
            listener(event)


if __name__ == "__main__":
    hub = EventMediator()
    hub.subscribe("cart:checkout", lambda e: print(f"Inventory reserve notified: {e.data}"))
    hub.publish(Event(topic="cart:checkout", sender="WebClient", data={"sku": "PROD-1", "qty": "2"}))
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Mediator - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class Mediator(ABC):
    @abstractmethod
    def notify(self, sender: object, event: str) -> None:
        pass


class BaseComponent:
    def __init__(self, mediator: Mediator | None = None) -> None:
        self._mediator = mediator

    @property
    def mediator(self) -> Mediator:
        assert self._mediator is not None
        return self._mediator

    @mediator.setter
    def mediator(self, mediator: Mediator) -> None:
        self._mediator = mediator


class Component1(BaseComponent):
    def do_a(self) -> None:
        print("Component 1 does A.")
        self.mediator.notify(self, "A")

    def do_b(self) -> None:
        print("Component 1 does B.")
        self.mediator.notify(self, "B")


class Component2(BaseComponent):
    def do_c(self) -> None:
        print("Component 2 does C.")
        self.mediator.notify(self, "C")

    def do_d(self) -> None:
        print("Component 2 does D.")
        self.mediator.notify(self, "D")


class ConcreteMediator(Mediator):
    def __init__(self, c1: Component1, c2: Component2) -> None:
        self._c1 = c1
        self._c1.mediator = self
        self._c2 = c2
        self._c2.mediator = self

    def notify(self, sender: object, event: str) -> None:
        if event == "A":
            print("Mediator reacts on A and triggers following operations:")
            self._c2.do_c()
        elif event == "D":
            print("Mediator reacts on D and triggers following operations:")
            self._c1.do_b()
            self._c2.do_c()


if __name__ == "__main__":
    c1 = Component1()
    c2 = Component2()
    mediator = ConcreteMediator(c1, c2)

    print("Client triggers operation A.")
    c1.do_a()

    print("\nClient triggers operation D.")
    c2.do_d()
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 当一些对象和其他对象紧密耦合以致难以对其进行修改时
- 当组件因过于依赖其他组件而无法在不同应用中复用时
- 如果为了在不同情景下复用一些基本行为而导致需要创建大量组件子类时

### 收益

- 单一职责原则：可以将多个组件间的通信抽取到单一位置，更易于理解和维护
- 开闭原则：无需修改实际组件就能增加新的中介者
- 可以减轻应用中多个组件之间的高耦合度

### 代价

- 随着时间推移，中介者很容易演变为无所不知的“上帝对象（God Object）”

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / mediator](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/behavioral/mediator.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
