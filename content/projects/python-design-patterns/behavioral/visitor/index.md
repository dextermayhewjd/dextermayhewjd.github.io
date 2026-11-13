---
title: "访问者 · Visitor"
description: "针对一组对象类型增加新的操作。"
weight: 100
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [行为型](../)

## 1. 要解决什么问题

**针对一组对象类型增加新的操作。**

当一套核心对象结构（例如语法树 AST、报表节点、CAD 图形结构）已经稳定，但经常需要对其执行各种不同的操作（如代码检查、导出 XML、计算累计面积、生成字节码）。如果把这些新操作都塞进各个节点类中，会污染核心类的业务职责并导致频繁修改发布。

## 2. 在 Python 中怎样表达

type Expression = Num | BinOp 描述表达式节点；evaluate_expression 用 match 区分数字、加法和乘法，再递归计算子表达式。

**运行前先观察：**遇到 Num 与 BinOp 时各执行哪个分支，嵌套加法和乘法怎样交回结果？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Visitor - Python 3.12+ Example: PEP 695 Type Alias & Pattern Matching
"""
from dataclasses import dataclass

type Expression = Num | BinOp


@dataclass
class Num:
    value: int


@dataclass
class BinOp:
    left: Expression
    op: str
    right: Expression


def evaluate_expression(expr: Expression) -> int:
    match expr:
        case Num(val):
            return val
        case BinOp(l, "+", r):
            # 递归计算左右子表达式，再组合为加法结果。
            return evaluate_expression(l) + evaluate_expression(r)
        case BinOp(l, "*", r):
            return evaluate_expression(l) * evaluate_expression(r)
        case _:
            raise ValueError(f"Unknown operation: {expr}")


if __name__ == "__main__":
    ast: Expression = BinOp(Num(3), "*", BinOp(Num(4), "+", Num(5)))
    print("Evaluated AST:", evaluate_expression(ast))
```

运行输出：

```text
Evaluated AST: 27
```

## 4. 使用边界

这是用联合类型与模式匹配组织访问操作的替代方案，不是经典双重分派。新增节点类型时仍要补充相应处理分支。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Visitor - Python 3.10+ Example: @functools.singledispatch & Match-Case
"""
from dataclasses import dataclass
from functools import singledispatch


@dataclass
class NumberNode:
    val: float


@dataclass
class AddNode:
    left: object
    right: object


# In Python, @singledispatch eliminates the need for double-dispatch accept() methods!
@singledispatch
def evaluate(node) -> float:
    raise NotImplementedError(f"Unsupported node type: {type(node)}")


@evaluate.register
def _(node: NumberNode) -> float:
    return node.val


@evaluate.register
def _(node: AddNode) -> float:
    return evaluate(node.left) + evaluate(node.right)


def stringify(node) -> str:
    """Alternative visitor implemented purely with pattern matching."""
    match node:
        case NumberNode(val):
            return str(val)
        case AddNode(left, right):
            return f"({stringify(left)} + {stringify(right)})"
        case _:
            return str(node)


if __name__ == "__main__":
    expr = AddNode(NumberNode(10), AddNode(NumberNode(5), NumberNode(3)))
    print("Formula:", stringify(expr))
    print("Evaluated result:", evaluate(expr))
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Visitor - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class Component(ABC):
    @abstractmethod
    def accept(self, visitor: "Visitor") -> str:
        pass


class ConcreteComponentA(Component):
    def accept(self, visitor: "Visitor") -> str:
        return visitor.visit_concrete_component_a(self)

    def exclusive_method_of_concrete_component_a(self) -> str:
        return "A"


class ConcreteComponentB(Component):
    def accept(self, visitor: "Visitor") -> str:
        return visitor.visit_concrete_component_b(self)

    def special_method_of_concrete_component_b(self) -> str:
        return "B"


class Visitor(ABC):
    @abstractmethod
    def visit_concrete_component_a(self, element: ConcreteComponentA) -> str:
        pass

    @abstractmethod
    def visit_concrete_component_b(self, element: ConcreteComponentB) -> str:
        pass


class ConcreteVisitor1(Visitor):
    def visit_concrete_component_a(self, element: ConcreteComponentA) -> str:
        return f"{element.exclusive_method_of_concrete_component_a()} + ConcreteVisitor1"

    def visit_concrete_component_b(self, element: ConcreteComponentB) -> str:
        return f"{element.special_method_of_concrete_component_b()} + ConcreteVisitor1"


class ConcreteVisitor2(Visitor):
    def visit_concrete_component_a(self, element: ConcreteComponentA) -> str:
        return f"{element.exclusive_method_of_concrete_component_a()} + ConcreteVisitor2"

    def visit_concrete_component_b(self, element: ConcreteComponentB) -> str:
        return f"{element.special_method_of_concrete_component_b()} + ConcreteVisitor2"


def client_code(components: list[Component], visitor: Visitor) -> None:
    for component in components:
        print(component.accept(visitor))


if __name__ == "__main__":
    components: list[Component] = [ConcreteComponentA(), ConcreteComponentB()]

    print("The client code works with all visitors via the base Visitor interface:")
    visitor1 = ConcreteVisitor1()
    client_code(components, visitor1)

    print("\nIt allows the same client code to work with different visitors:")
    visitor2 = ConcreteVisitor2()
    client_code(components, visitor2)
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 如果你需要对一个复杂对象结构（例如对象树）中的所有元素执行某些操作，可使用访问者模式
- 可使用访问者模式来清理辅助行为的业务逻辑
- 当某个行为仅在类层次结构中的一些类中有意义，而在其他类中没有意义时

### 收益

- 开闭原则：你可以引入在不同类对象上执行的新行为，且无需对这些类做出修改
- 单一职责原则：可将同一行为的多个不同版本集中在同一个类中
- 访问者可以在遍历对象结构的过程中累积状态

### 代价

- 每次在元素层次结构中增加或删除元素类时，都必须更新所有访问者类
- 在访问者访问私有成员变量和方法时，可能会违反封装原则

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / visitor](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/behavioral/visitor.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
