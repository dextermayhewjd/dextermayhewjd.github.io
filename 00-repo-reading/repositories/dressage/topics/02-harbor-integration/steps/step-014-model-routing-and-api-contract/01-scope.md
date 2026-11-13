# 01 · Dressage Step 014：准备并运行 Agent，接清运行中的模型请求

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一范围](../step-013-harbor-kubernetes-environment/01-scope.md) · [下一范围](../step-015-harbor-results-and-samples/01-scope.md)

> 状态：2026-11-12 按真实调用交接调整。本页是已确认的后续 scope；本轮只更新范围与导航，尚未开始本步阅读或创建函数卡。 Harbor 入口统一依据 v0.25.0 发布版；没有运行任务、安装、模型或集群验证。

## 1. 阅读目标

**沿 _setup_agent → _run_agent 看选定 Agent 怎样使用环境，再追一条模型请求，对齐路由、尝试身份和响应。**

## 2. 指挥官、入口条件与边界

1. **主线入口**：接 Step 013 后的 [Trial._setup_agent:1880](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1880)，再回到 SingleStepTrial._run 的 [_run_agent:74](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L74)。已读安装关系只短回顾，不通读安装脚本。
2. **已有输入**：选定 Agent、可用环境、题目 instruction；只沿一个 Agent/协议、普通 run（非 resume/load、无 user-agent bridge）阅读。
3. **前置回查**：on_job_start 在 Job 运行前配置路由；START 在 _prepare 前登记尝试；AGENT_START 在 Agent.run 前打开本轮模型交互。各自按原时机回查，不把这些准备统一画成环境启动后的新调用。
4. **停止位置**：能指出 Agent 的实际执行入口、请求目的地、trial/session 对应和响应来源；返回 SingleStepTrial._run 的日志与产物阶段。商用 API 适配只在选用它且确有缺口时深入，不预设必须重建 Proxy。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

沿用 Step 010、011 的整体主线，各步保持相同图形结构。**本步从环境就绪后继续 Agent.setup，再进入 Agent.run；模型请求发生在等待 Agent 执行的期间。路由登记只作为必要前置回查。** 具体入口与返回位置见 3.2；图中回调和 HTTP 均标明交互方式，不当作同一同步调用栈。

图内标注直接对应本步：**[本步]** 是当前展开位置，**[交给 Step …]** 是停止与交接位置；其余节点保留作整体背景。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> _CREATE_JOB(job_config)          # 创建 Job 时组成各次尝试的配置。
            -> plugin.on_job_start(job)  # [本步前置回查] 路由配置/回调在运行前登记，不是到这里才执行。
            -> Harbor Job.run
                 -> _run_trials_with_queue -> TrialQueue -> Trial.run  # 队列交接后进入一次尝试。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup  # [本步] _setup_agent 调用已选 Agent.setup；安装入口仅短回顾。
                      -> _run
                           -> _run_agent  # [本步] _run_agent_phase 把 instruction/environment/context 交给 Agent.run。
                           -> _collect_artifacts  # [交给 Step 015] Agent 阶段结束后继续日志、产物和评测。
                           -> _run_verifier      # 使用题目的验证规则取得评分。
                      -> _finalize               # 清理环境并发出生命周期事件。
                           == END 事件 ==> plugin._on_end
                                            # 回调内部的轨迹处理留到实际接入时回查。
            <- JobResult
            -> plugin.on_job_end(...)           # 整份 Job 返回后的插件收尾。
            -> _bundle_samples                   # 训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务  # [本步] 等待 Agent 执行期间追一条请求与响应。
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

下面是普通单步任务的教学裁剪。按编号进入当前局部，弄清交接后回到真实调用方；前置回查、能力对照和验证不会冒写成一条连续执行栈。

```python
# 主线：环境已就绪，从 _prepare 继续。
[1] Trial._setup_agent(...)
  -> await agent.setup(environment=...)  # 已读：Claude/Codex 可按需安装。
  <- 返回 _prepare，再回到 Trial.run

Trial.run -> SingleStepTrial._run
  -> [2] _run_agent -> Trial._run_agent_phase(...)
       -> AGENT_START 回调               # 路由打开发生在实际 Agent 执行前。
       -> await agent.run(...)           # 当前选普通执行分支。
            # [3] 等待期间，Agent 发起模型请求，不是 run 返回后才调用模型。
            == HTTP ==> Gateway -> RolloutLLMProxy -> Dressage Proxy -> 模型后端
       -> AGENT_END 回调
  -> _upload_agent_logs                  # Agent 阶段返回，交给 Step 015。

# 仅为解释上面的地址和身份而回查；这些准备发生得更早：
plugin.on_job_start -> _inject_agent_routing(...)
Trial START ==> plugin._on_start -> GatewayLease.register -> GatewayRuntime._register
  -> GatewayRuntime._create_proxy(...)
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 环境就绪后准备 Agent | [_setup_agent:1880](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1880) · [已有准备卡](../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-mainline) | 确认 setup 用的是哪个环境、准备完成后返回哪里；安装细节只按具体问题回查。 |
| 2. 题目交给 Agent | [_run_agent:74](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L74) → [_run_agent_phase:700](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L700) | 追 instruction/environment/context 交给实际 run 的位置；在普通分支停住，不追所有 CLI 事件解析器。 |
| 3. 一条实际模型请求 | [_inject_agent_routing:1031](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1031) · [_on_start:639](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L639) | 回查已配置地址与 route/session 归属，再返回 Agent 请求；必要时进入 Gateway._create_proxy，不通读线程和容量管理。 |
| 4. 后端合同与一次响应 | [SGLangRouterClient.generate:176](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/sglang_client.py#L176) | 确认默认 token 接口与所选后端是否匹配，保留一次请求/响应及失败证据；只做 API 评测与训练数据分别验收。 |
| 5. 返回执行主线 | [_run_agent_phase 的结束位置:781](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L781) → [SingleStepTrial._run:41](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L41) | AGENT_END 后回到 _run_agent 的输出同步，再回 _run 的日志/产物阶段，接 Step 015。 |

**按需前置的停止位置**：只认清回调登记、触发与地址归属即可。完整 on_job_start、_safe、所有事件列表不重新变成必读；Step 011 的按需导航可以复用。

**实施前要核对，但不另开一轮通读**：Pod 是否能访问所配置地址；所选模型后端是否提供所需协议；Dressage 的版本门禁是否已适配。默认 SGLang token 接口不是普通商业 messages API；模型请求成功也不保证存在可训练轨迹。已有商业 API 工厂仅在确实选用时对照。

**本步局部验证**：一条真实请求和响应、对应的 trial/session、Agent 执行出口。会话 finalize/read 的完整控制交接在 Step 015 用同一次尝试继续，未取得的 token/logprob 如实留缺口。

**读后接续**：回到 SingleStepTrial._run 的日志、产物和 Verifier 调用，进入 [Step 015](../step-015-harbor-results-and-samples/01-scope.md)；不把模型请求画成 Agent 返回后的串行下一步。

<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0），本轮按本地 git show 定位相关符号；本地 main 与发布标签有差异，不混用。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](references/history/2026-11-12-before-call-order-scope.md)完整保留。本次只改 scope 与导航，不将未读函数提前建卡或标为掌握。

</details>
