---
title: "代理 · Proxy"
description: "在访问真实对象时加入控制。"
weight: 70
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [结构型](../)

## 1. 要解决什么问题

**在访问真实对象时加入控制。**

当需要对一个重量级对象执行延迟初始化（Lazy Loading）、访问权限控制、网络通信封装或对结果进行缓存时，直接修改原服务类会混杂非核心职责，且客户端无从得知调用时机。

## 2. 在 Python 中怎样表达

LazyProxy[T] 保存一个返回 T 的工厂，第一次读取 target 时创建 HeavyResource，后续读取复用同一个目标；get_data 再调用目标的 fetch_data。

**运行前先观察：**创建 LazyProxy 与第一次 get_data 时，哪一步真正创建 HeavyResource？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Proxy - Python 3.12+ Example: PEP 695 Generic Lazy Proxy
"""
from collections.abc import Callable


class HeavyResource:
    def fetch_data(self) -> str:
        return "Heavy payload data loaded"


class LazyProxy[T]:
    def __init__(self, factory: Callable[[], T]) -> None:
        self._factory = factory
        self._target: T | None = None

    @property
    def target(self) -> T:
        if self._target is None:
            # 第一次读取 target 时创建对象，后续读取复用。
            self._target = self._factory()
        return self._target

    def get_data(self) -> str:
        return getattr(self.target, "fetch_data")()


if __name__ == "__main__":
    proxy: LazyProxy[HeavyResource] = LazyProxy(HeavyResource)
    print("Proxy initialized without loading heavy resource.")
    print(proxy.get_data())
```

运行输出：

```text
Proxy initialized without loading heavy resource.
Heavy payload data loaded
```

## 4. 使用边界

这是受控接口的懒加载示例，并非完整透明代理。工厂的返回类型 T 不自动保证存在 fetch_data 方法，接入其他对象时仍需核对接口。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Proxy - Python 3.10+ Example: Dynamic Delegation Proxy & Lazy Loading
"""
from collections.abc import Callable
from typing import Any


class HeavyDatabaseService:
    def __init__(self) -> None:
        print("[DB] Initializing heavy connection pool...")

    def query(self, sql: str) -> str:
        return f"Results for: {sql}"


class LazyProxy:
    def __init__(self, factory: Callable[[], Any]) -> None:
        self._factory = factory
        self._instance: Any | None = None

    def _get_target(self) -> Any:
        if self._instance is None:
            self._instance = self._factory()
        return self._instance

    def __getattr__(self, name: str) -> Any:
        target = self._get_target()
        return getattr(target, name)


if __name__ == "__main__":
    proxy = LazyProxy(HeavyDatabaseService)
    print("Proxy created (DB not yet connected)")
    print(proxy.query("SELECT * FROM users"))
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Proxy - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class Subject(ABC):
    @abstractmethod
    def request(self) -> str:
        pass


class RealSubject(Subject):
    def request(self) -> str:
        return "RealSubject: Handling request."


class Proxy(Subject):
    def __init__(self, real_subject: RealSubject) -> None:
        self._real_subject = real_subject

    def request(self) -> str:
        if self.check_access():
            result = self._real_subject.request()
            self.log_access()
            return f"Proxy: {result}"
        return "Proxy: Access denied."

    def check_access(self) -> bool:
        print("Proxy: Checking access prior to firing a real request.")
        return True

    def log_access(self) -> None:
        print("Proxy: Logging the time of request.")


def client_code(subject: Subject) -> str:
    return subject.request()


if __name__ == "__main__":
    real_subject = RealSubject()
    print("Client: Executing the client code with a real subject:")
    print(client_code(real_subject))

    proxy = Proxy(real_subject)
    print("\nClient: Executing the same client code with a proxy:")
    print(client_code(proxy))
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 延迟初始化（虚拟代理）：有一个偶尔使用的重量级服务对象，无需一直占用内存
- 访问控制（保护代理）：只希望特定客户端使用服务对象，代理可验证凭据
- 本地执行远程服务（远程代理）：服务对象位于远程服务器上
- 记录日志与请求缓存（日志记录与缓存代理）：缓存客户端请求结果以降低服务负载

### 收益

- 可以在客户端毫无察觉的情况下控制服务对象
- 如果客户端对服务对象的生命周期没有特殊要求，可以由代理全权管理
- 即使服务对象还未准备好或不可用，代理依然可以运作
- 开闭原则：无需修改服务或客户端就能引入新代理

### 代价

- 代码可能会变得更复杂，因为需要引入大量新类
- 服务响应可能会产生延迟

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / proxy](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/structural/proxy.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
