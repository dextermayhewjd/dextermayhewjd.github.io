---
title: "模板方法 · Template Method"
description: "固定处理步骤，把可变化的步骤留给调用方。"
weight: 90
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [行为型](../)

## 1. 要解决什么问题

**固定处理步骤，把可变化的步骤留给调用方。**

当多个类实现相同的整体算法流程（例如数据导入流水线：打开文件 -> 提取原始数据 -> 解析数据 -> 输出报告 -> 关闭文件），但各个子类在某些特定步骤的处理细节上有所不同。如果让每个子类各自实现完整流程，会导致算法骨架和通用步骤代码大量重复。

## 2. 在 Python 中怎样表达

BaseWorkflow[T, R].execute 固定先 sanitize 再 process 的步骤；TextWorkflow 通过重写两个方法指定文本处理行为，@override 标记这些重写方法。

**运行前先观察：**execute 固定了什么调用顺序，TextWorkflow 又替换了哪两个步骤？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Template Method - Python 3.12+ Example: PEP 695 Generic Workflow & @override
"""
from typing import override


class BaseWorkflow[T, R]:
    def execute(self, payload: T) -> R:
        # 外层固定先清洗再处理；具体步骤由子类重写。
        cleaned = self.sanitize(payload)
        return self.process(cleaned)

    def sanitize(self, payload: T) -> T:
        return payload

    def process(self, payload: T) -> R:
        raise NotImplementedError


class TextWorkflow(BaseWorkflow[str, int]):
    @override
    def sanitize(self, payload: str) -> str:
        return payload.strip()

    @override
    def process(self, payload: str) -> int:
        return len(payload)


if __name__ == "__main__":
    wf = TextWorkflow()
    count = wf.execute("   Hello World   ")
    print(f"Workflow processed count: {count}")
```

运行输出：

```text
Workflow processed count: 11
```

## 4. 使用边界

@override 帮助类型检查器核对是否正确重写，不会在运行时自动校验所有行为。模板方法依赖继承关系，应保持步骤接口稳定。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Template Method - Python 3.10+ Example: Higher-Order Function Workflow with Hooks
"""
from collections.abc import Callable
from typing import Any


def process_pipeline(
    raw_data: str,
    parser: Callable[[str], dict[str, Any]],
    formatter: Callable[[dict[str, Any]], str] | None = None,
) -> str:
    """Template workflow: load -> parse -> format -> deliver."""
    print("Pipeline: Validating raw input data...")
    parsed = parser(raw_data)

    print("Pipeline: Processing internal business rules...")
    if formatter:
        return formatter(parsed)
    return f"Standard Output: {parsed}"


if __name__ == "__main__":
    def json_parser(data: str) -> dict[str, Any]:
        return {"type": "json", "content": data.strip("{}")}

    result = process_pipeline(
        raw_data="{user: 'Alice'}",
        parser=json_parser,
        formatter=lambda d: f"Custom JSON Report -> {d['content']}",
    )
    print(result)
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Template Method - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class AbstractClass(ABC):
    def template_method(self) -> None:
        self.base_operation1()
        self.required_operations1()
        self.base_operation2()
        self.hook1()
        self.required_operation2()
        self.base_operation3()
        self.hook2()

    def base_operation1(self) -> None:
        print("AbstractClass says: I am doing the bulk of the work")

    def base_operation2(self) -> None:
        print("AbstractClass says: But I let subclasses override some operations")

    def base_operation3(self) -> None:
        print("AbstractClass says: But I am doing the bulk of the work anyway")

    @abstractmethod
    def required_operations1(self) -> None:
        pass

    @abstractmethod
    def required_operation2(self) -> None:
        pass

    def hook1(self) -> None:
        pass

    def hook2(self) -> None:
        pass


class ConcreteClass1(AbstractClass):
    def required_operations1(self) -> None:
        print("ConcreteClass1 says: Implemented Operation1")

    def required_operation2(self) -> None:
        print("ConcreteClass1 says: Implemented Operation2")


class ConcreteClass2(AbstractClass):
    def required_operations1(self) -> None:
        print("ConcreteClass2 says: Implemented Operation1")

    def required_operation2(self) -> None:
        print("ConcreteClass2 says: Implemented Operation2")

    def hook1(self) -> None:
        print("ConcreteClass2 says: Overridden Hook1")


def client_code(abstract_class: AbstractClass) -> None:
    abstract_class.template_method()


if __name__ == "__main__":
    print("Same client code can work with different subclasses:")
    client_code(ConcreteClass1())
    print("")
    client_code(ConcreteClass2())
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 只希望客户端扩展某个特定算法步骤，而不是整个算法或其结构时
- 当多个类的算法大体相同，仅在某些特定细节上略有差异时

### 收益

- 你只允许客户端重写一个庞大算法中的特定部分，使得算法其他部分不会被轻易破坏
- 你可以将相同的代码提取到超类中，消除代码重复

### 代价

- 部分客户端可能会受到算法框架现有结构的限制
- 通过子类重写默认步骤可能违反里氏替换原则
- 模板方法中的步骤越多，其维护工作就越繁琐

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / template-method](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/behavioral/template_method.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
