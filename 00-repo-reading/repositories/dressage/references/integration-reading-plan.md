# Slime、Dressage、Harbor 与 Agent Sandbox：接入阅读规划

[项目入口与唯一进度](../README.md) · [研究依据与版本](agent-sandbox-harbor-integration-research.md) · [Step 005：执行前准备](../topics/01-native-agent-rollout/steps/step-005-agent-registration/01-scope.md)

2026-11-12 更新：[012–017 scope 已按调用交接调整](#call-order-scopes-applied-20261112)。下文早期规划保留历史，当前入口与边界以各步 scope 和项目唯一进度为准。

2026-11-07，按用户确认保存。本页负责后续阅读顺序、重点和停止位置；研究细节留在研究报告，实际进度只在项目 README 维护。下面的编号是规划顺序，不是预先创建的 Step，也不表示相关函数已读完。

2026-11-08 的[topic 与逐步 scope 划分](topics-and-step-scopes-after-step006.md)进一步给出各单元的编号、主读入口和停止标准，仍沿用本页的整体顺序。用户随后授权准备所有后续 scope 并按 topic 归档；新步骤仅有范围文件，不表示已阅读或已实施。

用户随后确认的[跨 topic 阅读与实施顺序](../README.md#confirmed-reading-and-implementation-route)集中保存在项目入口：Step 013 转入 Agent Sandbox 后回到同一步，Step 017 接到现有项目的整合与验收，不另起一套实时进度。

后续兼容性核对发现适配实现缺失和版本基线冲突，针对“优先实际接入 Agent Sandbox”的[最小阅读与验证建议](agent-sandbox-harbor-compatibility.md#integration-first-reading)已单列：先核对版本、生命周期与 Environment 合同，并尽早验证冷创建。下文保留已确认的完整学习顺序，不把它解释为开始接入前必须全部读完；尚未据此重编号或自动切换实际进度。

## 1. 目标与分工

用户于 2026-11-08 重申，最高目标是腾讯混元 Agent 强化学习框架岗位。本页的接入工作是其中一个工程案例：用于检验接口设计、任务/评测扩展、K8s 运行和失败处理。此前“优先实际接入”的顺序只适用于该子任务，不覆盖岗位主线，也不要求为完成三个框架的组合而无限扩展兼容工作。

**在现有 slime_api_data_collecting 项目基础上，复用现成框架完成 K8s 沙箱、不同任务与 Agent、模型调用及结果采集的接入。** 能复用的直接复用，新增代码集中在接口不兼容的地方。

| 组件 | 在目标方案中的职责 |
| --- | --- |
| Slime | 提供已有的数据与扩展接口；需要训练时作为外层调用方消费 Sample |
| Dressage | 用已有 Harbor 集成连接执行、模型路由、轨迹和结果；需要时桥接成 Slime 的批量输出 |
| Harbor | 管理 Task、Agent、Trial、Verifier，以及该条执行路线的并发和重试 |
| Agent Sandbox | 管理 Kubernetes 中的环境创建、就绪、预热、领取和回收 |
| 当前项目的适配代码 | 连接 Harbor 环境接口与已有 K8s 能力，校准商业模型 API、采集和报告的交接 |

Harbor 与此前对话中的 harbour 按同一 Agent 评测框架理解。

## 2. 始终保留的整体位置

```text
Slime
  -> Dressage.generate_rollout_harbor_sync
       -> Harbor Job / Trial
            -> Environment
                 -> K8s 环境适配
                      -> Agent Sandbox -> Pod
            -> Agent.setup / Agent.run
            -> Verifier.verify
            -> 环境停止与 Trial 结果
       <- 执行结果与 Dressage 插件关联的轨迹
       -> 转换为 Sample 组
  <- RolloutFnTrainOutput
```

这是接回 Slime 时的职责图，不是完整的同步调用栈。Dressage 插件在 Trial 生命周期中挂接模型路由和采集；模型请求实际发生在 Agent 运行期间。

当前项目只运行 API 模型评估时，可以直接作为 Harbor Job 的调用方，不必启动 Slime 训练。短读外层 Slime 接口是为了保留整体位置，不把完整训练部署变成搭平台的前置。

此前的 `blackbox_dispatch.generate → Paddock → BlackboxServer` 是另一条原生执行路线。先给它收尾，作为已有背景；不把它串到每个 Harbor Trial 里面再次执行。

## 3. 固定阅读顺序

### 3.1 先给旧 blackbox generate 做主线收尾

入口：[blackbox_dispatch.generate](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L116)。

已读的环境取得、身份和注册准备作为背景；返回调用方后，依次补清：

1. `call_agent` 怎样交回结果，`agent_response` 从哪里取得。
2. `after_agent` 在什么时间执行，负责什么后置操作。
3. `finalize_session` 怎样收尾会话。
4. `read_trajectory` 怎样取回已经产生的轨迹。
5. `expand_segments_to_samples` 怎样把轨迹段转成 Sample。
6. `finally` 怎样安排回收，取消和普通失败怎样影响返回。

**停止位置：** 能把“执行 → 结果 → 轨迹 → Sample → 回收”连起来。子调用先看用途和交接，不为全部 helper 建卡；没有展开的内部机制明确留白。完成这次收束不等于原生黑盒体系已全部掌握。

### 3.2 再从 Slime 进入 Dressage 的 Harbor 批量入口

入口：[训练脚本的 hook 配置](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh#L66) → [generate_rollout_harbor_sync](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1257)。

1. 区分单条 `--custom-generate-function-path` 与整批 `--rollout-function-path`。
2. 看清输入来自 `HarborDataSource`，返回为含 Sample 组的 `RolloutFnTrainOutput`。
3. 沿 `_run_harbor_rollout → _run_partition` 定位 Harbor Job 的创建和运行；先折叠训练校验及复杂分组细节。

**停止位置：** 能指出 Slime 在哪里调用 Dressage，Dressage 又在哪里交给 Harbor。此处只建立外层导航，不重读整套 Slime rollout。

### 3.3 沿 Harbor Trial 看执行，并定位 Dressage 插件

入口：[Trial.run](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L345)；对照 [DressageHarborPlugin.on_job_start](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L261)。

1. 跟随 `_prepare → _run → _finalize`，分清 Task、Agent、Environment、Verifier。
2. 看任务与 Agent 配置怎样生成一次 Trial；先选一道题和一个 Agent。
3. 在 Agent.setup 中定位安装与配置，知道可以复用 Harbor 的现成实现。
4. 只在对应事件位置看 Dressage 插件怎样挂接模型路由、结果和取消回调。

**停止位置：** 能说明一次尝试的完整生命周期，以及换题、换 Agent 分别改什么。Claude 走一条代表路径，Codex 按差异回查；不通读全部 Agent。

### 3.4 重点完成 Environment 与 Agent Sandbox 的接缝

入口：[Harbor BaseEnvironment](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L892) → [现有 UpstreamK8sSandbox](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/sandboxes/k8s/adapter.py:100)。

1. 映射环境创建、就绪、命令执行和删除。
2. 映射工作目录、环境变量、执行用户、超时、退出码与输出。
3. 补齐 Harbor 使用的单文件及目录上传、下载。
4. 先验证冷创建的一条完整路径。
5. 再接既有 Agent Sandbox 主题的 WarmPool／Claim，验证提前准备、独立领取与释放。备用环境 Ready 不等于题目和 Agent 已全部初始化。

**停止位置：** 有清楚的接口映射和待补项，能够进入一题的接入验证。K8s 已读的 Pod、Ready、状态写回继续复用；具体进度仍由 Agent Sandbox 项目入口维护。

### 3.5 最后连接模型 API、采集和结果返回

入口：[路由注入](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1031) → [ProxyClient](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L42)；结果侧对照 [HarborArtifactStore](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L256) 与 [_bundle_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L624)。

1. 确定 Agent 的模型请求经过哪里，以及 Trial、attempt、session 怎样关联。
2. 将现有商业模型 API 后端与 Dressage 所需协议逐项对照。
3. 区分 Agent 结果、Verifier 奖励、轨迹与最终 Sample。
4. 追踪一次失败或取消，明确环境清理、模型路由关闭和结果提交各由谁负责。

**停止位置：** 能验证一次真实请求和一次结果收尾；没有真实 token/logprob 等信息时如实保留缺失，不能用字段形式一致代替训练语义正确。需要训练时才继续深入分段权重和训练校验。

## 4. 旧知识怎样接到新路线

| 已接触的原生 generate 职责 | Harbor 路线中的对应位置 |
| --- | --- |
| `paddock.init` | `Environment.start` 与 K8s 适配 |
| `register_agent / call_agent` | Harbor Agent 的 `setup / run` |
| `finalize_session / read_trajectory` | Dressage Harbor 插件与采集接口 |
| `expand_segments_to_samples` | Dressage Harbor rollout 的结果转换 |
| `finally` 回收 | Harbor 管环境，Dressage 插件管路由和采集资源 |

这张表只对应职责，不表示两套对象和方法可以直接互换。

## 5. 执行规划时保留的边界

1. **按用户最新要求，后续步骤先只准备 scope。** 已按 topic 建立范围与导航；函数卡、长期继承、形成过程和总结在实际进入时再生成。新问题优先挂回当前主线，不把目录存在当作阅读完成。
2. **先收尾，后转线。** 先完成 3.1 的原生 generate 主线收尾，再转入 Harbor 接入。具体步骤是否开始或收束，以项目入口的唯一进度为准；各步骤的未知继续保留，不因为规划已保存就标为完成。
3. **版本和依赖按研究报告核对。** Dressage 固定 Harbor 0.18.0；Agent Sandbox 的 Harbor 示例版本不同且当前 checkout 缺引用的集成模块，不能作为开箱即用依赖。
4. **商业 API 接入不是改 URL。** 模型调用、会话收尾和轨迹读取合同分别验证；K8s 环境接通不等于采集链路也接通。
5. **不用完成全部阅读才开始局部验证。** 第 3.4 项已有明确合同后即可做环境闭环；完整整合完成仍需第 3.5 项的验证。

各项技术依据、源码版本、兼容性缺口和验收案例统一查[研究报告](agent-sandbox-harbor-integration-research.md)，本页不另维护一份实现完成清单。


<a id="steps012-017-review-20261112"></a>

## 2026-11-12：Step 012–017 顺序与边界复核（建议，未重排 scope）

用户要求重新评估后续六步。核对当前 scope、Harbor v0.25.0 发布源码及 Dressage 固定源码后，建议保留 012 → 013 → 014 → 015 → 016 → 017 的编号与主题顺序；它是阅读路线，不是所有真实函数按此顺序调用，也不是读完六步才能动手。当前 Step 012 已按 0.25 校准，013–017 尚有 0.18 来源与旧粒度，不能直接视为全部已经适配新版。

| 步骤 | 合理的核心问题与停止位置 | 建议修正的边界 |
| --- | --- | --- |
| 012 任务、Agent、Verifier | 同一个 hello-world：知道题目文件、Agent 选择、验证规则在哪里，以及怎样组成尝试配置 | 保留已开始的 JobPlan 卡；用具体题目接回抽象，不重读已在 011 核对的 setup/install/生命周期。配置对象与运行对象、两类 TaskConfig 分开 |
| 013 Environment 与 Agent Sandbox | 映射 start/exec/文件/stop，完成或明确准备一题冷创建基线 | 目标已经是 Agent Sandbox，其他 K8s 后端仅选一个作参考；镜像、网络、超时与释放合同要覆盖。WarmPool/Claim 的优化阶段不阻塞第一次冷创建验证 |
| 014 模型与路由 | 从一个实际 Agent 请求，接清地址注入、会话身份和模型响应 | 保留在环境主线之后阅读；但实施前应先做一次模型/Proxy 合同可行性检查。商用 API 到完整 Dressage Proxy 的改造不能自动变成默认必修 |
| 015 轨迹、奖励与训练输出 | 一次实际尝试的结果与 Proxy 轨迹怎样对应并提交，若需要训练再核对 Sample 语义 | Step 007/008 的通用 finalize/read、分段转换和 Step 010/011 的归组、manifest 职责复用，只读 Harbor 特有身份映射与提交边界 |
| 016 取消、失败与重试 | 选一种故障，核对环境/路由/结果三方收尾与最终状态 | 基本 stop/超时验证应已随 013 开展；此步扩为组合系统的一个故障场景。外部取消、普通执行失败、超时不能画成一条必然重试链 |
| 017 整合与复跑证据 | 汇总前面的小验证，用固定任务、配置和版本再跑一次闭环 | 不作为第一次运行；它负责整合回归和证据记录，不要求在此才首次尝试冷创建、模型连通或清理 |

### 已核对到的两处具体流程问题

- **Step 013** 目前将 EnvironmentFactory.create_environment_from_config 画在 Trial._prepare 下。v0.25.0 中，Agent 环境对象在 Trial._init_agent_environment（trial.py:1453 起，工厂调用:1464）创建；_prepare:641 经 _setup_agent_environment/_start_agent_environment 执行 start。需分开“创建本地环境对象”和“实际启动环境”。停止也可能发生在 SingleStepTrial._run 中，不只在 _finalize。
- **Step 016** 当前图在 CANCEL/END 后接“按策略创建新的尝试”，容易让人理解为取消后自动重试。v0.25.0 Trial.run 的 CancelledError 分支会重新抛出，队列 _execute_trial_with_retries 没有在该 await 外捕获取消；其重试判断针对返回的 TrialResult.exception_info。后续应选一个具体场景画实际路径，不能把所有失败出口合并。

### 建议的实践穿插，不增加新必读章节

012 固定任务与评分规则 → 013 冷创建/命令/文件/停止小验证 → 014 一条真实模型请求 → 015 同一次尝试的结果和轨迹对齐 → 016 一次可控失败 → 017 整合复跑。若某环节已有等价运行证据，复用即可；没有运行条件时记为待验证，不用更多源码通读代替。

开始组合实施前，复用既有兼容性检查：Dressage 的 Harbor 0.18 精确限制、目标 0.25，以及 Agent Sandbox 例子所引用适配实现的缺失。Harbor + Agent Sandbox 的独立冷创建验证无需先完成全部 Dressage 商用模型代理适配；三方完整联通则必须验证这些接口。固定一个目标版本，先明确评测产物还是训练产物所需合同，避免同时改环境、模型协议、存储和训练转换。

本次仅保存评估，没有修改六步正式 scope 或改变当前阅读位置，也没有安装、运行模型或操作集群。源码证据来自 Harbor 发布提交 fdba28fc411e47e8765420a1a063b4918fce3def 的 trial/trial.py、trial/queue.py、environments/factory.py、environments/base.py；以及 Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c 的 plugin.py、artifacts.py、gateway.py、compat.py。


<a id="call-order-scopes-applied-20261112"></a>

## 2026-11-12：按调用交接更新 012–017 scope

用户要求重构阅读顺序及各步 scope。保留编号、目录和共同 3.1 主图，改变 3.2 的入口、返回点和停止范围：012 配置/任务/Agent 对象 → 013 环境对象创建与实际启动 → 014 Agent.setup/run 及运行中的模型请求 → 015 日志/产物、Verifier、END 轨迹提交与正常返回。016 是对正常链的一次故障回看，017 是整合与复跑，不宣称六步构成一条完全线性的程序调用栈。

014 的路由配置与 START/AGENT_START 属于更早发生的前置，只为当前模型请求按需回查；013 的 stop/文件/exec 接口为能力合同回查。小验证分别在 013–016 进行，017 整合证据。具体内部函数不因出现在骨架上就预建卡片或成为必须通读内容。

各 scope 旧稿保存在本步 references/history/2026-11-12-before-call-order-scope.md；Harbor 源码入口按 v0.25.0 发布标签核对，Dressage 版本限制与实际集成验证另行处理。当前仍在 Step 012 的 JobPlan.build_trial_configs，未启动后续步骤或执行安装、模型和集群操作。
