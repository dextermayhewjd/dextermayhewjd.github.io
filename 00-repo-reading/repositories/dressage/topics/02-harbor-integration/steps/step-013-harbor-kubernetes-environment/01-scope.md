# 01 · Dressage Step 013：创建并启动 Environment，对齐 Agent Sandbox 能力

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一步总结](../step-012-task-agent-verifier/05-task-flow.md) · [下一范围](../step-014-model-routing-and-api-contract/01-scope.md)

> 状态：2026-11-13，按用户明确的范围先读环境接口，不进入具体后端。对象创建、启动包装与 BaseEnvironment.start 已讨论；exec、文件传输、stop 的六张方法卡已按用户要求建立，尚待逐项讨论。Agent Sandbox 实现与运行验证保留为待办，本步尚未完成。

> **2026-11-17 回访**：Step 016 的清理主线之后，用户要求先核对环境接口及现成接入例子。见[沙箱接口对照与阅读入口](../../../../references/harbor-sandbox-interface-map.md)。下方旧导航保留当时阅读位置；本轮不将旧卡片状态升级为已掌握，也未开始接入实验。

> **同日补充目标**：用户进一步要求理解 DSec 所代表的系统问题，以及题目环境怎样经预热池、Claim 和 Kubernetes 交给 `Environment.start()`。本轮系统图见[沙箱供给与预热](../../../../references/sandbox-supply-prewarm-and-kubernetes.md)；先建立这一交接模型，具体函数入口为后续建议。

> **2026-11-17 运行前提与组合判断**：用户要求从 Slime 出发，在无本地 GPU 的条件下调用国内厂商 LLM API，先完成任务执行与评测。独立记录见[Slime 起点的 API 评测方案](../../../../references/slime-api-evaluation-integration.md)。下方历史骨架保留原调用语境；新的无 GPU 入口与 API 适配尚待核对，不能将原训练路径视为已支持该方案。

## 1. 阅读目标

**先看清 Harbor 如何取得和启动环境对象，再认清执行命令、文件传输与停止的接口要求；用这些合同继续理解 Agent 执行主线。**

目标仍是接入 Agent Sandbox。本轮只确定调用方需要环境提供什么能力，具体适配与性能机制留到实施时核对。

## 2. 指挥官、入口条件与边界

1. **入口**：接 Step 012 的 [Trial._init_agent_environment:1453](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1453)。这里创建本地 Environment 对象；实际启动在 Trial.run 的 _prepare 内，二者分开阅读。
2. **已有输入**：接住 Step 012 的运行配置、Task 与 Agent 对象；此前 hello-world / Docker 仅用于解释共同参数。后续实现阅读以 K8s / kubernetes-sigs/agent-sandbox 为目标，先看 BaseEnvironment 合同，再核对现有 UpstreamK8sSandbox 与 Harbor 的适配接缝；DockerEnvironment.start 不列为必读，不预设现有 K8s 类已直接接入 Harbor。
3. **首轮阅读停止位置**：能说明对象创建与实际启动的区别，认清 start/exec/upload/download/stop 的参数、方向和返回；沿 _prepare 的健康检查接清 exec 的调用，skills 上传和默认用户先认用途，再进入 Step 014 的 Agent.setup。未读完这些接口前，不把首轮标为结束。
4. **实施待办**：具体 Agent Sandbox Environment、接口映射、冷创建/文件/命令/回收验证尚未完成。后续接入时回访；WarmPool/Claim、ACK/GKE 设计和性能优化不作为本轮接口阅读前置。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

沿用 Step 010、011 的整体主线，各步保持相同图形结构。**本步当前只读环境对象创建、启动调用与运行接口合同；具体 Agent Sandbox 操作未实现，后续阅读显式假设接口满足要求。** 具体入口与返回位置见 3.2；图中回调和 HTTP 均标明交互方式，不当作同一同步调用栈。

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
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # [本步先认合同] 具体适配与冷创建验证待实施。
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

**当前范围：只看调用合同，暂缓具体后端。** start 接口已读，剩余六个运行方法已按确认范围建卡，仍待逐项接清。下面只链接本地函数卡，卡片建立不代表阅读完成。

**阅读导航随实际问题更新。** 图中保留真实调用关系；表中的编号用于定位阅读入口。逐段带读时更新当前函数、停留位置、回查入口和返回位置，不按卡片清单一次读完。已讨论内容与待读内容分别标明。

<a id="current-reading"></a>

> **当前函数：[Trial._prepare](02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-agent-call)**，停在技能上传返回后的第 649 行。
>
> **已接清什么**：健康检查的用途、把本地技能目录放入环境；具体传输后端与其余接口仍有待回查。
>
> **下一处建议**：先认清 `with_default_user(...)` 临时设置默认用户，再沿当前 user_agent=None 分支进入 `Trial._setup_agent:1880`。该函数属于 Step 014，尚未开始该步。
>
> **本步边界**：未逐项阅读的运行接口和实际适配验证仍保留，推荐下一入口不等于 Step 013 全部完成。其余接口可否在后续真实消费位置回查，作为后续安排建议。

```python
# 已读：对象在 Trial 初始化时创建。
[1] Trial._init_agent_environment -> self.agent_environment

# 已读：运行到 _prepare 后才真正调用启动。
Trial._prepare
  -> [2] _setup_agent_environment -> [2.1] _start_agent_environment
       -> [3] await self.agent_environment.start(...)
  -> [3A.0] run_healthcheck(...)         # 用途已讨论；细节按需回查。
       -> [3A] self.exec(...) -> ExecResult  # 读到 1592 行时再进接口卡。
       # exec 返回后，接回 1594 行的 result.return_code 判断。
  -> [3B.0] _upload_injected_skills(...)  # 用途已讨论：准备目标目录并上传技能。
       -> [3B] upload_dir(...)          # 上传本地 source 到环境内 target_dir。
  -> with_default_user(...)              # 当前返回处：临时设置默认用户。
       -> _setup_agent(...)              # Agent 准备交给 Step 014。

# 其余接口地图：按需要回查，不是 _prepare 下面连续执行一遍。
[3B] upload_file / upload_dir             # 本地文件/目录进入环境。
     download_file / download_dir        # 环境中的文件/目录回到本地。
[3C] stop(delete=...)                     # 停止与删除要求；调用发生在后续收尾阶段。

# [4] 具体 Agent Sandbox 实现、冷创建与回收验证：后续实施，不在本轮下钻。
```

<a id="reading-sequence"></a>

| 阅读位置 | 本地函数卡或待建入口 | 本轮看清什么、返回哪里 |
| --- | --- | --- |
| 1. 环境对象创建 · 已讨论 | [Trial._init_agent_environment](02-short-term-memory/functions/harbor/trial/trial.py/Trial._init_agent_environment.md) · [调用方 Trial.__init__](02-short-term-memory/functions/harbor/trial/trial.py/Trial.__init__.md) | 已知配置与题目要求怎样交给工厂，保存到 self.agent_environment；对象存在不等于环境已经启动。 |
| 2. 启动包装 · 已讨论 | [Trial._setup_agent_environment](02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent_environment.md) · [调用方 _prepare](02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md) | 启动事件、计时与委派；后续 _prepare 的健康检查、skills、默认用户只认用途。 |
| 2.1. 启动调用与超时 · 已讨论 | [Trial._start_agent_environment](02-short-term-memory/functions/harbor/trial/trial.py/Trial._start_agent_environment.md) | 已知 force_build 怎样传给具体对象、wait_for 等待和超时转换；不下钻后端启动。 |
| 3. 启动接口 · 已讨论 | [BaseEnvironment.start](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.start.md) | start 定义已认清；返回启动包装，再回到 _prepare，继续健康检查。 |
| 3A.0. 健康检查 · 用途已讨论 | 从 [Trial._prepare 的调用入口](02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-healthcheck-call) 进入 [BaseEnvironment.run_healthcheck](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.run_healthcheck.md#healthcheck-loop) | HTTP 示例的就绪检查用途已讨论；循环与 exec 细节按需回查，正常返回 _prepare 后继续 3B.0。 |
| 3A. 命令执行 · 按需回查 | [BaseEnvironment.exec（含 ExecResult）](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.exec.md)；卡已建，待讨论 | 看 command/cwd/env/timeout_sec/user，输出 return_code/stdout/stderr；从 _prepare 的健康检查调用回查，读完返回该调用方，后端实现暂缓。 |
| 3B.0. 技能上传 · 用途已讨论 | [Trial._upload_injected_skills](02-short-term-memory/functions/harbor/trial/trial.py/Trial._upload_injected_skills.md#upload-skills-mainline) | 先看 source 与目标目录的对应，再按需进入 upload_dir；返回 _prepare 后继续默认用户与 Agent 准备 |
| 3B. 文件与目录传输 · 待讨论 | [upload_file](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.upload_file.md) · [upload_dir](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.upload_dir.md) · [download_file](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.download_file.md) · [download_dir](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.download_dir.md)；四卡已建，按一组方向合同阅读 | 区分本地路径与环境路径，明确上传/下载方向；每卡保留真实消费场景，不把四个方法当作 _prepare 中连续执行的步骤。 |
| 3C. 停止与删除 · 待讨论 | [BaseEnvironment.stop](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.stop.md)；卡已建；[已读 Trial 收尾位置](../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._finalize.md) | 看 delete 的含义与谁在何时调用 stop，读完返回 _stop_agent_environment 和 _finalize；资源是否释放留给实测，不是在 _prepare 中停止环境。 |
| 4. 实现与验证 · 实施待办 | 尚未进入具体 Agent Sandbox Environment；不预建实现卡 | 适配类缺口、冷创建、文件/命令/回收验证继续保留。可以待后续正常主线读清后回访，不能据接口阅读声称已接入。 |

**本轮按当前调用逐段展开。** run_healthcheck 的用途已讨论，重试细节按需回查。技能上传用途已讨论，当前回到 with_default_user，先认其临时设置默认用户的用途；_setup_agent 是 Step 014 的入口；本例 user_agent=None，相关 user-agent/bridge 分支暂略。_write_stream_handle 只认辅助记录，不另开机制专题。

**其他声明先知用途**：type、_validate_definition 和 capabilities/resource_capabilities 在实际适配时再核对具体要求，不把基类全部工具方法都加入本轮必读。

**首轮停止标准**：上述七个运行操作（start、exec、四个文件方法、stop）的输入输出和调用位置已能解释，再带着“环境满足这些接口”的阅读假设进入 Step 014。当前已从 3B.0 返回 _prepare，运行接口卡片虽已建立，尚未逐项完成阅读；实现和运行验证也未完成。

**读后接续**：回到 _prepare 的 _setup_agent，随后看 Step 014 的 Agent.setup/run。具体后端、预热与性能比较在实际接入或故障需要时回查。

<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0）。2026-11-13 本轮已再次核对本地 /home/fredkeira/projects/harbor，使用 git show v0.25.0 读取固定源码；main 领先发布标签 123 个提交，不混用。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](references/history/2026-11-12-before-call-order-scope.md)完整保留。11-13 仅为实际进入的环境创建函数建卡，并调取调用方；其余未读函数仍只定位。

</details>
