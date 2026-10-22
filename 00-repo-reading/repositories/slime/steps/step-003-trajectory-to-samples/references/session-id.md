# sid：标识 Agent 对一道题的一次执行

[返回 shutdown_session](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md) · [接着阅读 inflight](inflight.md)

这份说明先回答“sid 究竟标识什么”。以下为助手按固定源码整理的解释；当前请求怎样登记和收尾，接着在 inflight 说明中阅读。

<a id="what-session-identifies"></a>

## 这里的“会话”具体是哪件事

**在当前 Coding Agent 路径里，一个 `sid` 标识 Agent 对某道题的一次独立执行。** 这次执行可以包含很多轮模型请求和工具操作，最后结束并收集结果。“会话编号”就是给这一次执行取一个名字，方便不同组件把属于它的状态找回来。

把用户问到的几个对象放到一起：

| 对象 | 它回答什么问题 | 与 sid 的关系 |
| --- | --- | --- |
| `instance_id` | 正在解决哪一道题？ | 同一道题可以独立尝试多次，各次执行应使用不同 sid |
| `image` | 用什么镜像创建运行环境？ | 镜像可包含题目所需的代码和依赖；它描述环境，不区分每次执行 |
| `sid` | 这是 Agent 的哪一次执行？ | 是关联本次配置、请求和轨迹的字符串键，本身不装这些内容 |
| 每次请求中的 `messages` | 这轮提交给模型的上下文是什么？ | 同一次执行的历史可以增长、改写或压缩，sid 仍可沿用 |
| manager 中的轨迹树 | 这次执行记录过哪些消息路径与生成结果？ | manager 按 sid 找树；树在后续记录时建立，可有多条分支 |

下面是**概念示意**，`run-A`、`run-B` 只是便于阅读的编号，不是实测值：

```text
同一道题 instance_id = "issue-123"
├─ 第一次独立执行：sid = "run-A"
│  ├─ 第 1 轮请求：初始上下文
│  ├─ 第 2 轮请求：加入工具执行结果后的上下文
│  └─ ……这些轮次的记录归入 manager._trees["run-A"]
└─ 第二次独立执行：sid = "run-B"
   └─ 有自己的多轮消息与轨迹树
```

**先有执行编号，再按编号积累记录。** `generate` 在启动沙箱和 CLI 之前取得 `session_id` 并调用 `open_session`；`record_turn` 后来用 `self._trees.setdefault(sid, MessageNode())` 找到或建立该编号的树。`messages` 用于在这棵树里定位消息路径，并不用来计算 sid。树出现分支也不自动产生新 sid。

## 编号从哪里来

具体编号的来源允许不同：`_session_id` 优先沿用输入 Sample 已有的 `session_id`；没有时才用题目与样本索引组合，或附加随机串。正常组级生成会给尚无编号的 Sample 分配 UUID。`sid` 不要求从题目内容、镜像或消息树算出来。

## 编号怎样传到每轮请求

当前路径中，`generate` 决定 `session_id`，登记会话并传给 Harness；CLI 的请求将它带回 Adapter，`_run_turn` 取出后命名为 `sid`。因此外层的 `session_id` 和这里的 `sid` 可以指向同一个会话编号。

> `sid` 回答“这是 Agent 的哪一次执行”。这次执行可以有很多轮消息，最后形成自己的轨迹记录。

读清这个对象后，进入 [inflight：按编号登记当前请求](inflight.md)，再返回 `shutdown_session`。

<details>
<summary>源码与原始讨论</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 编号来路：[`generate` 取得并传递 session_id](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L194-L209)。当前 Claude Code 路径将其设为 [`ANTHROPIC_AUTH_TOKEN`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L62-L67)，Adapter 从[请求头解析编号](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L192-L195)。这只是当前协议路径的定位，不是完整认证教程。
- 2026-10-22 补充执行粒度：[`_session_id` 的沿用与生成规则](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L308-L313)、[组级生成分配 UUID](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L399-L402)、[每次 Agent 执行的编号约定](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L216-L219)、[按 sid 找树，再按消息找路径](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L300-L305)。[本次追问](../04-flow.md#sid-run-task-tree-messages)保留用户的对象辨析问题；本节是助手解释，不代表已确认理解。
- `run-A`、`run-B` 是教学编号；本节按源码静态核对，没有运行新实验，也不表示用户已经掌握。
- [拆分决定与记录边界](../04-flow.md#split-sid-inflight-references)：2026-10-22 从原合并说明迁入；迁移不算个人认识更新。

</details>
