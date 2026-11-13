---
title: "策略 · Strategy"
description: "保持调用流程不变，替换其中的算法。"
weight: 80
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [行为型](../)

## 1. 要解决什么问题

**保持调用流程不变，替换其中的算法。**

当一个类有许多相似但在细节上不同的算法行为（如不同格式的数据压缩、不同运输方式的运费计算、不同的支付通道或排序方式），若将所有算法硬编码进同一类中，会产生庞大的条件分支语句且难以扩展新算法。

## 2. 在 Python 中怎样表达

type Strategy[T, R] = Callable[[T], R] 描述策略函数；AlgorithmRunner[T, R] 保存策略，run 将输入交给它并返回结果。

**运行前先观察：**替换传入 AlgorithmRunner 的策略函数后，run 自身需要怎样改变？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Strategy - Python 3.12+ Example: PEP 695 Generic Strategy
"""
from collections.abc import Callable

type Strategy[T, R] = Callable[[T], R]


class AlgorithmRunner[T, R]:
    def __init__(self, strategy: Strategy[T, R]) -> None:
        self.strategy = strategy

    def run(self, data: T) -> R:
        # 将输入交给保存的策略函数，返回它的计算结果。
        return self.strategy(data)


if __name__ == "__main__":
    runner = AlgorithmRunner[list[str], list[str]](strategy=lambda items: sorted(items, reverse=True))
    result = runner.run(["apple", "banana", "cherry"])
    print(f"Reversed sort: {result}")
```

运行输出：

```text
Reversed sort: ['cherry', 'banana', 'apple']
```

## 4. 使用边界

无状态的算法用函数很直接；算法需要配置、状态或多个关联操作时，策略对象仍然合适。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Strategy - Python 3.10+ Example: First-Class Callable Strategies
"""
from collections.abc import Callable


# A Strategy in Python is simply a Callable
ShippingStrategy = Callable[[float, float], float]


def standard_shipping(weight_kg: float, distance_km: float) -> float:
    return 5.0 + (weight_kg * 1.5) + (distance_km * 0.05)


def express_shipping(weight_kg: float, distance_km: float) -> float:
    return 20.0 + (weight_kg * 4.0) + (distance_km * 0.15)


def free_economy_shipping(weight_kg: float, distance_km: float) -> float:
    return 0.0


def calculate_shipping(weight_kg: float, distance_km: float, strategy: ShippingStrategy) -> float:
    return strategy(weight_kg, distance_km)


if __name__ == "__main__":
    cost1 = calculate_shipping(2.5, 120, standard_shipping)
    print(f"Standard Shipping: ${cost1:.2f}")

    cost2 = calculate_shipping(2.5, 120, express_shipping)
    print(f"Express Shipping:  ${cost2:.2f}")

    # Ad-hoc strategy via lambda
    cost3 = calculate_shipping(2.5, 120, lambda w, d: w * 2.0)
    print(f"Custom Flat Rate:  ${cost3:.2f}")
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Strategy - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class Strategy(ABC):
    @abstractmethod
    def do_algorithm(self, data: list[str]) -> list[str]:
        pass


class ConcreteStrategyA(Strategy):
    def do_algorithm(self, data: list[str]) -> list[str]:
        return sorted(data)


class ConcreteStrategyB(Strategy):
    def do_algorithm(self, data: list[str]) -> list[str]:
        return list(reversed(sorted(data)))


class Context:
    def __init__(self, strategy: Strategy) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> Strategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: Strategy) -> None:
        self._strategy = strategy

    def do_some_business_logic(self, data: list[str]) -> str:
        print("Context: Sorting data using the strategy (not sure how it'll do it)")
        result = self._strategy.do_algorithm(data)
        return ", ".join(result)


if __name__ == "__main__":
    context = Context(ConcreteStrategyA())
    data = ["a", "b", "c", "d", "e"]
    print("Client: Strategy is set to normal sorting.")
    print(context.do_some_business_logic(data))

    print("\nClient: Strategy is set to reverse sorting.")
    context.strategy = ConcreteStrategyB()
    print(context.do_some_business_logic(data))
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 想使用对象中各种不同的算法变体，并希望在运行时能够动态切换算法时
- 有许多仅在执行某些行为时略有不同的相似类时
- 如果算法在上下文的逻辑中不是特别重要，使用该模式能将类的业务逻辑与其算法实现细节隔离开来

### 收益

- 可以在运行时切换对象内的算法
- 可以将算法的实现细节与使用算法的代码隔离开来
- 可以使用组合来代替继承
- 开闭原则：无需对上下文进行修改就能够引入新的策略

### 代价

- 如果算法极少发生改变，没有必要引入额外的类和接口让程序变得复杂
- 客户端必须了解不同策略之间的区别才能选择合适的策略

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / strategy](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/behavioral/strategy.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
