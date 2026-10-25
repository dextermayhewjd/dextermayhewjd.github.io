# BaseAdapter

> 2026-10-24 精简前的全字段类卡，完整保留初值、状态例子和记录来源，仅调整相对链接。[当前类卡](../02-short-term-memory/classes/slime/agent/adapters/common.py/BaseAdapter.md)单独维护。

## 1. 对象职责

BaseAdapter 提供模型请求处理与会话生命周期的共同实现。一个 Adapter 实例可以管理多个 `sid`，持有请求状态、轨迹管理器，以及模型调用所需的对象和配置；具体协议由子类补充。

本卡先建立字段的浅层认识，再随阅读补充使用关系。字段说明由助手据源码整理；个人表述与未知单独保留。

## 2. 字段总览

当前基类明确初始化 **13 个实例字段**，另有 **4 个类级默认配置**。下面按职责分组，每个字段只说明保存什么、从哪里来及基本用途。

<a id="session-tracking"></a>

### 2.1 会话与轨迹：实例字段

| 字段 | 保存什么 | 构造时的初始形态或来源 | 基本用途 |
| --- | --- | --- | --- |
| `store` | `sid → Session` 配置对象 | 空字典 `{}` | 按会话保存采样、长度等配置 |
| `inflight` | `sid → 请求 Task 集合` | 空字典 `{}` | 登记请求任务，供会话收尾时查找 |
| `closed` | 已关闭的 `sid` 集合 | 空集合 `set()` | 阻止已关闭会话继续进入新请求 |
| `manager` | `TrajectoryManager` 对象 | 在初始化中创建 | 管理逐轮轨迹，并将轨迹导出为样本 |
| `max_turns_per_sid` | 每个会话的轮数上限 | 构造参数，默认 `None` | 为请求轮数检查提供上限；`None` 表示不启用此项限制 |
| `_sid_turn_count` | `sid → 已计数的请求轮数` | 空字典 `{}` | 在启用上限时记录轮数，供后续检查 |

### 2.2 请求处理与协作对象：实例字段

| 字段 | 保存什么 | 构造时的初始形态或来源 | 基本用途 |
| --- | --- | --- | --- |
| `app` | aiohttp 的 `web.Application` 对象 | 初始化中创建，并注册路由 | 承载 Adapter 的 HTTP 请求入口 |
| `tokenizer` | tokenizer 对象 | 传入的 `tokenizer` | 将消息编码为 token，并解码生成内容 |
| `sglang_url` | 模型生成服务的地址配置 | 传入地址；字符串会去掉末尾 `/` | 为模型请求提供目标地址 |
| `tool_parser` | 工具调用解析器的选择名称 | 构造参数，默认 `None` | 交给输出解析逻辑选择工具调用解析方式 |
| `reasoning_parser` | 思考内容解析器的选择名称 | 构造参数，默认 `None` | 交给输出解析逻辑选择思考内容解析方式 |
| `rollout_args` | 生成相关的配置对象 | 构造参数，默认 `None` | 供生成辅助函数读取额外选项 |
| `debug_callback` | 可调用的调试函数，或 `None` | 构造参数，默认 `None` | 需要时接收本轮调试数据；未设置时跳过 |

`manager`、`app`、`tokenizer` 都是对象引用，内部结构在对应对象的阅读中再展开。`debug_callback` 的值虽然可以是函数，它仍然是 Adapter 持有的字段。

### 2.3 类级默认配置

这些默认值写在类体上，协议子类可以覆盖；它们与前两表在 `__init__` 中建立的实例字段分开列出。

| 字段 | 保存什么 | BaseAdapter 的默认值 | 基本用途 |
| --- | --- | --- | --- |
| `logger` | 日志对象 | `logging.getLogger(__name__)` | 记录请求、限制和异常信息 |
| `log_prefix` | 日志中的标识字符串 | `"adapter"` | 区分日志来自哪类 Adapter |
| `max_token_keys` | 请求中最大生成长度的候选键名 | 空元组 `()` | 按协议从请求正文提取长度限制 |
| `stop_keys` | 请求中停止序列的候选键名 | 空元组 `()` | 按协议从请求正文提取停止条件 |

类体中的 `manager: Any` 是类型注解；实际的 `self.manager` 已计入实例字段。方法参数 `sid` 与局部变量 `tasks`、`pending`、`loop` 不计入这份持久字段清单。

## 3. 已展开的使用关系

当前先保留已经讨论过的 `closed`、`inflight` 用法。其余字段随之后的实际阅读补充；源码总览不直接转成“已学过”的记录。

| 字段 | 使用者 | 具体作用 | 展开位置 |
| --- | --- | --- | --- |
| `closed` | `_run_turn` 进入时 | 检查当前 sid，已关闭时拒绝请求 | [Step 001 方法卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)；源码 `397–399` |
| `inflight` | `_run_turn` 进入时 | 将当前请求 Task 加入对应 sid 的集合 | [Step 001 方法卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)；源码 `406–407` |
| `inflight` | `_run_turn` 退出时 | 从对应集合移除当前 Task | [登记清理段](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#inflight-cleanup)；源码 `475` |
| `closed` | `shutdown_session` | 为当前 sid 添加关闭标记 | [收尾方法卡](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md#shutdown-cross-loop)；源码 `296` |
| `inflight` | `shutdown_session` | 取出当前 sid 的集合，筛选未完成任务 | [收尾方法卡](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md#shutdown-cross-loop)；源码 `297–299` |

<details>
<summary>已讨论字段的状态示例</summary>

教学状态示意，`task_A`、`task_B`、`task_C` 代表已存在的请求 Task：

```python
adapter.closed = {"sid-done"}
adapter.inflight = {
    "sid-demo": {task_A, task_B},
    "sid-other": {task_C},
}
```

- `sid` 是分类用的编号，集合里的 Task 才是正在执行的工作。关闭 `sid-demo` 时取出它的任务集合，`sid-other` 的登记仍保留。
- `inflight` 的某个集合为空，只说明当前没有登记中的请求；会话是否已关闭要看 `closed`。
- 会话配置由 `store` 保存，逐轮轨迹由 `manager` 保存；请求准入与在途登记由上面两个字段管理。

</details>

后续遇到同一用法时复用或修订原条目，遇到新的使用者时补充一行。类卡保留关系摘要与跳转，具体代码、调用过程和结果放在对应方法或函数记录中；使用者也可能是类外函数。

## 4. 我的直接表述（原话）

2026-10-24，用户提出记录归属：

> 我在想这里的这个closed和inflight的内容是否更加适合放在adapter short term中的adapter class里面

这是将对象状态集中到类卡片的提议；此前关于收尾过程的完整复述保存在 [shutdown_session 的原话区](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md#shutdown-user-restatement-2026-10-24)。

随后对类卡写法的补充：

> 那么你觉得是否适合一次性先点亮所有的字段呢?
> 然后简单说一下中间记录的大概是什么 然后如果这个字段之后再被用到了?
> 那么应该考虑的就是把这一部分具体在哪里使用的方式说清楚?
> 你觉得这样子会好很多吗?
>
> 好好考虑一下应该如何写这种short term memory把

以上是记录方式的提议与确认，尚未据此认为所有字段及其用法均已理解。

## 5. 尚不清楚

- `sid` 与请求 Task 的区别、字段中保存的具体对象，仍需结合本轮复述核对。
- 同一 Adapter 的请求为何共用事件循环，以及 `run_coroutine_threadsafe` 怎样提交收尾协程，仍在当前函数问题中继续澄清。
- 已列出字段全景；其余字段的实际使用细节、协议子类的覆盖方式和完整初始化过程，尚未在本轮逐项阅读。

## 6. 来源

<details>
<summary>源码版本、记录来路与验证范围</summary>

- 固定源码：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本机 `/home/fredkeira/projects/slime`。
- [类声明与实例初始化](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L190-L240)：13 个实例字段与 4 个类级默认配置的定义依据。
- [会话配置登记与收尾](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L312)、[轮数检查与调试回调](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L354-L385)、[请求处理中的取用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L394-L475)。
- [生成辅助函数读取 Adapter 配置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L524-L576)；[Anthropic 子类覆盖类属性](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L42-L46)。上述位置用于核对字段用途，不代表本轮展开了所有函数。
- 首次接触：此前已通过 Adapter 的方法接触；2026-10-24 在 Step 004 建立独立类卡片，归并会话状态的说明。
- 最近认识更新：暂无对本类状态的独立技术复述；本次保存用户的记录归属提议，字段含义由助手据源码整理。
- 2026-10-24：按用户确认扩展为全字段总览与渐进用法索引。[先前的两字段类卡](base-adapter-before-field-overview.md)保留当时范围，[格式讨论与确认](../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#class-field-memory-applied)保存本次调整依据。
- [原 inflight 状态推演](inflight.md)和 [sid 说明](session-id.md)保留历史依据。本轮为静态源码核对与记录整理，没有运行真实 HTTP 请求，也不新增个人掌握结论。

</details>
