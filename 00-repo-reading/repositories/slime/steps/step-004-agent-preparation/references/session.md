# Session：类卡片入口与语法参考

主体说明已整理为正式的 [Session 类卡片](../02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md)，包括构造输入、实例字段、per-session state 的含义及与 sid 的关联。本页保留原链接入口和补充语法依据。

[返回 open_session 函数卡片](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md) · [session_id 的含义](../../step-003-trajectory-to-samples/references/session-id.md) · [本轮确认与原始来源](../../step-004-agent-preparation/04-flow.md#session-class-card)

<a id="session-dataclass-syntax"></a>

<details>
<summary>Python 语法依据：dataclass 与默认字典</summary>

**书上怎么说**

- 声明的字段会成为自动生成的 `__init__` 的参数。[依据 A]
- `default_factory` 提供创建默认值的可调用对象，使不同实例可以拥有各自的可变默认值。[依据 A]

**我的判断（本书未覆盖）**

- Session 的两项字段、sid 存在 store 的键上，以及类卡片与函数卡片的分工，依据 Slime 源码与当前阅读约定，不是本书对 Slime 的结论。

**依据 A**：第 5 章，Field Options / 5.6.1 字段选项，锚点 `field-options`。英文 `corpus/en/ch05.md:682–786`，中文 `corpus/zh/ch05.md:769–874`；《Fluent Python》第 2 版基于 Python 3.10，本轮环境为 Python 3.12.3。

- 原文：The instance fields you declare will become parameters in the generated `__init__`.
- 对照：声明的字段将作为参数传给生成的 `__init__` 方法。
- 原文：The `default_factory` parameter lets you provide a function, class, or any other callable, which will be invoked with zero arguments to build a default value each time an instance of the data class is created.
- 对照：`default_factory` 参数的值可以是一个函数、一个类，或者其他可调用对象，在每次创建数据类的实例时调用（不带参数），构建默认值。

本地语料根目录：`/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/`。这里只用于核对本页的必要语法，不展开数据类的其他机制。

</details>
