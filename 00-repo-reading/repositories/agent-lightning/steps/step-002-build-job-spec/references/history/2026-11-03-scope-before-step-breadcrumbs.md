# Step 002 · 从 rollout 与模板构造 Job 配置

[项目与唯一进度](../../../../README.md#current-reading) · [前一步：Job 事件接收与处理](../../../step-001-watch-job-events/README.md) · [最初的完整骨架](../../../step-000-k8s-controller-entry/01-scope.md#core-skeleton)

> 当前先准备本步 scope。具体字段示例与函数卡片在后续阅读时展开；本页不表示已经读懂、运行或验证了一次 Kubernetes 任务。

## 1. 阅读目标

- **整体目标**：把前两步的任务状态管理，接到 Agent 真正运行所需的 Kubernetes Job/Pod 配置。
- **本步问题**：一条 rollout 的任务输入与 Job 模板，怎样成为可以交给 Kubernetes 的 manifest？镜像、启动命令、任务关联标记与 Gateway 连接配置分别来自哪里？
- **停止位置**：能沿一份真实模板说明 `build_job_spec` 交出了什么，再带着返回值回到 `_create_job` 的提交位置。先不进入 Agent 内部执行、Trainer 更新或 Kubernetes 调度器源码。

沿用用户已确认的读法：先有骨架，一次进入一个函数；字段说明贴着实际 YAML/JSON 或代码出现。watch 的停止、重连与并发恢复继续保留为后续问题。

## 2. 指挥官函数、来路与最小前置

- **当前入口**：[`build_job_spec:43`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43)。它组织模板渲染、YAML 解析与配置补充，返回一份 Job 字典。
- **调用来路**：[`_create_job:259`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L259) 的 `manifest = build_job_spec(rollout, self._config)`。这是最初骨架里的 **[2] → [3]**；本步聚焦 [3]，创建函数的[已有记录](../../../step-001-watch-job-events/03-long-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md)只作来路与返回位置。
- **配套材料**：[`examples/swe_smith/job-template-openai.yaml`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/job-template-openai.yaml)。使用仓库真实的 Coding Agent 模板，不另造一个接口不同的示例。

进入时只需接住两项已有输入：`rollout` 带着任务输入和模板文本，`controller_config` 带着控制器的运行设置。本例模板会使用 `input.image_name` 与 `input.problem_statement`；值的具体展示留在函数卡片。

模板的最小来源关系已经核对：示例[训练配置:157–159](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/train_smith_agent.py#L157)指定文件路径，Trainer 侧[读取模板文本:283–284](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/agl_rollout_manager.py#L283)，再放入[创建 rollout 的配置:393–396](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/agl_rollout_manager.py#L393)。所以进入当前函数时，拿到的是 `rollout.config.k8s.job_template` 文本，当前函数不负责按本地路径打开模板文件。这条来源仅用于接入本步，暂不展开 Trainer 内部。

## 3. 核心骨架与阅读导航

### 3.1 在整体中的位置

保留最初 [1]–[5] 的全局编号；本步进入创建路径的 [3]，不改变此前函数的实际阅读历史。

```text
K8sReconciler.run()
|-- [A] _periodic_reconcile_loop()
|   `-- [1] _reconcile_once()
|       |-- _query_rollouts() + Job.async_list()
|       |-- no Job + QUEUING -> [2] _create_job()
|       |   |-- [3] build_job_spec() -> manifest   <-- Step 002
|       |   `-- Job(manifest, ...) -> await job.async_create()
|       |-- no Job + RUNNING -> [5] _patch_status(FAILED)
|       `-- existing Job -> [5] _patch_status(...) if needed
`-- [B] [4] _watch_jobs_loop()
    `-- _handle_job_event() -> [5] _patch_status(...)
```

这是职责与调用定位图；A/B 并行运行。Job 提交以后，由 Kubernetes 承接 Pod 与容器的运行，不能把容器里的 Agent 当成 `build_job_spec` 同步调用的下一层函数。

### 3.2 从输入到返回值的正常骨架

教学裁剪：假定模板存在，能渲染成一份 `kind: Job` 的 YAML；暂时省去校验、异常包装和具体字段值。以下 `...` 是对真实语句的省略，不是可执行示例，也没有引入新的包装函数。

```python
template = rollout.config.k8s.job_template if rollout.config.k8s else None
env = Environment()
env.filters["yaml_escape"] = ...          # 为模板准备转义工具
rendered = env.from_string(template).render(...)
docs = [doc for doc in yaml.safe_load_all(rendered) if doc is not None]
job = docs[0]                            # 模板文本成为待补充的 Job 配置

metadata = job.setdefault(...)
...                                      # 写名称、namespace 与任务关联标签
spec = job.setdefault(...)
...                                      # 设置重试、清理；有 timeout 时设置期限
pod_spec = spec.setdefault(...).setdefault(...)
...                                      # 设置 Pod 的重启策略

...                                      # 选 train/val，准备 Agent 访问 Gateway 的配置
for container in pod_spec.get(...):
    env = container.setdefault(...)
    ...                                  # 按名称添加或覆盖连接相关环境变量

return job                               # 返回给 _create_job 中的 manifest
```

此处 `job` 是配置字典。回到 `_create_job` 后，才会用它构造 kr8s Job 对象，并执行 `await job.async_create()`。字段的完整写法、同名 `env` 在不同位置的含义与具体数据变化，后续贴着对应代码解释。

<a id="reading-navigation"></a>

### 3.3 五个入口：从哪里看，读完回到哪里

下表的 **1–5 是本步局部阅读顺序**，整张表都服务于全局入口 [3] `build_job_spec`；它们不代表新增五个函数或五张函数卡。

| 顺序 | 代码入口 | 当前只弄清什么 | 返回或下一处 |
| --- | --- | --- | --- |
| **1 · 先看模板** | [Job 模板:4–23](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/job-template-openai.yaml#L4) | 哪个位置描述 Pod/容器，image、command、任务输入写在哪里；模板中的占位符等待谁填入 | 带着这份文本进入函数第 45 行，不进入启动命令所指的 Agent 实现 |
| **2 · 模板变成配置** | [build_job_spec:45–59](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L45) | 模板怎样得到 job_name 与 input，渲染和解析后交出哪份 Job 数据 | 回到 `job = docs[0]`，继续看这份数据被补充什么 |
| **3 · 补任务身份与运行约束** | [63–77 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L63) | 前面查询、watch、事件处理读过的名称和 labels 在哪里写入；哪些设置属于 Job，哪些属于 Pod 模板 | 沿同一个 `job` 进入容器配置；运行约束先知道用途 |
| **4 · 补 Gateway 连接信息** | [79–100 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L79) | 每个容器通过哪些 env 得到模型代理、事件上报地址和凭据；已有同名项怎样处理 | 回到 `return job`；Gateway 服务端内部不在本轮展开 |
| **5 · 带着 manifest 返回** | [101 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L101) → [_create_job:259–270](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L259) | 返回值怎样被接成 manifest、交给 Job 对象并提交 | 回到全局 [2]；本步到创建请求的交接处收束 |

**第一次只展开入口 1，再进入入口 2。** 不要求一轮讲完五段；每次都保留完整骨架，随后只打开当前需要的代码。

入口 1 中，模板的 [resources 与挂载:45–66](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/job-template-openai.yaml#L45)先定位即可。如果启动命令涉及的脚本路径无法解释，就最小回查对应挂载，再返回入口 1；不自动展开完整存储、权限或调度课程。奖励参数、完整 Agent 循环与镜像制作也暂时保留背景位置。

### 3.4 记录与本轮边界

当前只建立 scope，源码链接是后续阅读入口；没有预建 `build_job_spec`、模板处理或库函数的短期卡片。正式进入阅读时，再从 Step 001 的 `03 + 02` 完整继承累计记录，并按本步需要调取旧卡。

本函数的详细例子将保存在后续的单函数卡片；模板作为同一场景的输入材料。通用 Pod、资源、配置或卷知识继续归入项目已有的 [`k8s/`](../../../../../kubernetes/README.md)，项目标签与 Gateway 设置保留在本项目阅读记录。

<details>
<summary>源码版本与范围依据</summary>

- 本地源码：`/home/fredkeira/projects/agent-lightning`；2026-11-03 核对 HEAD 为 `0029dbb35c467799d35fee81d15d80264b0d1bd3`，工作区干净。
- 核心入口：`agentlightning/controller/k8s_reconciler.py:43–101`；调用方 `_create_job` 的构造与提交在 259–270 行。
- 配套输入：`examples/swe_smith/job-template-openai.yaml`；路径配置见 `examples/swe_smith/train_smith_agent.py:157–159`。
- 结构依据：[scope skill](../../../../../../../.agents/skills/repo-reading-scope/SKILL.md)与[局部导航 reference](../../../../../../../.agents/skills/repo-reading-scope/references/local-call-context.md)。
- [前一步提出本方向的依据](../../../step-001-watch-job-events/04-flow.md#next-topic-job-runtime) · [本轮 scope 创建记录](../../../step-001-watch-job-events/04-flow.md#step-002-scope-prepared)。
- 本次是范围与源码导航准备，没有渲染模板、提交 Job、运行 Agent 或建立 Hugo 页面。

</details>
