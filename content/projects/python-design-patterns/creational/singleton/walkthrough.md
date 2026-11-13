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
