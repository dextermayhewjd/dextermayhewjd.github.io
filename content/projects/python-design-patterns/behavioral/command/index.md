---
title: "命令 · Command"
description: "把一次操作保存成以后可以执行的值。"
weight: 20
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [行为型](../)

## 1. 要解决什么问题

**把一次操作保存成以后可以执行的值。**

如果用户界面按钮、菜单栏、快捷键直接调用具体的业务逻辑函数，会导致触发端（Invoker）与业务执行端（Receiver）强耦合，且无法实现统一的操作历史撤销、宏命令录制以及请求队列重试。

## 2. 在 Python 中怎样表达

Action[T] 保存数据 payload、正向函数 forward 和逆向函数 backward。TextBuffer 创建动作后，由调用方通过 apply 执行、revert 撤销。

**运行前先观察：**make_append_action、apply、revert 分别何时创建操作、修改内容和撤销修改？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Command - Python 3.12+ Example: PEP 695 Generic Command & typing.Self
"""
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Action[T]:
    payload: T
    forward: Callable[[T], None]
    backward: Callable[[T], None]

    def apply(self) -> None:
        # 执行之前保存的动作，将 payload 交给正向函数。
        self.forward(self.payload)

    def revert(self) -> None:
        self.backward(self.payload)


class TextBuffer:
    def __init__(self) -> None:
        self.content: list[str] = []

    def make_append_action(self, text: str) -> Action[str]:
        return Action(
            payload=text,
            forward=lambda t: self.content.append(t),
            backward=lambda _: self.content.pop() if self.content else None,
        )


if __name__ == "__main__":
    buf = TextBuffer()
    act = buf.make_append_action("Hello Python 3.12")
    act.apply()
    print(f"Buffer: {buf.content}")
    act.revert()
    print(f"Buffer after revert: {buf.content}")
```

运行输出：

```text
Buffer: ['Hello Python 3.12']
Buffer after revert: []
```

## 4. 使用边界

Callable 不会自动提供撤销。撤销需要保存足够的旧状态，外部副作用也未必能完全恢复。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Command - Python 3.10+ Example: Dataclass Command with Callable & Undo Stack
"""
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Command:
    execute: Callable[[], None]
    undo: Callable[[], None]
    description: str = ""


class Canvas:
    def __init__(self) -> None:
        self.elements: list[str] = []

    def draw(self, shape: str) -> Command:
        def do() -> None:
            self.elements.append(shape)

        def undo() -> None:
            if self.elements:
                self.elements.pop()

        return Command(execute=do, undo=undo, description=f"Draw {shape}")


@dataclass
class CommandManager:
    _history: list[Command] = field(default_factory=list)

    def execute(self, cmd: Command) -> None:
        cmd.execute()
        self._history.append(cmd)

    def undo(self) -> str | None:
        if not self._history:
            return None
        cmd = self._history.pop()
        cmd.undo()
        return cmd.description


if __name__ == "__main__":
    canvas = Canvas()
    mgr = CommandManager()

    mgr.execute(canvas.draw("Circle"))
    mgr.execute(canvas.draw("Square"))
    print(f"Canvas: {canvas.elements}")

    undone = mgr.undo()
    print(f"Undone: {undone}, Canvas now: {canvas.elements}")
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Command - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass


class SimpleCommand(Command):
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def execute(self) -> None:
        print(f"SimpleCommand: See, I can do simple things like printing ({self._payload})")


class Receiver:
    def do_something(self, a: str) -> None:
        print(f"Receiver: Working on ({a}.)")

    def do_something_else(self, b: str) -> None:
        print(f"Receiver: Also working on ({b}.)")


class ComplexCommand(Command):
    def __init__(self, receiver: Receiver, a: str, b: str) -> None:
        self._receiver = receiver
        self._a = a
        self._b = b

    def execute(self) -> None:
        print("ComplexCommand: Complex stuff should be done by a receiver object")
        self._receiver.do_something(self._a)
        self._receiver.do_something_else(self._b)


class Invoker:
    _on_start: Command | None = None
    _on_finish: Command | None = None

    def set_on_start(self, command: Command) -> None:
        self._on_start = command

    def set_on_finish(self, command: Command) -> None:
        self._on_finish = command

    def do_something_important(self) -> None:
        print("Invoker: Does anybody want something done before I begin?")
        if self._on_start:
            self._on_start.execute()

        print("Invoker: ...doing something really important...")

        print("Invoker: Does anybody want something done after I finish?")
        if self._on_finish:
            self._on_finish.execute()


if __name__ == "__main__":
    invoker = Invoker()
    invoker.set_on_start(SimpleCommand("Say Hi!"))
    receiver = Receiver()
    invoker.set_on_finish(ComplexCommand(receiver, "Send email", "Save report"))

    invoker.do_something_important()
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 需要通过操作来参数化对象时（例如将回调函数封装为可传递的命令对象）
- 需要将操作放入队列中、操作的执行或者远程执行时
- 需要实现操作的撤销（Undo）与重做（Redo）功能时

### 收益

- 单一职责原则：可以将触发操作的类和执行操作的类解耦
- 开闭原则：可以在不修改现有客户端代码的情况下创建新命令
- 可以实现撤销和恢复功能
- 可以实现操作的延迟执行或队列化调度

### 代价

- 代码可能会变得更繁琐，因为在发送者和接收者之间增加了一个全新的中间命令层

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / command](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/behavioral/command.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
