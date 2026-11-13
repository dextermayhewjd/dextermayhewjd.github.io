---
title: "备忘录 · Memento"
description: "保存状态快照，以便以后恢复。"
weight: 50
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [行为型](../)

## 1. 要解决什么问题

**保存状态快照，以便以后恢复。**

直接从外部复制对象的状态进行快照会导致对象的私有字段被迫暴露给外部管理者，彻底破坏面向对象的封装性。

## 2. 在 Python 中怎样表达

History[S] 保存状态快照并在 rollback 时取出最近一份；GameState 用 frozen dataclass 保存游戏状态，当前状态变化通过新建 GameState 表达。

**运行前先观察：**current 换成新 GameState 后，历史中保存的对象还是哪一份？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Memento - Python 3.12+ Example: PEP 695 Generic Snapshot History
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GameState:
    level: int
    score: int
    health: int


class History[S]:
    def __init__(self) -> None:
        self._checkpoints: list[S] = []

    def save(self, state: S) -> None:
        # 保存这一份状态对象；当前状态随后可以换成新对象。
        self._checkpoints.append(state)

    def rollback(self) -> S | None:
        return self._checkpoints.pop() if self._checkpoints else None


if __name__ == "__main__":
    history: History[GameState] = History()
    current = GameState(level=1, score=100, health=100)
    history.save(current)

    current = GameState(level=2, score=250, health=50)
    print(f"Level 2: {current}")

    prev = history.rollback()
    print(f"Rolled back to: {prev}")
```

运行输出：

```text
Level 2: GameState(level=2, score=250, health=50)
Rolled back to: GameState(level=1, score=100, health=100)
```

## 4. 使用边界

frozen 只阻止字段重新赋值，不会递归冻结字段内部的列表或字典；快照还需要考虑复制深度和内存。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Memento - Python 3.10+ Example: Frozen Dataclass Snapshots
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EditorSnapshot:
    text: str
    cursor_position: int
    selection_length: int


class TextEditor:
    def __init__(self) -> None:
        self.text: str = ""
        self.cursor: int = 0
        self.selection: int = 0

    def type_text(self, text: str) -> None:
        self.text += text
        self.cursor += len(text)

    def save(self) -> EditorSnapshot:
        return EditorSnapshot(self.text, self.cursor, self.selection)

    def restore(self, snapshot: EditorSnapshot) -> None:
        self.text = snapshot.text
        self.cursor = snapshot.cursor_position
        self.selection = snapshot.selection_length


if __name__ == "__main__":
    editor = TextEditor()
    editor.type_text("Initial text. ")
    saved = editor.save()

    editor.type_text("Draft modifications.")
    print(f"Modified: {editor.text}")

    editor.restore(saved)
    print(f"Restored: {editor.text}")
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Memento - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod
from datetime import datetime


class Memento(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_date(self) -> str:
        pass


class ConcreteMemento(Memento):
    def __init__(self, state: str) -> None:
        self._state = state
        self._date = str(datetime.now())[:19]

    def get_state(self) -> str:
        return self._state

    def get_name(self) -> str:
        return f"{self._date} / ({self._state[0:9]}...)"

    def get_date(self) -> str:
        return self._date


class Originator:
    _state: str = ""

    def __init__(self, state: str) -> None:
        self._state = state
        print(f"Originator: My initial state is: {self._state}")

    def do_something(self) -> None:
        print("Originator: I'm doing something important.")
        self._state = f"State_{datetime.now().microsecond}"
        print(f"Originator: and my state has changed to: {self._state}")

    def save(self) -> Memento:
        return ConcreteMemento(self._state)

    def restore(self, memento: Memento) -> None:
        assert isinstance(memento, ConcreteMemento)
        self._state = memento.get_state()
        print(f"Originator: My state has changed to: {self._state}")


class Caretaker:
    def __init__(self, originator: Originator) -> None:
        self._mementos: list[Memento] = []
        self._originator = originator

    def backup(self) -> None:
        print("\nCaretaker: Saving Originator's state...")
        self._mementos.append(self._originator.save())

    def undo(self) -> None:
        if not self._mementos:
            return
        memento = self._mementos.pop()
        print(f"Caretaker: Restoring state to: {memento.get_name()}")
        try:
            self._originator.restore(memento)
        except Exception:
            self.undo()


if __name__ == "__main__":
    originator = Originator("Super-duper-super-puper-super.")
    caretaker = Caretaker(originator)

    caretaker.backup()
    originator.do_something()

    caretaker.backup()
    originator.do_something()

    caretaker.undo()
    caretaker.undo()
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 当你需要创建对象状态快照来恢复其之前的状态时（例如撤销操作）
- 当直接访问对象的成员变量、获取器或设置器导致封装原则被破坏时

### 收益

- 可以在不破坏对象封装性的前提下创建对象状态快照
- 可以通过让负责人维护原发器状态历史记录来简化原发器代码

### 代价

- 如果客户端频繁创建备忘录，程序可能会消耗大量的内存
- 负责人必须完整跟踪原发器的生命周期，以便能够销毁过期的备忘录

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / memento](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/behavioral/memento.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
