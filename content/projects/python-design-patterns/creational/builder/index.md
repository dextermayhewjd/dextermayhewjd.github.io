---
title: "建造者 · Builder"
description: "把复杂对象的配置和构造组织清楚。"
weight: 30
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [创建型](../)

## 1. 要解决什么问题

**使用心智模型：数据对象保存结果，Builder 组织逐步构建结果的过程。**

本例中，`Query` 保存表名、字段、筛选条件和数量限制；`QueryBuilder` 用 `from_table()`、`select()`、`where()`、`take()` 逐步填写它。

创建 Builder 时先创建 Query → 设置方法修改它，并返回 Builder 自己以便继续调用 → `build()` 交出这个 Query。这里不会执行数据库查询。

使用 dataclass 并不意味着必须配一个 Builder；也可以直接写 `Query(...)`。Builder 提供的是组织逐步配置过程的一种方式。

复杂对象包含大量字段和可选配置，导致构造函数参数爆炸（重叠构造函数/伸缩构造函数），许多参数传 None 或默认值，可读性和维护性极差。

## 2. 在 Python 中怎样表达

QueryBuilder 保存 Query，用 from_table、select、where、take 逐步填写查询描述。Self 表示设置方法返回当前建造者类型，build 最后返回 Query。

**运行前先观察：**每一步修改 Query 的哪个字段，build 返回建造者还是查询描述？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Builder - Python 3.12+ Example: typing.Self Fluent Builder
"""
from dataclasses import dataclass, field
from typing import Self


@dataclass
class Query:
    table: str = ""
    fields: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    limit: int | None = None


class QueryBuilder:
    def __init__(self) -> None:
        self._query = Query()

    def from_table(self, table: str) -> Self:
        self._query.table = table
        return self

    def select(self, *fields: str) -> Self:
        self._query.fields.extend(fields)
        return self

    def where(self, condition: str) -> Self:
        self._query.filters.append(condition)
        return self

    def take(self, count: int) -> Self:
        self._query.limit = count
        return self

    def build(self) -> Query:
        # 交出内部的查询描述对象；这里不重新创建，也不执行查询。
        return self._query


if __name__ == "__main__":
    q = (
        QueryBuilder()
        .from_table("users")
        .select("id", "email")
        .where("active = 1")
        .take(5)
        .build()
    )
    print(f"Built Query: {q}")
```

运行输出：

```text
Built Query: Query(table='users', fields=['id', 'email'], filters=['active = 1'], limit=5)
```

## 4. 使用边界

本例只收集查询描述，不执行 SQL，也不生成安全的参数化 SQL。Builder 与 yield 生成器是不同概念。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Builder - Python 3.10+ Example: Dataclass with kw_only & Fluent Builder
"""
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class ServerConfig:
    host: str = "localhost"
    port: int = 8080
    ssl_enabled: bool = False
    workers: int = 4
    middlewares: list[str] = field(default_factory=list)
    timeout: float | None = 30.0


class ServerConfigBuilder:
    def __init__(self) -> None:
        self._config = ServerConfig()

    def with_host(self, host: str) -> "ServerConfigBuilder":
        self._config.host = host
        return self

    def with_port(self, port: int) -> "ServerConfigBuilder":
        self._config.port = port
        return self

    def enable_ssl(self) -> "ServerConfigBuilder":
        self._config.ssl_enabled = True
        return self

    def add_middleware(self, name: str) -> "ServerConfigBuilder":
        self._config.middlewares.append(name)
        return self

    def build(self) -> ServerConfig:
        return self._config


if __name__ == "__main__":
    # Direct keyword-only instantiation (simplifies parameter explosion)
    cfg1 = ServerConfig(host="0.0.0.0", port=443, ssl_enabled=True)
    print(f"Direct kw_only config: {cfg1}")

    # Fluent builder when step-by-step assembly is needed
    cfg2 = (
        ServerConfigBuilder()
        .with_host("api.internal")
        .with_port(9000)
        .add_middleware("auth")
        .add_middleware("rate_limiter")
        .build()
    )
    print(f"Fluent built config: {cfg2}")
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Builder - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod
from typing import Any


class Product1:
    def __init__(self) -> None:
        self.parts: list[Any] = []

    def add(self, part: Any) -> None:
        self.parts.append(part)

    def list_parts(self) -> str:
        return f"Product parts: {', '.join(self.parts)}"


class Builder(ABC):
    @property
    @abstractmethod
    def product(self) -> Product1:
        pass

    @abstractmethod
    def produce_part_a(self) -> None:
        pass

    @abstractmethod
    def produce_part_b(self) -> None:
        pass

    @abstractmethod
    def produce_part_c(self) -> None:
        pass


class ConcreteBuilder1(Builder):
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._product = Product1()

    @property
    def product(self) -> Product1:
        product = self._product
        self.reset()
        return product

    def produce_part_a(self) -> None:
        self._product.add("PartA1")

    def produce_part_b(self) -> None:
        self._product.add("PartB1")

    def produce_part_c(self) -> None:
        self._product.add("PartC1")


class Director:
    def __init__(self) -> None:
        self._builder: Builder | None = None

    @property
    def builder(self) -> Builder:
        assert self._builder is not None
        return self._builder

    @builder.setter
    def builder(self, builder: Builder) -> None:
        self._builder = builder

    def build_minimal_viable_product(self) -> None:
        self.builder.produce_part_a()

    def build_full_featured_product(self) -> None:
        self.builder.produce_part_a()
        self.builder.produce_part_b()
        self.builder.produce_part_c()


if __name__ == "__main__":
    director = Director()
    builder = ConcreteBuilder1()
    director.builder = builder

    print("Standard basic product:")
    director.build_minimal_viable_product()
    print(builder.product.list_parts())

    print("Standard full featured product:")
    director.build_full_featured_product()
    print(builder.product.list_parts())
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 使用生成器模式可避免“重叠构造函数（telescoping constructor）”的出现
- 希望使用代码创建不同形式的产品时（例如不同格式的报告、SQL 查询）
- 构建复杂的组合树对象或其他复杂对象时

### 收益

- 可以分步创建对象，暂缓创建步骤或递归运行创建步骤
- 生成不同形式的产品时可以复用相同的制造代码
- 单一职责原则：将复杂构造代码与产品的业务逻辑分离

### 代价

- 由于该模式需要创建多个新类，代码整体复杂性会有所增加

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / builder](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/creational/builder.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
