---
title: "状态 · State"
description: "让同一个对象在不同状态下响应不同。"
weight: 70
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [行为型](../)

## 1. 要解决什么问题

**让同一个对象在不同状态下响应不同。**

当一个对象的行为严重取决于其当前状态（例如订单状态机、文档流转审批、网络连接状态），如果在方法中大量使用 `if (state == A) ... else if (state == B)` 分支语句，随着新状态增加，条件逻辑将变得难以理解与维护。

## 2. 在 Python 中怎样表达

StateMachine[S, E] 按 (当前状态, 事件) 在 TransitionTable[S, E] 中查下一状态；trigger 修改状态并返回 self，Self 描述可继续调用的状态机对象。

**运行前先观察：**投币 coin 和推动 push 各在哪个状态下有效，触发后状态变成什么？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
State - Python 3.12+ Example: PEP 695 Generic Finite State Machine
"""
from typing import Self

type TransitionTable[S, E] = dict[tuple[S, E], S]


class StateMachine[S, E]:
    def __init__(self, initial_state: S, transitions: TransitionTable[S, E]) -> None:
        self.state = initial_state
        self._transitions = transitions

    def trigger(self, event: E) -> Self:
        key = (self.state, event)
        if key in self._transitions:
            # 按当前状态和事件查表，将状态改为目标状态。
            self.state = self._transitions[key]
        else:
            raise ValueError(f"Invalid transition from {self.state} with event {event}")
        return self


if __name__ == "__main__":
    table: TransitionTable[str, str] = {
        ("locked", "coin"): "unlocked",
        ("unlocked", "push"): "locked",
    }
    turnstile = StateMachine("locked", table)
    turnstile.trigger("coin")
    print(f"State after coin: {turnstile.state}")
    turnstile.trigger("push")
    print(f"State after push: {turnstile.state}")
```

运行输出：

```text
State after coin: unlocked
State after push: locked
```

## 4. 使用边界

表中没有对应项时会抛出 ValueError；类型参数不自动补全状态转换规则。复杂状态可以另行封装行为。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
State - Python 3.10+ Example: Enum & Pattern-Matching State Transitions
"""
from dataclasses import dataclass
from enum import Enum, auto


class State(Enum):
    DRAFT = auto()
    IN_REVIEW = auto()
    PUBLISHED = auto()


@dataclass
class Document:
    title: str
    state: State = State.DRAFT

    def publish(self) -> str:
        match self.state:
            case State.DRAFT:
                self.state = State.IN_REVIEW
                return f"'{self.title}' submitted for review"
            case State.IN_REVIEW:
                self.state = State.PUBLISHED
                return f"'{self.title}' published successfully"
            case State.PUBLISHED:
                return f"'{self.title}' is already published"


if __name__ == "__main__":
    doc = Document("Design Patterns in Python 3.10")
    print(doc.publish())
    print(doc.publish())
    print(doc.publish())
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
State - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class Context:
    _state: "State | None" = None

    def __init__(self, state: "State") -> None:
        self.transition_to(state)

    def transition_to(self, state: "State") -> None:
        print(f"Context: Transition to {type(state).__name__}")
        self._state = state
        self._state.context = self

    def request1(self) -> None:
        assert self._state is not None
        self._state.handle1()

    def request2(self) -> None:
        assert self._state is not None
        self._state.handle2()


class State(ABC):
    @property
    def context(self) -> Context:
        assert self._context is not None
        return self._context

    @context.setter
    def context(self, context: Context) -> None:
        self._context = context

    @abstractmethod
    def handle1(self) -> None:
        pass

    @abstractmethod
    def handle2(self) -> None:
        pass


class ConcreteStateA(State):
    def handle1(self) -> None:
        print("ConcreteStateA handles request1.")
        print("ConcreteStateA wants to change the state of the context.")
        self.context.transition_to(ConcreteStateB())

    def handle2(self) -> None:
        print("ConcreteStateA handles request2.")


class ConcreteStateB(State):
    def handle1(self) -> None:
        print("ConcreteStateB handles request1.")

    def handle2(self) -> None:
        print("ConcreteStateB handles request2.")
        print("ConcreteStateB wants to change the state of the context.")
        self.context.transition_to(ConcreteStateA())


if __name__ == "__main__":
    context = Context(ConcreteStateA())
    context.request1()
    context.request2()
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 对象需要根据自身当前状态进行不同行为，同时状态数量非常多且状态代码经常改变时
- 某个类需要根据属性值进行大量条件语句分支判断时
- 当相似状态和基于条件的状态转换中存在许多重复代码时

### 收益

- 单一职责原则：将与特定状态相关的代码组织进独立的类中
- 开闭原则：无需修改已有状态类和上下文即可引入新状态
- 消除庞大的条件状态机分支语句

### 代价

- 如果状态机只有很少的几个状态或者很少改变，应用该模式可能会显得小题大做

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / state](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/behavioral/state.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
