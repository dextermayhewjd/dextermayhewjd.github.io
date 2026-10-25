# HarnessContext 的 Python 语法依据

本次主记录在 [HarnessContext 类卡片](../02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)。这里仅保存语言依据，字段的业务含义以 Slime 源码为准。

## 书上怎么说

1. `@dataclass` 的 `init` 默认值为 `True`，用于生成 `__init__`；用户已经实现初始化方法时不生成。见依据 A 的参数表。
2. `frozen=True` 用于防止意外更改实例，不应解释为无法绕过的绝对不可变。见依据 A。

## 我的判断（本书未覆盖）

- Slime 的 `HarnessContext` 没有自定义初始化方法，构造参数对应三个必填字段及一个有默认值的字段；这由项目源码与本地构造结果确认。
- `ctx` 的地址和编号如何进入 CLI 环境变量，是 `ClaudeCodeHarness.launch_and_wait` 的业务行为，不是 dataclass 自动完成的功能。
- 本例四个字段均为字符串；当前只需理解字段读取、默认值与普通赋值限制，不展开其他 dataclass 功能。

## 依据

A · 《Fluent Python》第 2 版，第 5 章，More About @dataclass / 5.6 @dataclass 详解。

- 英文：[corpus/en/ch05.md](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/en/ch05.md:621)，**621–681 行**，锚点 `more-about-dataclass`。
- 中文：[corpus/zh/ch05.md](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/zh/ch05.md:684)，**684–768 行**，同一锚点。
- 版本：本书基于 Python 3.10；本次运行环境为 Python 3.12.3。这里只使用两者共有的 `init` 与 `frozen` 行为，并已在本地验证。

参数表原文节选：

> `init` Generate `__init__` `True` Ignored if `__init__` is implemented by user.

中文表格对应单元格节选（原文排版拆行）：

> `init` 生成 `__init__` `True`

`frozen=True` 的解释原文：

> Protects against accidental changes to the class instances.

官方中文译文：

> 防止意外更改类的实例。

## 本地验证

仅用 AST 提取 `harness/common.py` 的原始 `HarnessContext` 类定义，提供标准库 `dataclass`，未执行模块的其他代码。在 Python 3.12.3 中输入卡片中的三个参数，得到：

```text
HarnessContext(workdir='/workspace/auth0-python', session_id='sid-demo', adapter_url='http://adapter-host:18001', model_label='slime-actor')
```

`dataclasses.fields` 确认字段为 `workdir`、`session_id`、`adapter_url`、`model_label`；普通赋值 `ctx.session_id = 'another-session'` 抛出 `FrozenInstanceError`。没有访问示例地址、启动沙箱或请求模型。
