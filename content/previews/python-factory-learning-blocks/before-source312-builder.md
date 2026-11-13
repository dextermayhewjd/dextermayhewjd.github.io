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

**这里的 Builder 用一组可以连续调用的方法逐步设置配置，最后通过 `build()` 交出配置好的对象。**

**使用心智模型：**创建建造者 → 用 `with_host()`、`with_port()` 等方法逐步配置 → 用 `build()` 取出 `ServerConfig`。中间方法返回建造者本身，方便继续调用；`build()` 返回配置对象。本例的配置对象在建造者初始化时就已创建。

复杂对象包含大量字段和可选配置，导致构造函数参数爆炸（重叠构造函数/伸缩构造函数），许多参数传 None 或默认值，可读性和维护性极差。

## 2. 在 Python 中怎样表达

主例子先用具名参数创建 ServerConfig，再展示 ServerConfigBuilder 的逐步设置。方法返回 self，Self 注解说明返回的是当前建造者类型。

**运行前先观察：**直接创建 cfg1 与逐步构建 cfg2 各设置了哪些字段，build 最后返回了什么？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

这一主例沿用先前的业务场景，更新为 Python 3.12 的类型写法；变化以类型表达为主，创建与调用关系保持一致。

```python
"""Builder - Python 3.12, preserving the ServerConfig teaching scenario."""

from dataclasses import dataclass, field
from typing import Self


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

    def with_host(self, host: str) -> Self:
        self._config.host = host
        return self  # Self 表示返回当前建造者类型，继续链式调用。

    def with_port(self, port: int) -> Self:
        self._config.port = port
        return self

    def enable_ssl(self) -> Self:
        self._config.ssl_enabled = True
        return self

    def add_middleware(self, name: str) -> Self:
        self._config.middlewares.append(name)
        return self

    def build(self) -> ServerConfig:
        return self._config  # 交出已有配置，不复制或重置。


if __name__ == "__main__":
    cfg1 = ServerConfig(host="0.0.0.0", port=443, ssl_enabled=True)
    print(f"Direct kw_only config: {cfg1}")
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

运行输出：

```text
Direct kw_only config: ServerConfig(host='0.0.0.0', port=443, ssl_enabled=True, workers=4, middlewares=[], timeout=30.0)
Fluent built config: ServerConfig(host='api.internal', port=9000, ssl_enabled=False, workers=4, middlewares=['auth', 'rate_limiter'], timeout=30.0)
```

## 4. 使用边界

Builder 在这里译为建造者。Python 的生成器（generator / yield）是另一种概念；仅靠 dataclass 也不等于实现了完整的建造者模式。

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
<summary>本地项目的另一份 Python 3.12 原例</summary>

这份原例使用另一业务场景，作为可选参考；上方主例继续沿用已经讨论的对象与接口。

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

本站保留已讨论的业务场景，迁移为 Python 3.12 的类型表达。工厂主例继续使用具名函数；抽象工厂使用泛型 Protocol，Builder 与 Prototype 使用 Self。对应的两份原例保留在本页对照区。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
