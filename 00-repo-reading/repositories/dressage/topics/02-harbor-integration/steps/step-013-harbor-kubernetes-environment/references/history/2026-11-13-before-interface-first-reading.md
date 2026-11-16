# 01 · Dressage Step 013：创建并启动 Environment，对齐 Agent Sandbox 能力

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [前一步总结](../../../step-012-task-agent-verifier/05-task-flow.md) · [下一范围](../../../step-014-model-routing-and-api-contract/01-scope.md)

> 状态：2026-11-13，用户确认开始本步；创建入口已讨论，BaseEnvironment.start 的接口已认清；当前停在第 3 项，下一处先定位目标 K8s 适配实现。通用创建与启动调用已讨论，具体后端操作与验证尚未展开。Harbor 依据 v0.25.0 固定发布提交核对，没有实际任务或集群运行。

## 1. 阅读目标

**沿 _init_agent_environment → 环境 start 看清后端选择与启动，再将命令、文件和停止合同映射到已有 Agent Sandbox 适配器。**

## 2. 指挥官、入口条件与边界

1. **入口**：接 Step 012 的 [Trial._init_agent_environment:1453](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1453)。这里创建本地 Environment 对象；实际启动在 Trial.run 的 _prepare 内，二者分开阅读。
2. **已有输入**：接住 Step 012 的运行配置、Task 与 Agent 对象；此前 hello-world / Docker 仅用于解释共同参数。后续实现阅读以 K8s / kubernetes-sigs/agent-sandbox 为目标，先看 BaseEnvironment 合同，再核对现有 UpstreamK8sSandbox 与 Harbor 的适配接缝；DockerEnvironment.start 不列为必读，不预设现有 K8s 类已直接接入 Harbor。
3. **停止位置**：明确环境对象的创建与 start 调用、exec/文件/stop 的接口映射及缺口；读取主线在环境启动和必要检查后返回 _prepare，随后进入 Step 014 的 Agent.setup。
4. **验证边界**：先准备或执行一题 Oracle/确定性任务的冷创建、文件/命令、评分与回收基线，已有证据可复用。WarmPool/Claim 作为下一轮热领取能力核对，不阻塞首次冷创建；不重写控制器。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

沿用 Step 010、011 的整体主线，各步保持相同图形结构。**本步展开 Trial 的环境对象创建与启动；对照 Agent Sandbox 接口，环境就绪后返回 _prepare 的 Agent 准备位置。** 具体入口与返回位置见 3.2；图中回调和 HTTP 均标明交互方式，不当作同一同步调用栈。

图内标注直接对应本步：**[本步]** 是当前展开位置，**[交给 Step …]** 是停止与交接位置；其余节点保留作整体背景。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> _CREATE_JOB(job_config)          # 创建 Job 时组成各次尝试的配置。
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> _run_trials_with_queue -> TrialQueue -> Trial.run  # [本步] Trial.create 内的 _init_agent_environment 创建后端对象（早于 Trial.run）。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start  # [本步] _prepare 中启动环境，核对就绪与超时。
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # [本步] 对齐 exec、文件与 stop 接口；做冷创建基线。
                           -> Agent.setup  # [交给 Step 014] 环境准备好后，从这里继续。
                      -> _run
                           -> _run_agent         # 把题目交给 Agent，执行中请求模型。
                           -> _collect_artifacts # 收集产物；按评测模式安排环境停止。
                           -> _run_verifier      # 使用题目的验证规则取得评分。
                      -> _finalize  # [本步按需回查] 环境停止合同；停止也可能已在 _run 中发生。
                           == END 事件 ==> plugin._on_end
                                            # 回调内部的轨迹处理留到实际接入时回查。
            <- JobResult
            -> plugin.on_job_end(...)           # 整份 Job 返回后的插件收尾。
            -> _bundle_samples                   # 训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

下面是普通单步任务的教学裁剪。按编号进入当前局部，弄清交接后回到真实调用方；前置回查、能力对照和验证不会冒写成一条连续执行栈。

**现在从哪里继续：**第 1、2、2.1 项的通用创建与启动调用已讨论，BaseEnvironment.start 的接口也已认清。接下来留在第 3 项，先定位目标 K8s 适配类，再看其实际启动、命令执行、文件传输和释放操作；抽象声明按接口对照即可，不要求逐个单开卡。第 4 项是后续运行验证，不是现在额外要读的一组函数。

**后端阅读边界：**目标是 K8s / Agent Sandbox。已读的 Docker 例子只帮助辨认输入；下一处从 BaseEnvironment 的 start/stop、exec 与文件接口接到实际 K8s 适配，不要求先读 DockerEnvironment.start。

```python
# 对象创建：由 Trial.__init__ 调用，仍未运行 Trial.run。
[1] Trial._init_agent_environment(...)  # 已讨论：配置到环境对象的交接。
  -> EnvironmentFactory.create_environment_from_config(...)
  -> self.agent_environment              # 后端对象已创建，尚不能据此认为容器已启动。

# 返回 Trial.create，队列挂接 hooks 后调用 Trial.run（已读路径）。
Trial.run -> Trial._prepare
  -> [2] _setup_agent_environment -> [2.1] _start_agent_environment  # 已讨论启动调用与超时。
       -> await self.agent_environment.start(...)
  -> run_healthcheck / _upload_injected_skills  # 已读，必要时核对环境能力。
  -> _setup_agent                         # 下一步 Step 014 接这里。

# [3] 能力对照，不是上面接着调用一遍所有接口：
BaseEnvironment.start  # 接口已认清；后续核对实际 K8s 实现。
后续按需核对 exec / 文件传输 / stop
  -- 待映射与验证 --> UpstreamK8sSandbox -> Agent Sandbox / Kubernetes
# [4] 用一个确定性任务验证冷创建和回收；模型接入不作为该基线的前置。
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. Trial._init_agent_environment · 已讨论主干 | [本步函数卡](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._init_agent_environment.md) · [调用方 Trial.__init__](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.__init__.md) | 看题目环境要求与运行后端配置怎样进入工厂，结果保存到 self.agent_environment；返回 Trial 初始化。工厂内部暂按接口，实际 start 留到第 2 项。 |
| 2. Trial._setup_agent_environment · 已讨论委派 | [本步函数卡](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent_environment.md) · [调用方 _prepare](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md) | 先看启动事件、计时与 await 委派；从 await 调用进入第 2.1 项。正常返回后，_prepare 继续健康检查、skills 与 Agent 准备。 |
| 2.1. Trial._start_agent_environment · 已讨论调用 | [本步函数卡](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._start_agent_environment.md) | 看环境 start 的 force_build 传参、wait_for 超时与异常转换；正常返回上层计时收尾，再回 _prepare 健康检查。具体后端实现尚未展开。 |
| <a id="current-reading"></a>3. K8s 实现与接口对照 · 当前待定位 | [本步函数卡](../../02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.start.md) · [现有 K8s 适配资料](../../../../../../references/agent-sandbox-harbor-compatibility.md) | start 接口已读。先确认实际选中的 K8s 适配类及配置入口，再看其启动、exec、文件传输、stop；这些是同一后端的职责，不要求逐个重读空接口。实现未找到时明确记录缺口，不假设已有可调用代码。 |
| 4. 冷创建与基本清理验证 · 待验证 | [Agent Sandbox 独立主题](../../../../../03-agent-sandbox/README.md) · [Job.run](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1082) | 选择一题确定性执行，观察创建、命令、文件、Verifier 与资源释放；本页准备不等于已运行，失败时只追相关接口。 |

**已知适配条件**：Harbor v0.25.0 的 start/stop/exec 与文件接口以当前基类为准；auto_mounts/auto_mounting、输出采集与共享/独立评测环境都要纳入合同。环境也可能在 SingleStepTrial._run 中停止，不只在 _finalize。

**复用边界**：已有 K8s 后端只选一个作接口参考；本地 Agent Sandbox 示例所指的 Harbor 适配目录此前未找到，不把类名写进配置就当作可用。详见[兼容性记录](../../../../../../references/agent-sandbox-harbor-compatibility.md)。Agent Sandbox 已有状态/Ready 知识继续复用；WarmPool/Claim、访问隔离按实际调用和故障回查。

**读后接续**：返回 Trial._prepare 的 _setup_agent，进入 [Step 014](../../../step-014-model-routing-and-api-contract/01-scope.md)；环境能力的最小验证与正式适配状态分别记录，不用继续通读控制器代替验证。

<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0）。2026-11-13 本轮已再次核对本地 /home/fredkeira/projects/harbor，使用 git show v0.25.0 读取固定源码；main 领先发布标签 123 个提交，不混用。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](2026-11-12-before-call-order-scope.md)完整保留。11-13 仅为实际进入的环境创建函数建卡，并调取调用方；其余未读函数仍只定位。

</details>
