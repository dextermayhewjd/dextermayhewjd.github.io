---
title: "观察者 · Observer"
description: "一次状态变化，通知多个订阅者。"
weight: 60
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [行为型](../)

## 1. 要解决什么问题

**一次状态变化，通知多个订阅者。**

当一个主对象的状态发生改变时，其他相关联的组件需要随之执行更新；若主对象直接维护外部依赖列表，将导致主对象与具体订阅者严重紧密耦合。

## 2. 在 Python 中怎样表达

EventSource[T] 登记 Listener[T] 回调；emit 接收一个事件并同步调用各个监听函数。type Listener[T] = Callable[[T], None] 描述回调签名。

**运行前先观察：**emit 发送字典事件时，登记的监听函数接收到什么？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Observer - Python 3.12+ Example: PEP 695 Generic EventSource
"""
from collections.abc import Callable

type Listener[T] = Callable[[T], None]


class EventSource[T]:
    def __init__(self) -> None:
        self._listeners: list[Listener[T]] = []

    def add_listener(self, listener: Listener[T]) -> None:
        self._listeners.append(listener)

    def emit(self, event: T) -> None:
        for listener in self._listeners:
            # 同步通知一个监听函数；返回后再通知下一个。
            listener(event)


if __name__ == "__main__":
    source: EventSource[dict[str, int]] = EventSource()
    source.add_listener(lambda payload: print(f"Listener received: {payload}"))
    source.emit({"temperature": 24, "humidity": 60})
```

运行输出：

```text
Listener received: {'temperature': 24, 'humidity': 60}
```

## 4. 使用边界

这里的通知是同步调用，没有提供取消订阅接口；一个回调抛出异常会中断本次通知。观察者模式本身不意味着异步或多线程。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Observer - Python 3.10+ Example: Callable Observers & Subscription Context Manager
"""
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Publisher:
    _subscribers: list[Callable[[str, Any], None]] = field(default_factory=list)

    def subscribe(self, callback: Callable[[str, Any], None]) -> Callable[[], None]:
        self._subscribers.append(callback)
        return lambda: self._subscribers.remove(callback) if callback in self._subscribers else None

    @contextmanager
    def temp_subscription(self, callback: Callable[[str, Any], None]):
        unsubscribe = self.subscribe(callback)
        try:
            yield
        finally:
            unsubscribe()

    def notify(self, event: str, data: Any) -> None:
        for cb in list(self._subscribers):
            cb(event, data)


if __name__ == "__main__":
    pub = Publisher()
    received = []
    unsub = pub.subscribe(lambda evt, data: received.append(f"{evt}:{data}"))
    pub.notify("price_update", 99.5)
    print("Received:", received)
    unsub()
    pub.notify("price_update", 100.0)
    print("After unsubscribe:", received)
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Observer - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod
from random import randrange
from typing import Any


class Subject(ABC):
    @abstractmethod
    def attach(self, observer: "Observer") -> None:
        pass

    @abstractmethod
    def detach(self, observer: "Observer") -> None:
        pass

    @abstractmethod
    def notify(self) -> None:
        pass


class ConcreteSubject(Subject):
    _state: int = 0
    _observers: list["Observer"] = []

    def attach(self, observer: "Observer") -> None:
        print("Subject: Attached an observer.")
        self._observers.append(observer)

    def detach(self, observer: "Observer") -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        print("Subject: Notifying observers...")
        for observer in self._observers:
            observer.update(self)

    def some_business_logic(self) -> None:
        print("\nSubject: I'm doing something important.")
        self._state = randrange(0, 10)
        print(f"Subject: My state has just changed to: {self._state}")
        self.notify()


class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject) -> None:
        pass


class ConcreteObserverA(Observer):
    def update(self, subject: Subject) -> None:
        assert isinstance(subject, ConcreteSubject)
        if subject._state < 3:
            print("ConcreteObserverA: Reacted to the event")


class ConcreteObserverB(Observer):
    def update(self, subject: Subject) -> None:
        assert isinstance(subject, ConcreteSubject)
        if subject._state == 0 or subject._state >= 2:
            print("ConcreteObserverB: Reacted to the event")


if __name__ == "__main__":
    subject = ConcreteSubject()
    observer_a = ConcreteObserverA()
    subject.attach(observer_a)

    observer_b = ConcreteObserverB()
    subject.attach(observer_b)

    subject.some_business_logic()
    subject.some_business_logic()

    subject.detach(observer_a)
    subject.some_business_logic()
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 当一个对象状态的改变需要改变其他对象，或实际对象数量未知、动态变化时
- 当应用中的一些对象必须观察其他对象，但仅在特定条件下或有限时间内进行观察时

### 收益

- 开闭原则：你无需修改发布者代码就能引入新的订阅者类（反之亦然）
- 可以在运行时建立对象之间的依赖关系

### 代价

- 订阅者的通知顺序通常是随机的
- 如果订阅者未及时解绑，可能会导致内存泄漏（失落的监听器问题）

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / observer](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/behavioral/observer.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
