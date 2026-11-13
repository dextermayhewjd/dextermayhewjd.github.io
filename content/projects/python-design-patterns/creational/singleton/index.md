---
title: "单例 · Singleton"
description: "让调用方复用同一个实例。"
weight: 50
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [创建型](../)

## 1. 要解决什么问题

**让调用方复用同一个实例。**

某些系统资源（例如全局配置、日志服务或数据库连接池）在整个生命周期内必须只能存在一个实例，多个实例会导致状态冲突或资源竞争。

## 2. 在 Python 中怎样表达

ServiceRegistry 在类属性 _instance 中保存实例，get_instance 第一次创建、后续返回保存的对象；Self 描述返回当前类的实例。

**运行前先观察：**为什么 registry1 is registry2 为真，实例引用保存在什么位置？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Singleton - Python 3.12+ Example: Generic Singleton Container & typing.Self
"""
from typing import Self


class ServiceRegistry:
    _instance: Self | None = None

    @classmethod
    def get_instance(cls) -> Self:
        if cls._instance is None:
            # 首次获取时创建，并把实例引用保存在类属性中。
            cls._instance = cls()
        return cls._instance

    def ping(self) -> str:
        return "pong"


if __name__ == "__main__":
    registry1 = ServiceRegistry.get_instance()
    registry2 = ServiceRegistry.get_instance()
    print(f"Registry shared: {registry1 is registry2}, response: {registry1.ping()}")
```

运行输出：

```text
Registry shared: True, response: pong
```

### 3.1 为什么 get_instance 要写成 classmethod？ {#singleton-classmethod}

**普通方法通常操作一个已有实例；这里的类方法负责从类这一层取得实例。** 方法写在 class 里面，并不自动意味着它是 classmethod。

| 调用 | Python 自动传入的第一个参数 | 操作对象 |
| --- | --- | --- |
| `registry1.ping()` | `self`，即 registry1 这个实例 | 某个已经存在的实例 |
| `ServiceRegistry.get_instance()` | `cls`，即 ServiceRegistry 这个类 | 类本身及其保存的实例引用 |

`self`、`cls` 是惯用参数名；决定第二行如何自动传参的是 `@classmethod`，不是把参数叫作 cls。

<details id="classmethod-entry">
<summary>为什么“取得实例”这个入口适合放在类上？</summary>

调用 `ServiceRegistry.get_instance()` 时，调用方可能还没有任何 ServiceRegistry 实例，但类本身已经存在。

如果按普通实例方法的调用方式，就需要先有 `registry1`，才能调用 `registry1.get_instance()`。这不适合作为取得初始实例的入口。

类方法允许调用方直接从类开始：先检查类里保存了什么，再决定创建还是复用。它是本例的组织方式，不代表所有创建对象的函数都必须使用 classmethod。

</details>

<details id="classmethod-cls">
<summary>cls、cls() 和 cls._instance 分别是什么？</summary>

在本次 `ServiceRegistry.get_instance()` 调用中：

| 表达式 | 意思 |
| --- | --- |
| `cls` | ServiceRegistry 类本身 |
| `cls()` | 调用这个类，创建一个 ServiceRegistry 实例 |
| `cls._instance` | 读取这个类保存的实例引用，初始为 None |

因此原方法做的是：

```python
if cls._instance is None:  # 类里尚未保存实例。
    cls._instance = cls()  # 创建实例，并把引用保存到类属性。
return cls._instance  # 第一次和后续调用都从这里取得保存的对象。
```

**classmethod 只负责让方法接收类，不负责自动实现单例。** 创建一次、以后复用，是这段检查和保存逻辑产生的行为。

</details>

## 4. 使用边界

本例通过 get_instance 复用实例；直接调用 ServiceRegistry() 仍会新建对象。类属性不跨进程共享，首次并发初始化也没有加锁。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

此原例使用函数缓存，主例使用类属性。原例 docstring 中关于并发首次初始化的表述已修正，执行逻辑不变。

```python
"""
Singleton - Python 3.10+ Example: Module-level instance / @lru_cache factory
"""
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class AppSettings:
    app_name: str = "ModernApp"
    debug: bool = False
    env_vars: dict[str, str] = field(default_factory=dict)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Cache settings for reuse; concurrent first calls may create multiple instances."""
    return AppSettings()


if __name__ == "__main__":
    s1 = get_settings()
    s2 = get_settings()
    s1.debug = True
    print(f"Singleton identical: {s1 is s2}, debug={s2.debug}")
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Singleton - Conceptual Example: Metaclass Implementation (Classic GoF)
"""
from typing import Any


class SingletonMeta(type):
    _instances: dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Singleton(metaclass=SingletonMeta):
    def some_business_logic(self) -> str:
        return "Executing singleton operation"


if __name__ == "__main__":
    s1 = Singleton()
    s2 = Singleton()
    print("Same instance:", s1 is s2)
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 如果程序中的某个类对于所有客户端只有一个可用的实例（如共享数据库连接、系统配置）
- 需要严格控制全局变量，防止它们被任意随处重写时

### 收益

- 可以保证一个类只有一个实例
- 获得指向该实例的全局访问节点
- 仅在首次请求单例对象时对其进行延迟初始化

### 代价

- 违反了单一职责原则（同时负责自身业务逻辑与控制自身生命周期）
- 在多线程环境下需要特殊处理，且单元测试较难进行 Mock

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / singleton](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/creational/singleton.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
