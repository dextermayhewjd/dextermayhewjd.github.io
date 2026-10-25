# 01 · 阅读范围：登记本次 Agent 执行的会话配置

[本步入口](README.md) · [Step 0 核心骨架](../step-000-coding-agent/01-scope.md) · [前序函数记忆](03-long-term-memory/overview.md) · [旧版 scope](references/scope-at-2f231865.md)

## 1. 阅读目标

- **整体目标**：理解 Coding Agent / Coding RL 的运行流程。
- **本步问题**：一次 Agent 执行开始前，会话配置怎样按 `sid` 登记到对应的 Adapter，供模型请求与样本导出使用？
- **阅读范围**：先弄清 `state` 指向的服务对象，再看它怎样提供 Adapter 与地址，随后进入 `open_session`，读清按 sid 创建和登记 Session 的关系；内部字段按用户最新要求留待后续。

## 2. 指挥官函数

- **整体编排**：`examples/coding_agent_rl/generate.py::_generate` 在启动执行沙箱前准备 Adapter、执行编号与会话配置；本步回到这段准备过程。
- **核心入口**：[BaseAdapter.open_session:275–292](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L292)，由 [_generate:270–279](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L270-L279) 调用。
- **选择理由**：Step 001 已看到运行时取用配置，Step 004 已看到结束时取走配置；这里补齐同一份配置最初的创建与登记。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 1 项

沿用前几步的 `evaluation=False` 正常路径。以下为教学裁剪：省略参数、配置、检查、追踪、日志、超时与失败包装，保留业务调用及其顺序；`baseline` 与运行统计接回 Step 002。

```python
adapter.open_session(...)  # 1. 本步：登记会话配置
async with boot_agent_sandbox(...) as sb:  # 2. 启动执行沙箱
    baseline = await swe.prepare_workspace(...)  # 3. 准备工作区，取得初始快照
    agent_exit_code = await harness.run(...)  # 4. 运行 CLI，等待结束
    # CLI 运行期间，通过 HTTP 进入 Step 001 并逐轮记录轨迹
    agent_metrics = await harness.collect_metrics(...)  # Step 002：读取运行统计
    diff_text = await swe.git_diff(...)  # 5. Step 002：提取代码补丁

reward, applied_cleanly = await swe.run_evaluation(...)  # 6. Step 003：独立评测
samples = await adapter.finish_session(...)  # 7. Step 004：导出训练样本
...  # 检查空结果，附加退出信息与截断状态；最终还有会话清理
return samples
```

本步展开第 1 项。执行时，登记先于模型请求与样本导出；阅读时从已读的取用与取出回查登记。`evaluation=True` 也需要登记会话，但会在评测后提前返回，不经过上图的训练样本导出。

<a id="adapter-to-open-session"></a>

### 3.2 从调用现场认清 Adapter 与编号

先看 [_generate:256–279](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L256-L279)。本轮将服务对象作为必要前置，按“`state` 是谁 → 它提供哪个 Adapter → 在该 Adapter 上登记”阅读。下图按执行顺序裁剪，保留题目信息到执行编号的来源，省略前置检查。

```text
_generate [generate.py:254]
├─ state = _AdapterService(...) [256] → 取得可复用的服务状态
│  └─ 首次初始化：_AdapterService.__init__ [168–182]
│     → 准备共用依赖，建立默认 Agent 的端点
├─ agent_name = agent_name_for(...) [257] → 确定本次使用的 Agent
├─ adapter, adapter_url, _ = state.endpoint(agent_name) [259]
│  └─ _AdapterService.endpoint [184–222] → 取用或创建该 Agent 的 Adapter
├─ md = swe.get_metadata(base_sample, protocol) [261] → 复用已读的题目信息整理逻辑
├─ instance_id = md["instance_id"] [262] → 取得题目编号
├─ session_id = base_sample.session_id = _session_id(...) [269]
│  └─ _session_id [438–443] → 沿用编号，或根据索引、随机串生成编号
└─ adapter.open_session(...) [270–279]
   └─ BaseAdapter.open_session [adapters/common.py:275–292]
```

`state` 是变量名，引用 `_AdapterService` 实例；服务对象保存共用依赖，并用 `_endpoints` 缓存各 Agent 的 `(adapter, adapter_url, app_handle)`。首次创建会初始化，后续可复用已有服务；单例内部机制暂不展开。

沿用 `claude_code → AnthropicAdapter` 示例。`state.endpoint(agent_name)` 交回本次使用的对象与地址；进入 `open_session` 后，`self` 指向其中的 Adapter，`session_id` 对应形参 `sid`。`adapter_url` 留给后续 Harness 使用，不是 `open_session` 的参数。

**已读前置，本步复用**：`md` 的整体含义和 Scaleswe 整理分支已在 Step 003 阅读，见[已有函数记录](../step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_metadata_scaleswe.md)及[当时的理解反馈](../step-003-swe-evaluation/04-flow.md#evaluation-environment-entry)。本步只接清 `md["instance_id"] → _session_id → open_session` 的输入关系；图中保留真实调用，元数据整理实现不列为本步新增阅读内容。需要唤起字段背景时回查前序记录，原有缺失值与回退规则仍保留为未知。

登记参数来自采样参数、服务的上下文长度、合并后的模板选项与当前任务的 trace。其他名称背景可回查[输入参考目录](references/generate-input-context.md)；旧版示例继续保留其原始来源。

<a id="reading-path"></a>

### 3.3 登记骨架与阅读导航

以下从 [open_session:284–292](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L284-L292)裁剪，只保留新 `sid` 的正常登记；重复编号会抛出 `ValueError`，不会覆盖已有配置。

```python
self.store[sid] = Session(...)  # 创建配置对象，登记到这个 Adapter
# 隐式返回 None；配置留在 store[sid] 中
```

当前先恢复服务对象的模型，再取得 Adapter，最后进入登记；编号规则只作必要回顾。已有初始化卡片已讨论过 `state` 与 Adapter 的关系，可直接用来唤起旧认识，但新版职责拆分与行号以固定源码为准。

| 阅读位置与入口 | 本步看清什么 | 返回或继续位置 |
| --- | --- | --- |
| ① 服务对象：[类卡](02-short-term-memory/classes/examples/coding_agent_rl/generate.py/_AdapterService.md) · [__init__ 卡片](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md) | `state` 是什么对象，保存什么，首次初始化与后续复用有什么区别 | 接回 `_generate:256–259`，看服务怎样提供本次 Adapter |
| ② 获取 Adapter：[endpoint 卡片](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.endpoint.md) | 按 `agent_name` 创建或复用 Adapter，连同地址和句柄返回 | 回到 `_generate:259` 解包，再接 `270` 的登记调用 |
| ② 内部的服务启动：[run_app_in_thread 卡片](02-short-term-memory/functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md) | 已有 `adapter.app` 怎样在后台线程开始监听；正常返回的 AppHandle 表示什么 | 回到 `endpoint:210`，用实际端口组成访问地址；服务线程继续运行 |
| ③ 登记主线：[open_session:275–292](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L292) · [函数卡片](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md) | 已有编号与配置怎样变成 `store[sid]`；登记前后改变什么 | 隐式返回 `None`，回到 `_generate`；本步在登记完成处停止 |
| 编号回查：[_session_id:438–443](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L438-L443) · [函数卡片](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_session_id.md) | 复用已有的三种规则，区分题目编号与执行编号 | 回到 `_generate:269` 保存字符串，再到 `270` 登记 |
| 后续参考：[Session:46–57](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L46-L57) · [类卡片](02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md) | 本轮先把它视为按 sid 管理的会话对象；内部字段暂缓，用到时再展开 | 当前直接接回 `open_session:287–292` 的创建与赋值 |

**停止条件**：能接清“服务对象 → 已监听的 Adapter → 哪次执行的编号 → 登记后的配置”，并连回 `_run_turn` 的取用与 [finish_session](../step-004-trajectory-to-samples/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md)的取出。HTTP 请求分派、服务停止回收、trace 内部处理、模板与前缀算法留待按需展开；后面的沙箱与工作区准备只保留整体位置。

## 版本说明

- **源码基准**：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本页入口、整体骨架、局部导航与行号已按此版本核对，见[本轮记录](04-flow.md#scope-refresh-18868a79)。
- **主要变化**：调用处使用 `state.endpoint(agent_name)` 取得 Adapter；`open_session` 新增模板选项与 trace 参数，Session 从两项字段增加为五项。`_session_id` 的函数 AST 与旧版相同，仅更新定位。
- **本轮材料**：服务类卡、初始化、endpoint 和后台启动卡片已按新版整理；编号卡已核对规则未变，open_session 与 Session 已按四项传参与五字段状态校准；[task flow](05-task-flow.md)已按本轮阅读与后置范围收拢。`03` 已继承 Step 004 当前的 30 份记录，原 27 份索引与被替换的三张卡片保留在[继承归档](references/long-term-before-2026-10-24/README.md)。[旧版 scope](references/scope-at-2f231865.md)及个人原话继续保留，材料整理不代表已经掌握实现。
