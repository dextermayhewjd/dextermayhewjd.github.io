# 01 · K8sReconciler 的整体骨架与阅读范围

[本地试读](README.md) · [已有函数记录](02-short-term-memory/overview.md) · [调整过程](04-flow.md#scope-first-revision)

> 本页保留 Step 000 当时的范围与导航。用户随后要求将事件接收独立建步，后续阅读见 [Step 001 范围](../step-001-watch-job-events/01-scope.md)。

## 1. 阅读目标

- **整体目标**：承接 Slime 的执行环境接口，理解 Agent 任务在 Kubernetes 中怎样被创建、跟踪与收束。
- **本步问题**：先看清整个 `K8sReconciler` 怎样连接 rollout 与 Job；按用户本轮明确选择，从 **[1] `_reconcile_once`** 看单轮协调。
- **当前范围**：Step 000 先建立全图并读 [1] 的职责与交接，已随问题进入 [2]、[5]；用户本轮明确进入 [4] `_watch_jobs_loop`，先看事件接收与交给处理函数的边界。[3] 与 `_handle_job_event` 内部继续按需展开。配置、错误包装与底层库先折叠，保留影响任务去向的业务分支。

用户已明确要求先给 Reconciler 骨架，再考虑函数深入。此前只看 `run()` 并提问的起点已调整；[原 scope](references/history/2026-11-03-scope-before-overview.md)保留回查。

用户随后认可 3.1、3.2 的整体呈现，并要求加入 1、2、3、4、5 的阅读路标、源码入口和步骤／短期函数映射。本轮保留两张图的结构，只补这些导航关系；[编号前的 scope](references/history/2026-11-03-scope-before-reading-numbers.md)保留。

已实际阅读的函数说明保存在 [短期函数记录](02-short-term-memory/overview.md)，通用概念见 [Kubernetes 基础资料](../../../kubernetes/README.md)。用户已撤回尚未接触的提前卡片；函数真正被选入阅读时再建卡，其余调用只保留源码定位。本页负责整体骨架、范围、编号导航和返回位置。

## 2. 找到指挥官函数与最小前置

- **启动定位，先作参考**：`K8sReconciler.run` 同时组织两条路径；[run 源码](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126)用于定位，尚未独立阅读或建卡。
- **[1] 本步首读入口**：`_reconcile_once`，看读取 rollout、读取 Job、逐项匹配以及创建或状态同步。
- **调用背景**：`_periodic_reconcile_loop` 在 151 行等待本函数；它负责重复调用与间隔，本轮先不展开。
- **[2]–[3] 后续创建路径**：`_create_job` → `build_job_spec`，对应“任务怎样成为 Job”的一步。
- **[4]–[5] 事件处理路径**：`_watch_jobs_loop` → `_handle_job_event` → `_patch_status`，连接 Job 事件接收、结果判断与状态回写；本轮先进入事件接收。

每个编号的源码、记录落点和返回位置统一见 [3.3 阅读导航](#reading-navigation)。

用户澄清上一轮函数名输入有误，明确要求从 `_reconcile_once` 开始。本轮据此恢复 [1]，后续 [2]–[5] 不变；此前入口比较保留在 [历史核对](04-flow.md#reading-order-audit)，最新选择见 [本轮记录](04-flow.md#reconcile-once-start)。

对象由 `controller/__main__.py` 的 `_run_controller` 在 k8s 分支创建。进入整体骨架前只需知道：**rollout 是 Gateway 中的一条任务及其状态；Job 是 Kubernetes 中用于运行任务的对象。** Reconciler 使用 Gateway 客户端读写前者，使用 Kubernetes 客户端管理和观察后者。

<a id="core-skeleton"></a>

## 3. 给出真正干活的核心骨架

### 3.1 整体位置

Trainer 将任务登记到 API Gateway；Controller 把任务与 Kubernetes Job 对应起来。Kubernetes 再通过 Job/Pod 运行 Agent。这里先看 Controller 的管理职责，Agent 内部执行、模型代理和训练消费保持背景位置。

```text
Trainer --> API Gateway: rollout + status
                  ^
                  | HTTP: query / patch
             K8sReconciler [1-5]
                  |
                  | Kubernetes API: list / create / watch
                  v
                 Job --> Pod --> Agent
```

`run()` 让下面 A、B 两条路径并发推进；它们不是先执行完 A 再执行 B。

### 3.2 Reconciler 的完整职责骨架

这是调用与职责导航，不是可执行代码。保留任务去向，暂不展开日志、校验、重试与状态字段拼装。

**图中的 [1]–[5] 是阅读顺序，与 3.3 同号对应。当前从 [1] 开始。** A/B 继续表示并发执行的两条路径；[5] 出现多次，表示回到同一个状态写回函数。未编号的初始化、客户端获取与停止先作背景，按需要回查。

```text
K8sReconciler
|-- __init__(api, config)
|-- run()
|   `-- asyncio.gather(...)
|       |-- [A] _periodic_reconcile_loop()
|       |   `-- [1] _reconcile_once()
|       |       |-- _query_rollouts(...) -> rollouts
|       |       |-- _get_k8s_api() + Job.async_list(...) -> jobs
|       |       `-- for rollout in rollouts: match Job
|       |           |-- no Job + QUEUING -> [2] _create_job(...)
|       |           |   |-- [3] build_job_spec(...) -> manifest
|       |           |   `-- Job(manifest, ...) -> job.async_create()
|       |           |-- no Job + RUNNING -> [5] _patch_status(...FAILED)
|       |           `-- existing Job -> [5] _patch_status(...) if needed
|       `-- [B] [4] _watch_jobs_loop()
|           `-- kr8s.asyncio.watch("jobs", ...)
|               `-- ADDED / MODIFIED -> _handle_job_event(...)
|                   `-- Complete / Failed -> [5] _patch_status(...)
`-- stop() -> self._stop.set()
```

两条路径最终都可能更新 Gateway 中的 rollout 状态：**A 周期性对照两边的记录；B 根据到来的 Job 事件及时处理完成或失败。** 因此不能把 A 仅看成创建 Job、把 B 看成唯一的状态更新方。

共享的交接边界如下，先知道用途即可：

| 入口 | 接到哪里、交付什么 |
| --- | --- |
| [1] 内部 `_query_rollouts` | 对 Gateway 发起 `GET /api/rollouts`，返回 `Rollout` 列表；本步先用其接口，不另设阅读编号 |
| [5] `_patch_status` | 对 Gateway 发起 `PATCH /api/rollouts/{rollout_id}`；返回本次请求成功与否的布尔值 |
| `_get_k8s_api` | 获取并缓存 Kubernetes API 客户端，供 list/create/watch 使用 |
| [3] `build_job_spec` | 同模块的独立函数，读取 rollout 中的模板，构造 Job manifest，补上关联标记、环境变量、超时与清理配置 |
| [2] 内部 `_fail_invalid_job_spec` | 将无法使用的 Job 配置标为 rollout 失败；本轮先折叠其错误包装 |

`stop()` 设置的是控制器停止信号；Job 完成后的自动清理由 `build_job_spec` 配置的 TTL 交给 Kubernetes 执行。它们属于不同的生命周期动作。

<a id="reading-navigation"></a>

### 3.3 按编号阅读：代码 → 问题 → 短期记录 → 返回位置

**本步最初从 [1] `_reconcile_once` 开始看代码。** 当时从两份数据来源进入，具体代码、数据节选与观察问题放在 [短期函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#two-data-sources)。[2] 创建 Job、[5] 写回状态从父调用按需下钻，外层周期循环只定位调用与返回。

用户随后选择从父函数的缺失 Job 分支进入 [2] `_create_job`，读完返回父函数，再看 [5] `_patch_status`；本轮再回整体骨架进入 [4] 事件观察。以下保留整体编号用于定位，[3] 模板构造按需要回查。当前实际进度见项目入口。

源码均在 [本地 k8s_reconciler.py](/home/fredkeira/projects/agent-lightning/agentlightning/controller/k8s_reconciler.py)；下表给出固定版本的行号链接。编号表示阅读顺序，运行时 A/B 仍然并发。

| 编号 | 从哪段代码开始 | 这一处要弄清什么 | 步骤与对应短期函数 | 读完返回哪里 |
| --- | --- | --- | --- | --- |
| <a id="read-1"></a><a id="read-1-1"></a>**[1] 当前先读** | [`_reconcile_once:161`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L161) | 取得 rollout 和 Job，按名字匹配，再决定创建、等待或更新状态；当前从两份数据来源进入 | **当前 Step 000**；[短期函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#two-data-sources) | 回 `_periodic_reconcile_loop:151`；完整检查返回后，外层才继续等待 |
| <a id="read-2"></a>**[2] 创建 Job** | [`_create_job:242`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L242) | 一条排队任务怎样经过 manifest 构造，交给 Kubernetes 创建 Job | **本轮在 Step 000 下钻**；[当前函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md) | manifest 来源不清楚时进 [3]；提交完成后回 [1] 的无 Job 分支 |
| <a id="read-3"></a>**[3] 构造 manifest** | [`build_job_spec:43`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43) | rollout 输入和模板怎样变成带任务标记、环境变量与运行约束的 Job 配置 | 按当前疑问决定是否深入，尚未独立建卡 | 返回 [2] 的 `manifest = build_job_spec(...)`，继续提交 Job |
| <a id="read-4"></a>**[4] 观察 Job** | [`_watch_jobs_loop:292`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L292) → [`_handle_job_event:311`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L311) | 本轮先看观察范围、收到的事件与 Job 数据、交给下游的位置 | **当前 Step 000 连续阅读**；已建立 [watch 函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md)，处理函数尚未独立展开 | 下游处理返回后继续接收；本函数整体退出则回到 run 的并发等待 |
| <a id="read-5"></a>**[5] 写回状态** | [`_patch_status:362`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L362) | 任务编号和状态字段怎样变成 Gateway 更新请求，布尔结果怎样交回调用方 | 已按用户要求建立[函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md)，当前从父函数失败登记场景进入 | 先回 [1] 的调用处；以后可复用到 [4] |

已经沿问题走过的阅读路线为：**[1] → [2] → 回 [1] → [5] → 回 [1]**。本轮回到整体骨架进入 **[4] `_watch_jobs_loop`**；[3] 仍是 [2] 的按需回查入口。这是学习时的进入与返回，不是两个后台循环的执行时间线。

回到 [1] 后，已有 Job 的后半段按[父函数卡内的三个阅读段](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#existing-job-reading-map)接续：归纳 Job 结果 → 根据结果选择状态回写路径。具体变量、分支与局部编号保存在函数卡中。

<a id="memory-map"></a>

#### 编号怎样落到函数记录

每步的函数卡片统一放在 `02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/`，文件名使用上表的完整函数名加 `.md`。

- **当前首读 [1]**：[K8sReconciler._reconcile_once](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md)，当前从两份数据来源进入；外层周期循环只作为调用背景。
- **[1] 已实际接触的内部调用**：[_query_rollouts](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._query_rollouts.md)、[_get_k8s_api](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md)，以及当前的 [Job.async_list](02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)；实际理解状态各自保留。
- **已选入 [2]**：[_create_job](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md) 现在根据用户的实际阅读请求建卡；此前提前创建并被删除的备稿不作为已读历史。
- **已选入 [4]**：[_watch_jobs_loop](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md) 已按本轮选择建立卡片；`_handle_job_event` 只保留源码入口，读到其交接后再按问题进入。
- **已选入 [5]**：[_patch_status](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md) 按用户要求独立阅读；从父函数的失败登记进入。
- **仅定位 [3]**：`build_job_spec` 的内部尚未展开，继续链接源码，未创建函数卡。
- **启动背景**：[K8sReconciler.run](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126)，不占 [1]–[5] 的主读编号。

此前按创建与状态回报分别组织后续步骤的安排属于建议。本轮按用户的连续问题在当前父函数下钻，没有自动创建新步骤；以后真正开启下一步时再继承已有记录。不能因为助手预先写过说明，就把尚未接触的函数算入本步记忆。

**本步停止点**：通过 [1] 解释任务与 Job 怎样匹配、为何选择创建或状态同步，并知道完整检查结束后回到外层循环。[2]–[5] 的内部实现不要求在 Step 000 一次读完。模板全部字段、Kubernetes 调度器、训练器内部和完整失败恢复继续按问题取舍。

<details>
<summary>参考的 Slime scope、源码版本与裁剪边界</summary>

- [Slime Step 001](../../../slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md)：保留任务七项骨架，再定位一次请求、展开局部顺序和阅读导航。
- [Slime Step 012](../../../slime/topics/02-rollout-reward/steps/step-012-async-rollout-worker-loop/01-scope.md)：先区分后台生产与上层消费，再给出完整循环，最后选择局部观察点。
- [Slime Step 017](../../../slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/01-scope.md)：整体位置、连续交接骨架、局部入口与返回位置分层组织。
- Agent Lightning 固定提交：`0029dbb35c467799d35fee81d15d80264b0d1bd3`。本次骨架依据 `agentlightning/controller/k8s_reconciler.py`，无源码改动或真实集群运行。
- 调用树跨多层仅作职责定位；不是本轮已对所有函数完成逐层阅读。函数内部的代码裁剪、输入输出和分支说明在 `02-short-term-memory/`，scope 只保留位置、范围与阅读导航。
- 控制器重试、限速、停止响应和清理细节没有被此概览验证。当前使用本地 Markdown，不建立或构建 Hugo 页面。

</details>
