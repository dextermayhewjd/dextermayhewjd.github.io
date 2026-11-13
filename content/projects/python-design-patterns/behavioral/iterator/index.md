---
title: "迭代器 · Iterator"
description: "逐个产生元素，让调用方不必了解内部结构。"
weight: 30
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [行为型](../)

## 1. 要解决什么问题

**逐个产生元素，让调用方不必了解内部结构。**

复杂集合（如复杂二叉树、图结构、远程分页集合）具有不同的遍历算法。如果将所有遍历逻辑塞入集合类中，会破坏其存储职责，且客户端需了解集合内部私有结构。

## 2. 在 Python 中怎样表达

batch_stream[T] 用 yield 分批交出列表；PipelineSource[T].__iter__ 用 yield from 交出内部元素。T 表示元素类型，不改变生成器的执行时机。

**运行前先观察：**batch_stream 何时开始产生批次，PipelineSource 的一次遍历何时创建生成器？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Iterator - Python 3.12+ Example: PEP 695 Generic Generator & Iterable Protocol
"""
from collections.abc import Iterator


def batch_stream[T](items: list[T], batch_size: int) -> Iterator[list[T]]:
    for i in range(0, len(items), batch_size):
        # 每次交出一批元素，然后暂停等待下一次取值。
        yield items[i : i + batch_size]


class PipelineSource[T]:
    def __init__(self, data: list[T]) -> None:
        self._data = data

    def __iter__(self) -> Iterator[T]:
        yield from self._data


if __name__ == "__main__":
    src: PipelineSource[int] = PipelineSource([1, 2, 3, 4, 5])
    print(f"Pipelined items: {list(src)}")
    batches = list(batch_stream(["a", "b", "c", "d"], batch_size=2))
    print(f"Batches: {batches}")
```

运行输出：

```text
Pipelined items: [1, 2, 3, 4, 5]
Batches: [['a', 'b'], ['c', 'd']]
```

## 4. 使用边界

每个生成器对象通常只能消费一遍；PipelineSource 每次调用 __iter__ 都创建新的生成器，因此这个源对象可以重复遍历。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Iterator - Python 3.10+ Example: Generators & yield from
"""
from collections.abc import Iterator


class BinaryTreeNode:
    def __init__(self, value: int, left: "BinaryTreeNode | None" = None, right: "BinaryTreeNode | None" = None) -> None:
        self.value = value
        self.left = left
        self.right = right

    def __iter__(self) -> Iterator[int]:
        """In-order tree traversal via generator."""
        if self.left:
            yield from self.left
        yield self.value
        if self.right:
            yield from self.right


def paginated_fetch(pages: int, per_page: int) -> Iterator[str]:
    """Generator-based streaming pagination."""
    for p in range(1, pages + 1):
        for i in range(1, per_page + 1):
            yield f"Page {p} - Item {i}"


if __name__ == "__main__":
    # Tree traversal using yield from
    root = BinaryTreeNode(10, BinaryTreeNode(5), BinaryTreeNode(15))
    print(f"Tree values in-order: {list(root)}")

    # Streaming items
    for item in paginated_fetch(pages=2, per_page=2):
        print(f"Stream: {item}")
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Iterator - Conceptual Example: Pythonic __iter__ and __next__ (Classic GoF)
"""
from collections.abc import Iterable, Iterator
from typing import Any


class AlphabeticalOrderIterator(Iterator):
    _position: int = 0
    _reverse: bool = False

    def __init__(self, collection: "WordsCollection", reverse: bool = False) -> None:
        self._collection = collection
        self._reverse = reverse
        self._position = -1 if reverse else 0

    def __next__(self) -> Any:
        try:
            value = self._collection[self._position]
            self._position += -1 if self._reverse else 1
        except IndexError:
            raise StopIteration()
        return value


class WordsCollection(Iterable):
    def __init__(self, collection: list[Any] | None = None) -> None:
        self._collection = collection or []

    def __getitem__(self, index: int) -> Any:
        return self._collection[index]

    def __iter__(self) -> AlphabeticalOrderIterator:
        return AlphabeticalOrderIterator(self)

    def get_reverse_iterator(self) -> AlphabeticalOrderIterator:
        return AlphabeticalOrderIterator(self, reverse=True)

    def add_item(self, item: Any) -> None:
        self._collection.append(item)


if __name__ == "__main__":
    collection = WordsCollection()
    collection.add_item("First")
    collection.add_item("Second")
    collection.add_item("Third")

    print("Straight traversal:")
    print("\n".join(collection))

    print("\nReverse traversal:")
    print("\n".join(collection.get_reverse_iterator()))
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 当集合在底层拥有复杂的数据结构，并且你希望对客户端隐藏其复杂性时
- 使用该模式可以减少程序中重复的遍历代码
- 如果你希望代码能够遍历不同的甚至无法预知的数据结构时

### 收益

- 单一职责原则：可以将繁琐的遍历算法从集合业务类中分离
- 开闭原则：可以实现新型的集合和迭代器并将其传递给现有代码，无需修改已有逻辑
- 可以并行遍历同一个集合，因为每个迭代器对象都维护自己的迭代状态

### 代价

- 如果应用程序只需处理简单列表，使用迭代器可能会过度设计

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / iterator](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/behavioral/iterator.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
