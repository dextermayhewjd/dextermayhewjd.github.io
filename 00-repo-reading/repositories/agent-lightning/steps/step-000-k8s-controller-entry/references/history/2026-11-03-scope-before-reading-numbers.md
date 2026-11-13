> 链接维护说明：用户已撤回尚未接触就提前创建的函数卡；本文指向这些卡片的旧链接现改为固定版本源码。历史叙述保留。

> 历史快照：2026-11-03，用户认可 3.1、3.2 的整体呈现后，要求增加阅读编号及步骤／函数记录映射。此稿保留编号补充前的状态。

# 01 · K8sReconciler 的整体骨架与阅读范围

[本地试读](../../README.md) · [已有函数记录](../../02-short-term-memory/overview.md) · [调整过程](../../04-flow.md#scope-first-revision)

## 1. 阅读目标

- **整体目标**：承接 Slime 的执行环境接口，理解 Agent 任务在 Kubernetes 中怎样被创建、跟踪与收束。
- **本步问题**：先看清整个 `K8sReconciler` 怎样连接 rollout 与 Job，再从这张骨架选择一个函数深入。
- **当前范围**：周期协调、Job 创建、事件观察与状态回写的职责和交接。配置、错误包装与底层库先折叠，保留影响任务去向的业务分支。

用户已明确要求先给 Reconciler 骨架，再考虑函数深入。此前只看 `run()` 并提问的起点已调整；[原 scope](2026-11-03-scope-before-overview.md)保留回查。

## 2. 找到指挥官函数与最小前置

- **控制器启动入口**：`K8sReconciler.run`，同时组织周期协调与事件观察两条路径；仅它的两个调用还不足以解释任务怎样执行。
- **一次周期协调的编排函数**：`_reconcile_once`，串起读取 rollout、读取 Job、逐项匹配以及创建或状态同步。
- **事件路径的处理入口**：`_handle_job_event`，从一个 Job 事件中定位 rollout 并回写终态。

对象由 `controller/__main__.py` 的 `_run_controller` 在 k8s 分支创建。进入整体骨架前只需知道：**rollout 是 Gateway 中的一条任务及其状态；Job 是 Kubernetes 中用于运行任务的对象。** Reconciler 使用 Gateway 客户端读写前者，使用 Kubernetes 客户端管理和观察后者。

<a id="core-skeleton"></a>

## 3. 给出真正干活的核心骨架

### 3.1 整体位置

Trainer 将任务登记到 API Gateway；Controller 把任务与 Kubernetes Job 对应起来。Kubernetes 再通过 Job/Pod 运行 Agent。这里先看 Controller 的管理职责，Agent 内部执行、模型代理和训练消费保持背景位置。

```text
Trainer --> API Gateway: rollout + status
                  ^
                  | HTTP: query / patch
             K8sReconciler
                  |
                  | Kubernetes API: list / create / watch
                  v
                 Job --> Pod --> Agent
```

`run()` 让下面 A、B 两条路径并发推进；它们不是先执行完 A 再执行 B。

### 3.2 Reconciler 的完整职责骨架

这是调用与职责导航，不是可执行代码。保留任务去向，暂不展开日志、校验、重试与状态字段拼装。

```text
K8sReconciler
|-- __init__(api, config)
|-- run()
|   `-- asyncio.gather(...)
|       |-- [A] _periodic_reconcile_loop()
|       |   `-- _reconcile_once()
|       |       |-- _query_rollouts(...) -> rollouts
|       |       |-- _get_k8s_api() + Job.async_list(...) -> jobs
|       |       `-- for rollout in rollouts: match Job
|       |           |-- no Job + QUEUING -> _create_job(...)
|       |           |   |-- build_job_spec(...) -> manifest
|       |           |   `-- Job(manifest, ...) -> job.async_create()
|       |           |-- no Job + RUNNING -> _patch_status(...FAILED)
|       |           `-- existing Job -> inspect / patch status if needed
|       `-- [B] _watch_jobs_loop()
|           `-- kr8s.asyncio.watch("jobs", ...)
|               `-- ADDED / MODIFIED -> _handle_job_event(...)
|                   `-- Complete / Failed -> _patch_status(...)
`-- stop() -> self._stop.set()
```

两条路径最终都可能更新 Gateway 中的 rollout 状态：**A 周期性对照两边的记录；B 根据到来的 Job 事件及时处理完成或失败。** 因此不能把 A 仅看成创建 Job、把 B 看成唯一的状态更新方。

共享的交接边界如下，先知道用途即可：

| 入口 | 接到哪里、交付什么 |
| --- | --- |
| `_query_rollouts` | 对 Gateway 发起 `GET /api/rollouts`，返回 `Rollout` 列表 |
| `_patch_status` | 对 Gateway 发起 `PATCH /api/rollouts/{rollout_id}`；返回本次请求成功与否的布尔值 |
| `_get_k8s_api` | 获取并缓存 Kubernetes API 客户端，供 list/create/watch 使用 |
| `build_job_spec` | 同模块的独立函数，读取 rollout 中的模板，构造 Job manifest，补上关联标记、环境变量、超时与清理配置 |
| `_fail_invalid_job_spec` | 将无法使用的 Job 配置标为 rollout 失败；本轮先折叠其错误包装 |

`stop()` 设置的是控制器停止信号；Job 完成后的自动清理由 `build_job_spec` 配置的 TTL 交给 Kubernetes 执行。它们属于不同的生命周期动作。

### 3.3 沿真实代码连接任务、Job 与状态

下面是职责级教学裁剪。调用参数通常省略；状态分支保留必要条件。已有 Job 的详细状态判断用下表承接，没有另造源码里不存在的同步函数。

**A：一轮周期协调先读两边，再逐条匹配。**

```python
# _reconcile_once
rollouts = await self._query_rollouts(...)  # 查询 QUEUING / RUNNING 的任务
api = await self._get_k8s_api()
jobs = [job.raw async for job in k8s_objects.Job.async_list(...)]
jobs_by_name = {job.get("metadata", {}).get("name", ""): job for job in jobs}

for rollout in rollouts:
    job_name = rollout.status.k8s_job_name or build_job_name(...)
    job = jobs_by_name.get(job_name)

    if job is None:
        if rollout.status.state == RolloutState.QUEUING:
            await self._create_job(...)
            continue
        await self._patch_status(..., state=RolloutState.FAILED)
        continue

    ...  # 已有 Job：根据下面的状态分支，按需调用 _patch_status
```

| 匹配后的情况 | 原实现的去向 |
| --- | --- |
| 找不到 Job，rollout 仍在排队 | `_create_job` 提交 Job；成功创建本身不立即改写 rollout 状态 |
| 找不到 Job，rollout 已登记为运行中 | `_patch_status` 标为失败，原因是 Job 消失 |
| Job 已存在且尚无终态 | 排队中的 rollout 更新为 `RUNNING`；原本已运行的任务继续等待 |
| Job 已完成或失败 | 按观测结果更新 rollout 的终态；排队中的任务若直接被观测为成功，会先尝试更新为 `RUNNING`，成功后再更新为 `SUCCEEDED` |

这里的 `RUNNING` 是 Agent Lightning 的任务状态；上述判断不等于逐一确认 Pod 内进程已开始执行。终态条件、计数回退及写入失败的细则留到函数阅读时展开。

**进入 `_create_job` 后，核心交接是：**

```python
manifest = build_job_spec(...)
api = await self._get_k8s_api()
job = k8s_objects.Job(manifest, api=api)
await job.async_create()
```

这段选择模板有效、未触发创建限速、提交成功的路径。函数完成后返回 `_reconcile_once`，继续处理其余 rollout；Agent 的运行由 Kubernetes 承接，不在这个 Python 函数里执行。

**B：事件观察接到 Job 的变化，再交给状态处理。**

```python
# _watch_jobs_loop：保留持续观察与事件交接，折叠停止检查和断线重试
while not self._stop.is_set():
    watcher = kr8s.asyncio.watch("jobs", ...)
    async for event_type, obj in watcher:
        if event_type in ("MODIFIED", "ADDED"):
            await self._handle_job_event(obj.raw)
```

`_handle_job_event` 从 Job label 取出 `rollout_id`；有效的 `Complete` 条件回写 `SUCCEEDED`，有效的 `Failed` 条件回写 `FAILED`。它通过 `_patch_status` 回到 Gateway，完成后返回观察循环。这里交回的是任务状态，奖励与模型调用记录有另外的事件通路。

<a id="reading-navigation"></a>

### 3.4 看完骨架后，再选择局部入口

当前先看完整骨架，不继续前一版关于 `run()` 调用次数的提问。下面是选入口时的依据，不表示已经开启这些函数的精读。

| 想先弄清的问题 | 对应源码入口 | 最小前置与返回位置 |
| --- | --- | --- |
| 一轮检查怎样决定创建、等待或同步状态？ | [`_reconcile_once:161`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L161) | 先认清 rollout 与 Job；读完回 A 的周期循环。这是整体骨架清楚后的优先候选 |
| 一条任务怎样成为真实 Job？ | [`_create_job:242`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L242) → [`build_job_spec:43`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43) | 需要该任务的输入与模板；读完回 `_reconcile_once` 的无 Job 分支 |
| Job 完成后怎样对应回原任务？ | [`_handle_job_event:311`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L311) → [`_patch_status:362`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L362) | 需要 Job label 与 condition；读完回 B 的观察循环 |
| 两条路径怎样并发和停止？ | 已整理的 [`run` 卡片](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126)及两个循环 | 按并发或退出的具体疑问回查，当前不作为先决问题 |

**本轮停止点**：能在骨架上找到“任务从哪里来、何时创建 Job、谁观察状态、状态交回哪里”。之后才选择局部问题，并从选定函数向下最多追两层。模板全部字段、Kubernetes 调度器、训练器内部和完整失败恢复暂不展开；骨架中列出函数不等于已经掌握或需要立刻建卡。

<details>
<summary>参考的 Slime scope、源码版本与裁剪边界</summary>

- [Slime Step 001](../../../../../slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md)：保留任务七项骨架，再定位一次请求、展开局部顺序和阅读导航。
- [Slime Step 012](../../../../../slime/topics/02-rollout-reward/steps/step-012-async-rollout-worker-loop/01-scope.md)：先区分后台生产与上层消费，再给出完整循环，最后选择局部观察点。
- [Slime Step 017](../../../../../slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/01-scope.md)：整体位置、连续交接骨架、局部入口与返回位置分层组织。
- Agent Lightning 固定提交：`0029dbb35c467799d35fee81d15d80264b0d1bd3`。本次骨架依据 `agentlightning/controller/k8s_reconciler.py`，无源码改动或真实集群运行。
- 调用树跨多层仅作职责定位；不是本轮已对所有函数完成逐层阅读。3.3 折叠类型转换、等待周期、日志、部分检查和异常处理；完整源码保留它们。
- 控制器重试、限速、停止响应和清理细节没有被此概览验证。当前使用本地 Markdown，不建立或构建 Hugo 页面。

</details>
