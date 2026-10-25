# BaseAdapter

## 1. 对象职责

一个 Adapter 实例处理多个 `sid` 的模型请求，管理其会话状态与轨迹；协议细节由子类补充。

**本轮关注：** `closed`、`inflight`；收尾后再接 `store`、`manager`。

## 2. 字段总览

13 个实例字段与 4 个类级配置。“—”表示本卡尚未归纳该字段的具体用法，后续在同一行补充。

<a id="session-tracking"></a>

### 2.1 会话与轨迹：实例字段

| 字段 | 含义 | 已展开的用法 |
| --- | --- | --- |
| `store` | `sid → Session` 配置表；初始 `{}` | [finish_session](../../../../../functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md#session-close-and-config)取出配置，读取导出长度上限 |
| `inflight` | `sid → set[Task]` 当前请求登记表；初始 `{}` | [`_run_turn`](../../../../../../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#inflight-cleanup)登记请求、退出时移除；[shutdown_session](../../../../../functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md#shutdown-cross-loop)按 `sid` 取出并筛选未完成任务 |
| `closed` | 已关闭的 `sid` 集合，用于拒绝新请求；初始 `set()` | [`_run_turn` 入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L397-L399)检查；[shutdown_session](../../../../../functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md#shutdown-cross-loop)添加关闭标记 |
| `manager` | 新建的 `TrajectoryManager` 对象，保存轨迹并导出样本 | [finish_session](../../../../../functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md)委托 [get_trajectory](../../../../../functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)按 sid 导出轨迹、赋奖励并移除记录 |
| `max_turns_per_sid` | 单个会话的轮数上限；默认 `None` 表示不启用 | — |
| `_sid_turn_count` | 按 `sid` 记录已计数轮数，供上限检查；初始 `{}` | — |

### 2.2 请求处理：实例字段

| 字段 | 含义 | 已展开的用法 |
| --- | --- | --- |
| `app` | 初始化中创建的 HTTP 应用，承载路由 | — |
| `tokenizer` | 传入的编解码对象，负责消息与 token 的转换 | [finish_session](../../../../../functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md)解码样本响应区，补上 response |
| `sglang_url` | 传入的模型服务地址配置 | — |
| `tool_parser` | 工具调用解析器名称；默认 `None` | — |
| `reasoning_parser` | 思考内容解析器名称；默认 `None` | — |
| `rollout_args` | 生成配置，如续生成、重放选项；默认 `None` | — |
| `debug_callback` | 可选的调试回调；默认 `None` | — |

### 2.3 类级默认配置：子类可覆盖

| 字段 | 含义 | 已展开的用法 |
| --- | --- | --- |
| `logger` | 日志对象；默认 `logging.getLogger(__name__)` | — |
| `log_prefix` | 日志标识；默认 `"adapter"` | — |
| `max_token_keys` | 请求中长度限制的候选键名；默认 `()` | — |
| `stop_keys` | 请求中停止序列的候选键名；默认 `()` | — |

`manager: Any` 只是类型注解，不另算一个字段。`sid`、`tasks`、`pending`、`loop` 是方法参数或局部变量。

## 3. 我的直接表述（原话）

现有原话主要是记录方式的选择，完整保留在下方。

<details>
<summary>记录方式的原话与来由</summary>

2026-10-24，用户提出记录归属：

> 我在想这里的这个closed和inflight的内容是否更加适合放在adapter short term中的adapter class里面

这是将对象状态集中到类卡片的提议；此前关于收尾过程的完整复述保存在 [shutdown_session 的原话区](../../../../../functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md#shutdown-user-restatement-2026-10-24)。

随后对类卡写法的补充：

> 那么你觉得是否适合一次性先点亮所有的字段呢?
> 然后简单说一下中间记录的大概是什么 然后如果这个字段之后再被用到了?
> 那么应该考虑的就是把这一部分具体在哪里使用的方式说清楚?
> 你觉得这样子会好很多吗?
>
> 好好考虑一下应该如何写这种short term memory把

以上是记录方式的提议与确认，尚未据此认为所有字段及其用法均已理解。

</details>

## 4. 尚不清楚

- `sid` 与请求 Task 的区别、字段中保存的具体对象，仍需结合本轮复述核对。
- 同一 Adapter 的请求为何共用事件循环，以及 `run_coroutine_threadsafe` 怎样提交收尾协程，仍在当前函数问题中继续澄清。
- 已列出字段全景；其余字段的实际使用细节、协议子类的覆盖方式和完整初始化过程，尚未在本轮逐项阅读。

## 5. 来源

<details>
<summary>源码版本、历史与构造细节</summary>

- 固定版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本机 `/home/fredkeira/projects/slime`。
- [字段定义与初始化](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L190-L240)、[会话方法](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L385)、[请求处理](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L394-L475)。
- [生成辅助函数取用配置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L524-L576)、[Anthropic 子类的默认值](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L42-L46)。
- 首次接触：此前已通过 Adapter 的方法接触；2026-10-24 在 Step 004 建立独立类卡片，归并会话状态的说明。
- 最近认识更新：暂无对本类状态的独立技术复述；本次保存用户的记录归属提议，字段含义由助手据源码整理。
- [精简前的完整类卡](../../../../../../../step-004-trajectory-to-samples/references/base-adapter-before-slimming.md)保存构造细节、状态例子与早期来源；[本轮调整记录](../../../../../../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#base-adapter-card-slimming)保存取舍。字段说明经过静态源码核对，不代表新增个人掌握或实际运行结果。

</details>
