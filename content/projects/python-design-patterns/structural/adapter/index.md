---
title: "适配器 · Adapter"
description: "把现有接口转换为调用方期待的接口。"
weight: 10
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [结构型](../)

## 1. 要解决什么问题

**使用心智模型：Adapter 是接口转换桥，复用旧服务，对外提供调用方需要的接口和数据格式。**

当需要接入第三方库、遗留代码或具有不兼容接口的系统时，直接改动现有业务代码会破坏已有架构且难以维护。

## 2. 在 Python 中怎样表达

XMLToDictAdapter 保存 XMLService 和一个转换函数，将 get_xml_payload 的字符串结果转换成调用方需要的字典。Converter[In, Out] 用 type 声明转换函数的输入输出类型。

**运行前先观察：**调用方要的接口是什么，适配器把原服务的返回值转换成了什么？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Adapter - Python 3.12+ Example: PEP 695 Generic Adapter & @override
"""
from collections.abc import Callable
from typing import Protocol

type Converter[In, Out] = Callable[[In], Out]


class DataSource(Protocol):
    def fetch_raw_data(self) -> dict[str, str]: ...


class XMLService:
    def get_xml_payload(self) -> str:
        return "<record><id>101</id><name>Alice</name></record>"


class XMLToDictAdapter[T: XMLService]:
    def __init__(self, service: T, parser: Converter[str, dict[str, str]]) -> None:
        self._service = service
        self._parser = parser

    def fetch_raw_data(self) -> dict[str, str]:
        # 从已有服务取出 XML 字符串，再交给转换函数。
        raw = self._service.get_xml_payload()
        return self._parser(raw)


if __name__ == "__main__":
    adapter = XMLToDictAdapter(
        XMLService(),
        lambda xml: {"parsed": xml.replace("<", "[").replace(">", "]")},
    )
    print(f"Adapted output: {adapter.fetch_raw_data()}")
```

运行输出：

```text
Adapted output: {'parsed': '[record][id]101[/id][name]Alice[/name][/record]'}
```

### 3.1 Adapter 具体在适配什么？ {#adapter-role}

**使用心智模型：保留旧服务，在外面接一个转换层，让它能按调用方期待的方法和数据格式工作。**

| 位置 | 方法与数据 |
| --- | --- |
| 旧服务 XMLService | `get_xml_payload()` 返回 XML 字符串 |
| 调用方期望的 DataSource 接口 | `fetch_raw_data()` 返回字典 |
| XMLToDictAdapter | 提供新接口，内部调用旧服务，再把结果交给 parser 转换 |

真正的适配行为是主例中的两行：

```python
raw = self._service.get_xml_payload()  # 按旧服务的接口拿到字符串。
return self._parser(raw)  # 把字符串转换成调用方需要的字典。
```

适配器不重新实现旧服务，也不负责生成这份原始 XML。它封装了方法调用和格式转换，使调用方只需面对 `fetch_raw_data()`。

`DataSource` 只描述调用方期望的接口；`Converter[In, Out]` 和 `T` 描述类型。真正工作的仍是上面两次函数调用。

### 3.2 用具名函数做真正的字段解析 {#adapter-parse-record}

原例的 lambda 只替换尖括号，再把整段文本放进 `parsed` 字段，适合作为类型转换演示，但不容易看出 XML 数据的实际用途。

更直观的使用方式是：**保留主例的类定义，把转换函数换成解析字段的 `parse_record`。** 下面是补充用法，不改动本地项目的原始主例：

```python
from xml.etree import ElementTree


def parse_record(xml: str) -> dict[str, str]:
    root = ElementTree.fromstring(xml)  # 将 XML 字符串解析成元素树。
    return {child.tag: child.text or "" for child in root}  # 取第一层子元素的名称和文本。


source: DataSource = XMLToDictAdapter(XMLService(), parse_record)
record = source.fetch_raw_data()  # 调用方使用期望的接口，得到字典。
print(record)
print(record["name"])
```

输出：

```text
{'id': '101', 'name': 'Alice'}
Alice
```

现在可以看清完整关系：旧服务给 XML，适配器调用解析函数，调用方得到可按字段读取的字典。更换转换函数，不需要修改 XMLService 或 XMLToDictAdapter 的实现。

这个 parse_record 只处理本例“一层 record 子元素都是文本”的结构，不是通用 XML 转字典算法。复杂嵌套、重复标签等数据需要按实际接口约定处理。

**一句话：Adapter 让调用方不必迁就旧接口，由转换层负责连接两边的差异。**

## 4. 使用边界

先明确两边的接口差异。本例 parser 只是字符串替换演示，并不是完整的 XML 解析器；真正接入时要换成符合数据协议的解析函数。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Adapter - Python 3.10+ Example: Protocol-based Structural Adapter & Callables
"""
from collections.abc import Callable
from typing import Protocol


class PaymentProcessor(Protocol):
    def process_payment(self, amount_cents: int) -> str: ...


class ModernStripeService:
    def charge(self, total_dollars: float, currency: str = "USD") -> dict[str, str]:
        return {"status": "success", "id": "tx_9988"}


class StripeAdapter:
    def __init__(self, service: ModernStripeService) -> None:
        self._service = service

    def process_payment(self, amount_cents: int) -> str:
        res = self._service.charge(amount_cents / 100.0)
        return f"Paid via Modern Stripe: {res['id']}"


def pay_with_fn(amount_cents: int, gateway: Callable[[float], str]) -> str:
    return gateway(amount_cents / 100.0)


if __name__ == "__main__":
    adapter: PaymentProcessor = StripeAdapter(ModernStripeService())
    print(adapter.process_payment(5000))
    # Functional adaptation
    res = pay_with_fn(3500, lambda amt: f"Lambda adapted: ${amt:.2f}")
    print(res)
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Adapter - Conceptual Example (Classic GoF)
"""


class Target:
    def request(self) -> str:
        return "Target: The default target's behavior."


class Adaptee:
    def specific_request(self) -> str:
        return ".eetpadA eht fo roivaheb laicepS"


class Adapter(Target):
    def __init__(self, adaptee: Adaptee) -> None:
        self.adaptee = adaptee

    def request(self) -> str:
        return f"Adapter: (TRANSLATED) {self.adaptee.specific_request()[::-1]}"


def client_code(target: Target) -> str:
    return target.request()


if __name__ == "__main__":
    target = Target()
    print(client_code(target))

    adaptee = Adaptee()
    adapter = Adapter(adaptee)
    print(client_code(adapter))
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 当你希望使用某个现有类，但其接口与其他代码不兼容时
- 当你希望复用几个现有的子类，这些子类缺少某些通用功能，且无法添加到超类中时

### 收益

- 单一职责原则：可以将接口或数据转换代码从主要业务逻辑中分离
- 开闭原则：只要客户端代码通过客户端接口与适配器进行交互，就能在不修改现有代码的情况下添加新的适配器

### 代价

- 代码整体复杂度增加，需要引入一系列新的接口和类

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / adapter](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/structural/adapter.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
