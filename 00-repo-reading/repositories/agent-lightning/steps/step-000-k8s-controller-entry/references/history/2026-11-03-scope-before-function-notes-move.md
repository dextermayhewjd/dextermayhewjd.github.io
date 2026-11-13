> 链接维护说明：用户已撤回尚未接触就提前创建的函数卡；本文指向这些卡片的旧链接现改为固定版本源码。历史叙述保留。

> 历史快照：2026-11-03，原 3.3 的函数内部说明迁入短期函数记录之前。现行 scope 保留整体骨架与编号导航，本文仅作历史回查。

# 01 · K8sReconciler 的整体骨架与阅读范围

[本地试读](../../README.md) · [已有函数记录](../../02-short-term-memory/overview.md) · [调整过程](../../04-flow.md#scope-first-revision)

## 1. 阅读目标

- **整体目标**：承接 Slime 的执行环境接口，理解 Agent 任务在 Kubernetes 中怎样被创建、跟踪与收束。
- **本步问题**：先看清整个 `K8sReconciler` 怎样连接 rollout 与 Job，再从 **[1] `_reconcile_once`** 看一轮协调的主流程。
- **当前范围**：Step 000 先建立全图并读 [1] 的职责与交接；[2]–[5] 在图中保留位置，按下方建议分入后续步骤。配置、错误包装与底层库先折叠，保留影响任务去向的业务分支。

用户已明确要求先给 Reconciler 骨架，再考虑函数深入。此前只看 `run()` 并提问的起点已调整；[原 scope](2026-11-03-scope-before-overview.md)保留回查。

用户随后认可 3.1、3.2 的整体呈现，并要求加入 1、2、3、4、5 的阅读路标、源码入口和步骤／短期函数映射。本轮保留两张图的结构，只补这些导航关系；[编号前的 scope](2026-11-03-scope-before-reading-numbers.md)保留。

## 2. 找到指挥官函数与最小前置

- **启动定位，先作参考**：`K8sReconciler.run` 同时组织两条路径；已有 [run 卡片](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126)用于回查，不把它再排成第一道局部问题。
- **[1] 本步主读入口**：`_reconcile_once`，串起读取 rollout、读取 Job、逐项匹配以及创建或状态同步。
- **[2]–[3] 后续创建路径**：`_create_job` → `build_job_spec`，对应“任务怎样成为 Job”的一步。
- **[4]–[5] 后续状态路径**：`_watch_jobs_loop` → `_handle_job_event` → `_patch_status`，对应“Job 状态怎样交回任务”的一步。

每个编号的源码、记录落点和返回位置统一见 [3.4 阅读导航](#reading-navigation)。

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

**图中的 [1]–[5] 是阅读顺序，与 3.4 同号对应。当前从 [1] 开始。** A/B 继续表示并发执行的两条路径；[5] 出现多次，表示回到同一个状态写回函数。未编号的初始化、客户端获取与停止先作背景，按需要回查。

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

### 3.3 沿真实代码连接任务、Job 与状态

下面是职责级教学裁剪。调用参数通常省略；状态分支保留必要条件。已有 Job 的详细状态判断用下表承接，没有另造源码里不存在的同步函数。

**[1] A：一轮周期协调先读两边，再逐条匹配。**

```python
# [1] _reconcile_once
rollouts = await self._query_rollouts(...)  # 查询 QUEUING / RUNNING 的任务
api = await self._get_k8s_api()
jobs = [job.raw async for job in k8s_objects.Job.async_list(...)]
jobs_by_name = {job.get("metadata", {}).get("name", ""): job for job in jobs}

for rollout in rollouts:
    job_name = rollout.status.k8s_job_name or build_job_name(...)
    job = jobs_by_name.get(job_name)

    if job is None:
        if rollout.status.state == RolloutState.QUEUING:
            await self._create_job(...)  # [2] 创建路径
            continue
        await self._patch_status(..., state=RolloutState.FAILED)  # [5] 共用出口
        continue

    ...  # 已有 Job：根据下面的状态分支，按需调用 [5] _patch_status
```

| 匹配后的情况 | 原实现的去向 |
| --- | --- |
| 找不到 Job，rollout 仍在排队 | `_create_job` 提交 Job；成功创建本身不立即改写 rollout 状态 |
| 找不到 Job，rollout 已登记为运行中 | `_patch_status` 标为失败，原因是 Job 消失 |
| Job 已存在且尚无终态 | 排队中的 rollout 更新为 `RUNNING`；原本已运行的任务继续等待 |
| Job 已完成或失败 | 按观测结果更新 rollout 的终态；排队中的任务若直接被观测为成功，会先尝试更新为 `RUNNING`，成功后再更新为 `SUCCEEDED` |

这里的 `RUNNING` 是 Agent Lightning 的任务状态；上述判断不等于逐一确认 Pod 内进程已开始执行。终态条件、计数回退及写入失败的细则留到函数阅读时展开。

**[2] 进入 `_create_job` 后，核心交接是：**

```python
manifest = build_job_spec(...)  # [3] 读完后回到这里，接住 manifest
api = await self._get_k8s_api()
job = k8s_objects.Job(manifest, api=api)
await job.async_create()
```

这段选择模板有效、未触发创建限速、提交成功的路径。函数完成后返回 `_reconcile_once`，继续处理其余 rollout；Agent 的运行由 Kubernetes 承接，不在这个 Python 函数里执行。

**[4] B：事件观察接到 Job 的变化，再交给状态处理。**

```python
# [4] _watch_jobs_loop：保留持续观察与事件交接，折叠停止检查和断线重试
while not self._stop.is_set():
    watcher = kr8s.asyncio.watch("jobs", ...)
    async for event_type, obj in watcher:
        if event_type in ("MODIFIED", "ADDED"):
            await self._handle_job_event(obj.raw)
```

`_handle_job_event` 同属 [4]，从 Job label 取出 `rollout_id`；有效的 `Complete` 条件回写 `SUCCEEDED`，有效的 `Failed` 条件回写 `FAILED`。它通过 [5] `_patch_status` 回到 Gateway，完成后返回观察循环。这里交回的是任务状态，奖励与模型调用记录有另外的事件通路。

<a id="reading-navigation"></a>

### 3.4 按编号阅读：代码 → 问题 → 短期记录 → 返回位置

**现在从 [1] 开始看代码。** 先看 `_reconcile_once` 怎样取两边的数据并选择动作；初读时把 [2] 创建 Job、[5] 写回状态当作接口使用，后续再展开。下表不是五项平行任选菜单，而是建议的连续阅读顺序。

源码均在 [本地 k8s_reconciler.py](/home/fredkeira/projects/agent-lightning/agentlightning/controller/k8s_reconciler.py)；下表给出固定版本的行号链接。编号表示阅读顺序，运行时 A/B 仍然并发。

| 编号 | 从哪段代码开始 | 这一处要弄清什么 | 步骤与对应短期函数 | 读完返回哪里 |
| --- | --- | --- | --- | --- |
| <a id="read-1"></a>**[1] 当前先读** | [`_reconcile_once:161`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L161) | 取得 rollout 和 Job，按名字匹配，再决定创建、等待或更新状态；两项外部动作先看接口 | **当前 Step 000**；主记录为 `K8sReconciler._reconcile_once`，实际展开时建立 | 回 A 的周期调用；看清整体后进入 [2] |
| <a id="read-2"></a>**[2] 创建 Job** | [`_create_job:242`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L242) | 一条排队任务怎样经过 manifest 构造，交给 Kubernetes 创建 Job | **拟 Step 001：任务变成 Job**；`K8sReconciler._create_job` | manifest 来源不清楚时进 [3]；提交完成后回 [1] 的无 Job 分支 |
| <a id="read-3"></a>**[3] 构造 manifest** | [`build_job_spec:43`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43) | rollout 输入和模板怎样变成带任务标记、环境变量与运行约束的 Job 配置 | **同一拟 Step 001**；`build_job_spec` | 返回 [2] 的 `manifest = build_job_spec(...)`，继续提交 Job |
| <a id="read-4"></a>**[4] 观察 Job** | [`_watch_jobs_loop:292`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L292) → [`_handle_job_event:311`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L311) | 事件怎样到达处理函数，怎样找到原任务并识别完成或失败 | **拟 Step 002：状态观察与回报**；`K8sReconciler._watch_jobs_loop`、`K8sReconciler._handle_job_event` | 需要交回状态时进 [5]；处理后回 B 等待后续事件 |
| <a id="read-5"></a>**[5] 写回状态** | [`_patch_status:362`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L362) | 任务编号和状态字段怎样变成 Gateway 更新请求，布尔结果怎样交回调用方 | **同一拟 Step 002**；`K8sReconciler._patch_status`，A/B 共用一张记录 | 回 [4] 当前调用；再回看 [1] 对同一接口的使用 |

阅读时的回查路线为：**[1] → [2] → [3] → 回 [2] → 回 [1] → [4] → [5] → 回 [4]**。这是学习时的进入与返回，不是两个后台循环的执行时间线。

<a id="memory-map"></a>

#### 编号怎样落到函数记录

每步的函数卡片统一放在 `02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/`，文件名使用上表的完整函数名加 `.md`。

- **已存在的卡片**：[K8sReconciler.run](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126)。它用于恢复启动与并发背景，不占 [1]–[5] 的主读编号。
- **当前 Step 000 的目标卡片**：`K8sReconciler._reconcile_once.md`。本轮只确定和标明阅读入口，尚未展开个人问答，未预建该卡；已有记录与目标的状态见 [本步函数索引](../../02-short-term-memory/overview.md)。
- **拟 Step 001 的两张卡片**：`K8sReconciler._create_job.md`、`build_job_spec.md`，分别对应 [2]、[3]。
- **拟 Step 002 的三张卡片**：`K8sReconciler._watch_jobs_loop.md`、`K8sReconciler._handle_job_event.md`、`K8sReconciler._patch_status.md`，分别承接 [4]、[5]；[5] 不因被两条路径调用而重复建卡。

后两步是本次建议的分组，尚未创建目录或记录，不算已经开始。实际开启时再确定该步范围，并按 `前一步 03 + 02 → 下一步 03` 继承；这里提供的是源码与明确的记录落点，没有指向不存在文件的链接。

**本步停止点**：先通过 [1] 解释任务与 Job 怎样匹配、为何选择创建或状态同步。[2]–[5] 的内部实现不要求在 Step 000 一次读完。模板全部字段、Kubernetes 调度器、训练器内部和完整失败恢复继续按问题取舍。

<details>
<summary>参考的 Slime scope、源码版本与裁剪边界</summary>

- [Slime Step 001](../../../../../slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md)：保留任务七项骨架，再定位一次请求、展开局部顺序和阅读导航。
- [Slime Step 012](../../../../../slime/topics/02-rollout-reward/steps/step-012-async-rollout-worker-loop/01-scope.md)：先区分后台生产与上层消费，再给出完整循环，最后选择局部观察点。
- [Slime Step 017](../../../../../slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/01-scope.md)：整体位置、连续交接骨架、局部入口与返回位置分层组织。
- Agent Lightning 固定提交：`0029dbb35c467799d35fee81d15d80264b0d1bd3`。本次骨架依据 `agentlightning/controller/k8s_reconciler.py`，无源码改动或真实集群运行。
- 调用树跨多层仅作职责定位；不是本轮已对所有函数完成逐层阅读。3.3 折叠类型转换、等待周期、日志、部分检查和异常处理；完整源码保留它们。
- 控制器重试、限速、停止响应和清理细节没有被此概览验证。当前使用本地 Markdown，不建立或构建 Hugo 页面。

</details>
