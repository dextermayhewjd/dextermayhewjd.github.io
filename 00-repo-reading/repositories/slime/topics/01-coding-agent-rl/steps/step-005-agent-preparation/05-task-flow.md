# 05 · 任务链路：准备 Adapter 服务并登记本次执行的会话

> `_generate` 先取得可用的 Adapter、访问地址与服务句柄，再为本次执行取得 sid，通过 `open_session` 在 Adapter 的 store 中登记 Session，供后续请求按编号取用。

[本步 scope](01-scope.md) · [步骤入口](README.md) · [函数与类记录](02-short-term-memory/overview.md) · [本轮收束](04-flow.md#agent-preparation-mainline-closure)

## 1. 本步在任务中的位置

Step 001 已看到模型请求按 sid 使用会话状态，Step 004 已看到结束时取走状态、导出样本。本步回到它们之前，补齐服务对象、执行编号与会话登记的来路。

- **已有输入**：`args` 提供运行配置，`base_sample` 提供任务与样本信息，`sampling_params` 提供采样参数；运行时调用 `swe.get_metadata` 得到 `md`，再取出 `instance_id`。本例复用 Step 003 已读的 Scaleswe 整理逻辑。
- **本例路径**：沿 `evaluation=False`，默认 Agent 与本次 Agent 均为 `claude_code`；服务首次初始化、sid 尚未登记，各项准备正常完成。
- **本步终点**：`open_session` 返回 `None`，新 Session 留在 `adapter.store[sid]`。随后才进入执行沙箱和工作区的准备。

Session 的内部字段按用户要求留待后续，本页只总结对象归属与交接。

## 2. 各部分怎样完成交接

下图的编号表示 `_generate` 中的处理阶段，缩进表示实际调用归属。`generate.py` 指 `examples/coding_agent_rl/generate.py`，`common.py` 指 `slime/agent/adapters/common.py`；HTTP 启动函数位于 `slime/agent/aiohttp_threaded.py`。

```text
_generate [generate.py:254]
├─ ① state = _AdapterService(args) [256]
│  └─ 首次初始化：_AdapterService.__init__ [168–182]
│     ├─ 保存配置，准备 tokenizer、解析器名称与模型地址 [169–180]
│     └─ self.endpoint(AGENT_NAME) [182 → 184–222]
│        ├─ 按 Agent 类型选择并创建 Adapter [187–195]
│        │  → 得到带有 HTTP 应用的 adapter 对象
│        ├─ run_app_in_thread(adapter.app, ...) [200–209]
│        │  → 后台线程建立监听，正常返回 app_handle
│        └─ 组成 adapter_url，缓存并返回三元组 [210–222]
│     → __init__:182 将三项保存为默认字段，初始化结束
│  → 类调用把服务对象交给 state；继续 _generate:257
│
├─ ② 为本次任务取得 Adapter [257–259]
│  ├─ agent_name_for(base_sample) → 本例为 claude_code [257]
│  └─ state.endpoint(agent_name) [259]
│     → 本例命中①创建的缓存，直接返回三元组
│  → 解包得到本次 adapter、adapter_url；继续 260
│
├─ ③ 取得并保存执行编号 [260–269]
│  ├─ swe.get_metadata(...) → md；从中取 instance_id [261–262]
│  └─ _session_id(base_sample, instance_id) [269 → 438–443]
│     → 本例返回 cagent-demo-1-0-0
│  → 调用方同时保存到 session_id 与 base_sample.session_id
│
└─ ④ adapter.open_session(session_id, ...) [270–279]
   └─ BaseAdapter.open_session [common.py:275–292]
      ├─ 检查 sid 是否已经登记 [285–286]
      └─ 创建 Session，保存到 self.store[sid] [287–292]
      → 隐式返回 None，状态留在这个 Adapter 中
   → 回到 _generate；本步在登记完成处停止
```

①中的 HTTP 线程在启动函数返回后继续运行。后续 CLI 请求才会触发 Adapter 的消息处理，图中没有把请求处理画成初始化的直接调用。已有服务对象可以复用；若本次选择另一种 Agent，②的 endpoint 会按其缓存情况取得或创建对应端点。

对应记录：[服务类卡](02-short-term-memory/classes/examples/coding_agent_rl/generate.py/_AdapterService.md) · [初始化](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md) · [endpoint](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.endpoint.md) · [HTTP 启动](02-short-term-memory/functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md) · [编号规则](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_session_id.md) · [会话登记](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)。

③保留 `get_metadata → md → instance_id`，因为它仍是本次运行中实际发生的交接。整理逻辑直接引用 [Step 003 的已有函数记录](../step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_metadata_scaleswe.md)；本页不重复展开其字段回退和组装实现。前序阅读记录说明我们何时学过它，本图说明程序何时执行它。

## 3. 本步留下什么，后续由谁使用

沿用编号卡与登记卡的构造例：`instance_id="demo-1"`，样本的 `index=0`、`group_index=0`，原先没有执行编号。登记后的核心关系如下，用名称表示已经创建的对象：

```text
state
└─ _endpoints["claude_code"] → (adapter, adapter_url, app_handle)

adapter
└─ store["cagent-demo-1-0-0"] → Session 对象
```

| 本步结果 | 去向与作用 |
| --- | --- |
| `adapter`、`adapter_url`、`app_handle` | 服务对象缓存端点；Adapter 接收会话操作，地址随后交给 Harness 配置 CLI，句柄保留服务运行资源 |
| `md` | 本次运行通过 `get_metadata` 得到的题目信息字典；本步使用 `instance_id`，其余资料继续交给后续环境准备与评测 |
| `session_id` | 调用方和 `base_sample` 保存同一个编号；它也是 store 的查找键，后续随任务交给 Harness 使用 |
| `adapter.store[sid]` 中的 Session | `_run_turn` 按 sid 取用；会话结束时 `finish_session` 取出并移除，接回已读的样本导出流程 |

`open_session` 的结果主要体现为对象状态变化，返回值是 `None`。同一 Adapter 可保存多个 sid 的记录；重复登记已有 sid 会报错，保留原对象。

Session 自身没有 sid 字段，关联由 store 的键建立。内部字段已有[类卡参考](02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md)，本轮不要求逐项展开。题目的描述、镜像和工作目录仍由 `base_sample` / `md` 承载。

## 4. 本轮收束与后续衔接

按本轮 scope，主线已接清：**准备服务对象 → 取得 Adapter 端点 → 取得执行编号 → 在 store 中登记 Session**。

用户已对初始化、HTTP 启动、端点和编号给出大致理解反馈，并明确概括由 Adapter 按 sid 管理 Session；最新的[登记复述与后置范围](04-flow.md#session-registry-understood-fields-deferred)作为本次收束依据。因此 Step 005 的主线阅读可以在这里结束，内部字段不会成为本轮结束的前置条件。

继续保留的深入问题：

- Session 各字段的具体内容，以及模板、前缀与追踪机制：等后续实际使用时再展开。
- HTTP、线程和事件循环的完整故障处理、停止与资源回收：已有卡片保留入口与未知。
- 索引的上游分配、IP 的选择实现以及协议细节：需要解释相应问题时再回查。

外层随后在 `_generate:283` 进入 `boot_agent_sandbox`。它对应已有的 [Step 006：执行沙箱准备](../step-006-agent-sandbox/README.md)，是下一处接续位置；本页只定位其入口。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定提交：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。
- [服务初始化与端点](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L167-L222)、[调用、编号保存与登记](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L254-L285)、[编号函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L438-L443)。
- [后台 HTTP 启动](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/aiohttp_threaded.py#L46-L98)、[Session 定义](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L45-L57)、[会话登记](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L292)。
- [请求取用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L405-L413)、[结束时取走并导出](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L330-L345)。
- [本轮收束记录](04-flow.md#agent-preparation-mainline-closure)保留用户问题与判断依据；[旧版 task flow](references/task-flow-at-2f231865.md)保留当时的内容、编号与源码归属。
- 既有局部验证覆盖编号、Session 字段、登记结果、字典复制及重复 sid 的处理；Thread 小实验仅覆盖线程构造与启动。本页做静态源码、链接与渲染核对，没有新增真实 HTTP、模型或沙箱运行。

</details>
