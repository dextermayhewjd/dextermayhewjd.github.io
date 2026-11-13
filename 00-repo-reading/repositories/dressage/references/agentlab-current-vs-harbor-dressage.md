# 本地 AgentLab 与 Dressage × Harbor × Agent Sandbox 的区别

[评测体系范围](evaluation-system-scope-audit.md) · [环境兼容性](agent-sandbox-harbor-compatibility.md) · [项目阅读入口](../README.md)

2026-11-08，按用户要求检查 /home/fredkeira/projects/slime_api_data_collecting。固定提交为 151db30d1f4533773948695f4033ebe4353521d8，工作区干净。本次比较当前运行入口和实现，不把 README 的历史描述直接当作当前已接通能力；没有执行模型或集群实验。

## 1. 结论

**现有项目已经是一套自行编排的 Agent 运行与评测框架，并且已经接入 Agent Sandbox。新组合的主要变化，是把任务/尝试/Agent/评测编排更多交给 Harbor，把模型路由与轨迹产物更多交给 Dressage。**

它不是“当前只有 API 调用，换三件套后才有沙箱、预热和评测”。这些能力当前已有相当一部分。是否替换，应比较具体接口、行为和维护成本，而不是比较使用的框架数量。

## 2. 当前真实入口与执行过程

pyproject 的命令入口是 agentlab.cli:main，包目录是 src/agentlab。README 和 docs/architecture.md 仍包含旧 src/apilab、check_rollout/N1–N7 的描述，不能直接用这些旧路径说明当前 CLI。

以下是正常执行关系示意，不是可直接运行的代码：

```python
agentlab.cli.run_scenario
  -> load_scenario  # 组装 TaskRecipe、Verifier、Harness、SandboxFactory、TaskSpec。
  -> RolloutRunner.run_batch
       -> PrewarmStore  # 提前创建环境、recipe.setup、可选 prepare_fn。
       -> claim_next_ready  # worker 领取先准备好的任务。
       -> run_trial -> _attempt_once
            -> 探索环境 + Harness  # 白盒 ReAct 或容器内 CLI。
            -> recipe.extract_artifact
            -> 释放探索环境
            -> 新建评测环境 + verifier.verify
            -> 可选 adapter.finish_session
       -> results.json / 逐任务产物 / 可选 Sample 与 Trace 文件
```

代码入口：[run_scenario](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/cli.py:81)、[run_batch](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/orchestration/runner.py:273)、[_attempt_once](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/orchestration/runner.py:110)。

拟采用的另一条路线为：

```python
Harbor Job / Trial  # 承担批量尝试、Agent 与 Verifier 的生命周期。
  -> Harbor Environment 适配
       -> Agent Sandbox -> Kubernetes 环境
  -> Harbor Agent.setup / Agent.run
  -> Harbor Verifier
  -> Trial 结果与清理

Dressage Harbor 插件  # 在上述生命周期挂接模型路由和结果/轨迹提交。
  -> Gateway / Proxy
  -> ArtifactStore
  -> 需要训练时转换为 Slime Sample 组
```

## 3. 逐项比较

| 维度 | 当前 AgentLab | 三件套路线意味着什么 |
| --- | --- | --- |
| 任务编排者 | 自有 RolloutRunner、RunnerConfig、TrialResult | Harbor Job/Trial 承担对应职责；不宜再包一层 AgentLab runner 重复重试、评分和回收 |
| 任务格式 | 自有 TaskSpec/TaskRecipe/Artifact/Verifier；JSONL/Parquet 与 smoke fixtures | 转为或接入 Harbor Task、Agent、Verifier 约定，复用其任务生态 |
| Agent 接入 | 自有白盒 ReAct；Claude/Codex 等较薄的 CLI 包装 | 主要复用 Harbor 的 Agent.setup/install/run，实现差异仍需验证 |
| 沙箱 | 已有 Agent Sandbox SDK 适配，以及直接创建 Sandbox/Claim 的分支；另有 InMemory | 仍可使用同一底层 Agent Sandbox，但外层合同要从 Slime 风格 Sandbox 映射成 Harbor Environment |
| 预热 | 提前准备具体 TaskSpec 的环境、任务工作区和可选 CLI 准备；按 ready 队列领取 | Agent Sandbox WarmPool 提供模板级备用环境；Harbor 的任务/Agent 准备要另接。它不会自动继承 AgentLab 的任务预热语义 |
| 模型调用 | CLI 主入口可直接使用 OpenAI/Anthropic API 白盒调用；另有 Slime API 生成替换函数 | Dressage 插件接 Gateway/Proxy，并要求会话与轨迹控制接口，不能只替换 URL |
| 结果与轨迹 | 自有 JSON、pass@k、偏好配对、可选 Slime Adapter 导出与 Trace | Harbor 提供 Trial/Job 结果，Dressage 管尝试身份、产物提交和训练输出；需对齐旧报告字段与去重规则 |
| 恢复与失败 | 自有基础设施重试、结果文件跳过与合并、可选背压 | 采用 Harbor/插件的尝试与结束语义；当前 Dressage Harbor 插件拒绝 Job resume，并不是所有能力都自动更强 |
| 维护成本 | 单项目内较直接，但任务规则、Agent 包装、队列与结果协议要自行维护 | 可复用更多生态实现，同时增加多仓版本、事件和协议兼容的工作 |

## 4. 当前已有的实质能力

1. **模块化任务与评测分工。** [contracts.py](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/tasks/contracts.py)定义 TaskSpec、Artifact、TaskRecipe、Verifier；代码任务在独立评测环境中应用提取出的 patch 再评分。
2. **实际存在的预热和 ready-first 派发。** [PrewarmStore](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/orchestration/prewarm.py:65)先完成环境与 recipe.setup，调用可选 prepare_fn；run_batch 的 worker 领取 ready 队列结果。不能为了“获得预热”就认定必须换成 Dressage 原生 worker。
3. **已经有 Agent Sandbox 接入。** [K8s 适配](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/sandboxes/k8s/adapter.py:62)有 Provider、SDK 和 direct 分支。保留它们中经过验证的底层能力，通常比重新写控制器合理；但分支参数语义不能视为完全相同。
4. **基本批量统计与持久化。** [metrics.py](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/observability/metrics.py:47)有 pass@k、筛选与偏好配对；[persistence.py](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/orchestration/persistence.py:15)有批次、逐任务产物和可选 Trace/Sample 文件。

src 中没有直接 import harbor 或 dressage，pyproject 也没有将它们列为依赖。源码注释中的“借鉴 Harbor/Dressage”表示参考设计，并不等于当前执行实际由这两个框架驱动。

## 5. 必须区分“有组件”与“当前入口已接通”

### 5.1 默认 CLI 并未接好可选的轨迹 Adapter

run_scenario:125 创建 RolloutRunner 时只传 recipe、verifier、sandbox_factory、harness，没有传 adapter。_attempt_once 仅在 adapter 不为 None 时调用 open_session / finish_session；因此当前这条默认入口不会通过该接口生成完整 Slime Sample。

另外存在的 [make_call_api_generate](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/models/api_backend.py:201)是 Slime 生成函数的替换工厂，不是默认白盒 API 路线本身；它当前只接受 anthropic 配置。其输出使用目标 tokenizer 重编码，并把 output_log_probs 填为 0.0，不能解释成服务商真实采样 token/logprob 或 on-policy 训练证据。

没有真实 samples 时，持久化代码还可能为 Trace viewer 保存只带基础字段的 dummy sample。因此有 .pt 文件或可打开时间线，不等于已经有训练轨迹。

### 5.2 多场景存在，但真实数据接入范围不同

[registry.py](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/tasks/registry.py:167)当前只有 SWE 构建器使用 data_path 读取真实 JSONL/Parquet。Search、Tau、ReTool 构建器使用内置 smoke specs 与 InMemorySandbox；它们的 recipe/verifier 是真实代码，但不能据此宣称已直接跑通各官方 benchmark 的全部真实环境。

HarnessRegistry 中注册了多个名字，但场景装配器明确分派的 CLI 主要是 Claude/Codex；其他注册项是否经过同一个命令入口要逐项核对。

### 5.3 恢复与失败行为应按代码验收

- [checkpoint.py](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/orchestration/checkpoint.py:25)按 results.json 中出现的 task_id 跳过，包含成功和失败记录；当前批次汇总在 run_batch 结束时保存。这不等于每个任务的事务性 checkpoint 或进程崩溃后的完整恢复。
- run_trial 捕获 BaseException 并可能转换为失败 TrialResult，包括取消异常；它与向外传播取消的语义不同，应有单独验证，不能仅凭注释宣称零资源泄漏。
- SWE factory 在部分创建错误时可回退 InMemory；白盒 API 的部分 HTTP 错误可被表示为 finished 消息。正式评测需要明确这些场景究竟算基础设施错误、终止还是低分，避免汇总口径混淆。
- BackpressureGuard 等组件存在，但当前 CLI 不直接注入它；配有该对象的测试或自定义调用不能自动代表默认入口已经启用。

这些是静态检查发现的接口和行为边界，不是本次跑出的故障报告，也不是完整代码审计。

## 6. 对迁移决策的含义

1. **已有项目应作为基线保留。** 不需要为了使用三个框架而从头重做已有预热、K8s 与评测分工。
2. **引入 Harbor 的主要价值是减少自维护的任务/Agent/尝试协议。** 代价是把 TaskSpec/recipe、评分与结果语义映射到 Harbor，而不是简单增加一个依赖。
3. **引入 Dressage 的主要价值是其模型路由、轨迹和尝试产物的配合。** 默认 Proxy 与当前 API 后端并不直接兼容；商业 API 采集和训练数据能力分别验收。
4. **同一条运行路径只选一个编排者。** 若采用 Harbor Job/Trial，旧 RolloutRunner 保留为独立基线或其他用途，不让两层同时创建环境、重试和评分。
5. **用同一道题比较两条路线。** 复用相同任务、镜像、Agent/模型和评分规则，核对结果、错误分类、清理及可观测性，再判断哪些迁移带来价值。不先承诺吞吐或质量提升。

对于岗位目标，现有项目已经包含可说明的框架工程内容；把当前真实主链、已接通能力和未接通边界讲清楚，比仅增加框架名更重要。

## 7. 证据与未验证范围

- 本轮按 pyproject → CLI → registry → runner → harness/环境/评测 → persistence 追踪正常路径，并读取相关单元测试。没有执行整套测试、部署或模型请求。
- 当前 checkout 有 25 个 tests/test_*.py 文件和 15 份 docs/reports Markdown。测试既有 mock/provider 委派，也有需要 APILAB_E2E 开关、真实数据与集群的用例；不能把测试文件存在当作已通过。
- [2026-10-16 故障回收报告](/home/fredkeira/projects/slime_api_data_collecting/docs/reports/2026-10-16-kind-failure-cleanup.md)、[2026-10-28 MiniMax 报告](/home/fredkeira/projects/slime_api_data_collecting/docs/reports/2026-10-28-minimax-swe-evaluation-report.md)记录了历史运行与现象。本轮保留这些既有经历，不推断用户没有做过实践。
- 当前机器的该 checkout 没有对应 runs/ 原始产物、data/mimo/tasks.jsonl 或 .venv，两个 third_party submodule 也未初始化；本轮不能复验报告指标或把旧 apilab 版本的结果直接等同于当前 agentlab 主入口。
- 对照组合仍采用既有固定版本的 Dressage/Harbor/Agent Sandbox 分析；[适配模块缺失与版本冲突](agent-sandbox-harbor-compatibility.md)没有因为本次比较而消失。
- 本轮没有修改 slime_api_data_collecting、Dressage 或 Agent Sandbox 的业务源码。
