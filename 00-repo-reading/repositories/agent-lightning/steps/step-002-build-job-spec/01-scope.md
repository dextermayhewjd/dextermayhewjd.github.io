# Step 002 · 进入 build_job_spec：构造 Job 配置

> **调用链面包屑**：[Step 000：_reconcile_once](../step-000-k8s-controller-entry/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#call-create-job) → [已读的 _create_job（本步调取）](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md#call-build-job-spec) → **[Step 002：build_job_spec](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/build_job_spec.md)** → 带回 manifest，继续 _create_job。

[项目与唯一进度](../../README.md#current-reading) · [前一步 Step 001：watch 事件路径](../step-001-watch-job-events/README.md)

**本步正在进入的具体函数是 `build_job_spec`。** `_create_job` 是已读的调用方；`_watch_jobs_loop` 是 Step 001 的背景路径。已按用户选择建立[函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/build_job_spec.md#template-input)，当前从取得模板输入开始。

## 1. 阅读目标

- **问题从哪里来**：Step 000 读 `_create_job` 时，已经看到它取得 manifest 并提交 Job；当时把 `build_job_spec` 当作“生成 manifest”的接口，没有展开这份配置怎样形成。
- **本步要回答**：打开那次 `build_job_spec` 调用，看 rollout 与模板怎样成为 Job 配置，特别是镜像、启动命令、任务标记和 Gateway 连接信息的来源。
- **停止位置**：带着返回的 Job 字典回到 `_create_job` 的 `manifest = ...`，接上后面的创建请求。Agent 内部执行和 Kubernetes 调度器源码留在本步边界外。

## 2. 当前函数与它的调用位置

- **当前函数**：[build_job_spec 函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/build_job_spec.md)；[源码 43–101 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43)，位于 `agentlightning/controller/k8s_reconciler.py`，是模块级函数。
- **从这里进入**：[`K8sReconciler._create_job:259`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L259) 调用 `manifest = build_job_spec(rollout, self._config)`。
- **这次交接**：调用方交入当前 rollout 和控制器配置；本函数返回 Job 配置字典，调用方用 `manifest` 接住。真正发出创建请求的是调用方后面的 `job.async_create()`。

当前函数负责组织模板渲染、YAML 解析和配置补充，因此本步在它内部逐段读。模板是它收到的一份输入材料，挂在这个函数下面回查。

## 3. 核心骨架与阅读导航

### 3.1 三个 Step 分别位于哪里

下面直接标 **Step 编号**。旧 scope 的 `[1]–[5]` 是当时的函数阅读路标，本页不再用它们充当当前定位。

```text
K8sReconciler.run()
|-- _periodic_reconcile_loop()
|   `-- _reconcile_once()                         [Step 000]
|       |-- query rollouts + list Jobs
|       |-- no Job + QUEUING -> _create_job()     [Step 000: caller]
|       |   |-- build_job_spec() -> manifest     [Step 002: current target]
|       |   `-- Job(manifest, ...) -> await job.async_create()
|       |-- no Job + RUNNING -> _patch_status(FAILED)
|       `-- existing Job -> _patch_status(...) if needed
`-- _watch_jobs_loop()                            [Step 001]
    `-- _handle_job_event() -> _patch_status(...)
```

所以，本步是**回到 Step 000 的创建分支，打开此前没有展开的子函数**。Step 001 的 watch 与周期协调并行运行；它不是当前函数的调用来源。

<a id="caller-breadcrumb"></a>

### 3.2 先回到已读调用点，再打开右侧的函数

> [Step 000：没有 Job 的 QUEUING 分支](../step-000-k8s-controller-entry/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#missing-job-branch) → [`await self._create_job(rollout)`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L181) → **打开下面第一行右侧的 `build_job_spec`**。

这是 `_create_job` 中与本步有关的连续交接，省略中间日志、attempt_id 读取及异常包装：

```python
# 调用方：K8sReconciler._create_job
manifest = build_job_spec(rollout, self._config)  # 259：Step 002 从这里下钻
api = await self._get_k8s_api()
job = k8s_objects.Job(manifest, api=api)
await job.async_create()
```

进入 `build_job_spec` 后，调用方暂时等待返回值。读完后回到这同一行，用返回的字典完成 `manifest` 赋值，再继续获取客户端和提交 Job。这个来回始终围绕一次创建调用。

<a id="build-job-spec-skeleton"></a>

### 3.3 现在站在 build_job_spec 内部

教学裁剪：假定模板存在且能得到一份 Job YAML，省略校验和具体字段值。保留真实函数名、处理顺序和返回位置；`...` 表示省略的原语句，这不是可执行示例。

```python
def build_job_spec(rollout, controller_config):
    template = rollout.config.k8s.job_template if rollout.config.k8s else None
    env = Environment()
    env.filters["yaml_escape"] = ...
    rendered = env.from_string(template).render(...)
    docs = [doc for doc in yaml.safe_load_all(rendered) if doc is not None]
    job = docs[0]

    metadata = job.setdefault(...)
    ...                                  # 补名称、namespace 与任务关联标签
    spec = job.setdefault(...)
    ...                                  # 补 Job 的运行约束
    pod_spec = spec.setdefault(...).setdefault(...)
    ...                                  # 补 Pod 的重启策略

    ...                                  # 准备 Agent 访问 Gateway 的配置
    for container in pod_spec.get(...):
        env = container.setdefault(...)
        ...                              # 按名称添加或覆盖容器环境变量

    return job                           # 回到 3.2：由 manifest 接住
```

这里的 YAML 模板和中间变量，后续都在相应语句旁解释。返回的 `job` 是配置数据；本函数的输出并不表示 Kubernetes 已创建或运行了它。

<a id="reading-navigation"></a>

### 3.4 沿面包屑逐段读，模板从使用处回查

下面的①–⑤只是 **build_job_spec 这一轮的局部导航**，与 Step 000/001/002 的步骤编号分开。

| 局部入口 | 代码位置 | 当前看清什么 | 读完回到哪里 |
| --- | --- | --- | --- |
| **① 找回调用点** | [_create_job:259](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L259) | 本步为何出现，交入什么、等待什么返回 | 打开右侧调用，进入 build_job_spec 第 43 行 |
| **② 接住模板输入** | [build_job_spec:45](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L45) | `template` 从 rollout 的哪个字段取得 | 需要看具体内容时，打开[真实模板:4–23](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/job-template-openai.yaml#L4)，看 image、command、任务输入；读完回到本函数第 49 行 |
| **③ 得到 Job 字典** | [49–59 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L49) | 模板如何使用 job_name/input，怎样渲染和解析 | 带着 `job = docs[0]` 得到的配置，进入第 63 行 |
| **④ 补身份与运行约束** | [63–77 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L63) | 前两步读过的任务标签在哪里写入；哪些设置属于 Job，哪些属于 Pod 模板 | 沿同一个 job 进入第 79 行；具体键与数据放在函数卡里 |
| **⑤ 补连接信息并返回** | [79–101 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L79) | 容器 env 怎样补入 Gateway 连接信息，最终交出什么 | 返回上方 3.2 的 manifest 赋值，再接到调用方的创建请求 |

**第一次从①进②。** 模板是②的回查分支，读完要返回 `build_job_spec`；它不再作为一个与当前函数脱离的起点。

模板的 [resources 与挂载:45–66](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/job-template-openai.yaml#L45)先定位。若②中启动命令的脚本路径不清楚，最小回查其挂载后回到②；奖励参数、完整 Agent 循环、镜像制作和 Kubernetes 调度内部按后续问题取舍。

### 3.5 当前准备到什么程度

本轮已从 scope 准备转入用户明确选择的函数阅读。Step 001 的 `03 + 02` 已合并为本步八份累计函数记录；短期目录调取 `_create_job` 并新增 `build_job_spec`。已从模板输入按实际疑问接到两处 env、Gateway 地址与镜像引用，其他阶段仍按骨架逐段展开；原话、未知与来源继续区分。

<details>
<summary>模板来源、版本与本轮纠正依据</summary>

- 固定源码：`/home/fredkeira/projects/agent-lightning`，提交 `0029dbb35c467799d35fee81d15d80264b0d1bd3`。
- 模板的输入来源：示例[训练配置:157–159](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/train_smith_agent.py#L157)指定路径；Trainer 侧[283–284 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/agl_rollout_manager.py#L283)读取文本，再放入[rollout 创建配置:393–396](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/agl_rollout_manager.py#L393)。当前函数取得的是模板文本。
- 结构依据：[scope 的局部导航](../../../../../.agents/skills/repo-reading-scope/references/local-call-context.md)与[已认可的面包屑 reference](../../../../../.agents/skills/repo-reading-short-term-memory/references/breadcrumb-navigation-and-shared-infra.md)。
- [修订前 scope](references/history/2026-11-03-scope-before-step-breadcrumbs.md) · [首次创建记录](../step-001-watch-job-events/04-flow.md#step-002-scope-prepared) · [本次定位纠正](../step-001-watch-job-events/04-flow.md#step-002-breadcrumb-correction)。
- [本步正式开始与继承记录](04-flow.md#build-job-spec-start)。局部模板渲染和 env 处理已按[本轮问题](04-flow.md#template-env-url-image)作隔离验证；未执行完整函数、提交 Job 或建立 Hugo 页面。

</details>
