# 2026-10-29 · 结合已有基础，确定剩余 Slime 阅读范围

[岗位与要求](../../../../slime_photo/code-reading/job-alignment.md#jd-required-depth-20261029) · [阅读计划](current-goal-slime-reading-order.md) · [唯一进度](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

**2026-11-01 当前 Slime 阅读取舍**：没有由这份 JD 直接推出的必需新增源码专题，当前可以停止扩展通读。保留“运行中结果与资源的一致性”和“评估与实验复现的交接”两个按具体问题触发的方向；不是新的必读目录，见[第 10 节](#slime-optional-directions-20261101)。生成接口已读的历史纠正继续有效。

**2026-11-01 最新历史核对**：生成接口与 plugin generate contract 已在 Step 015 讨论，后续已有理解反馈，并明确转入 Step 016、017。撤回把同一个契约测试排成默认下一步的建议；未执行该测试是运行证据状态，不能推出必须回退学习。完整证据与修正见[第 9 节](#contract-history-correction-20261101)。第 8 节保留同日稍早的建议，测试只作有实际需要时的可选入口。

**2026-10-31 最新复核建议**：当前正常训练闭环阅读可以停；不再把独立的中断源码章节作为固定下一项，优先复用已读接口做一个小接入验证，异常/中断行为融入该实例，必要时再回查实现。依据与边界见[第 7 节](#jd-recheck-20261031)。此前 A/B/C 安排保留为历史，不表示这些能力或验证已完成。

用户要求综合 Learn Claude Code、Python 异步与并发、Slime 阅读痕迹和已有强化学习理解，判断还缺什么，并确定剩余 Slime 范围。本次审查使用本地正文、明确学习反馈和已有验证记录；文章存在、本人已表达理解、实际系统运行分别判断。 Slime 源码核对固定在 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，其他专题保留各自版本；本轮未执行新测试、模型或训练。

## 1. 总判断

**不再增加一套 Agent、Asyncio 或强化学习基础课。Slime 剩余重点收为两段代码阅读，加一项已有接口的集成验证。** 当前主要补充“这些部件如何协同运行及如何证明行为正确”，而不是继续扩大算法或底层系统的清单。

这并不把现有全部章节标为已掌握。某个具体 API 或公式再次卡住当前任务时，回到既有教材局部复习；独立异步课程的既定范围不因本次审查被删改，也不作为继续 Slime 之前必须全部完成的前置。

## 2. 已有基础怎样计入

| 方向 | 本地证据与已覆盖的内容 | 对剩余范围的影响 |
| --- | --- | --- |
| Agent 框架理解 | [Learn Claude Code](../../../../content/projects/learn-claude-code/_index.md) 的 S01–S17 覆盖主循环、工具、权限/Hook、上下文、Memory、任务、后台任务、团队、MCP、Workflow 与 Goal；[S15 综合 Harness](../../../../content/projects/learn-claude-code/s15/_index.md#harness-understanding) 已明确模型、工具及结果回流的组合关系 | 不在 Slime 重讲整套 Agent Loop；只追框架接入合同和当前业务差异 |
| Python 异步与并发 | [异步课学习路线与记录](../../../../content/projects/python-async-concurrency/learning-route/index.md#reading-status) 与 98 项 API 的独立课程已有 Task、等待、取消、时间预算、队列、同步、ContextVar、线程/进程及回调材料；Slime 笔记也已有 semaphore、pacer、worker loop 和 callback | 不另开 Ray / Asyncio 底层课程；只在中断、回队、背压等业务行为上核对用法 |
| 强化学习原理 | [CS285 课程入口](../../../../content/courses/cs285/_index.md) 已有 BC/DAgger、策略梯度、Actor-Critic/GAE、PPO、TRPO 和奖励学习；[Lecture 14](../../../../content/courses/cs285/lecture-14/index.md#lecture-thread) 已接到 LLM 序列、组内优势、参考 KL 和策略更新 | 当前 JD 的一类训练基础已有内容支撑；不追加完整预训练/SFT 或再学一遍 PPO 数学，重点完成数据到训练的交接 |
| Slime 的真实组件 | 主题 01 的 Coding Agent 调用与评测、Step 010–013 的生成/评分/worker/收集，以及 [Step 015](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/README.md)、[Step 016](../topics/02-rollout-reward/steps/step-016-sample-to-train-data/README.md) 已建立场景记录 | 复用已有卡片，剩下按正常闭环和中断分支补缺，不重开整条调用链 |
| 部署基础 | [2026-10-25 的用户条件](../../../../slime_photo/code-reading/job-alignment.md#next-month-job-plan-20261025) 明确记录用户用过 kubectl、部署过简单服务 | 不按零基础部署安排；继续核实能否拿出完整的资源、网络或重启排查案例 |

**已有材料中的边界仍要保留。** [S15 综合 Harness](../../../../content/projects/learn-claude-code/s15/_index.md#harness-understanding) 明确 MCP 为 mock、部分 Skills / 隔离为教学实现；[S16 Workflow Runtime](../../../../content/projects/learn-claude-code/s16/_index.md#workflow-try) 的 demo 使用 MockAgentRunner。[Skills Lab 的验证边界](../../../../examples/s07-skills-lab/README.md) 的确定性脚本检查不等于真实模型的触发与行为评估。异步课明确记录 36.2 曾暂缓、ContextVar 与 RLock 没有全部标记掌握。这些信息用于避免夸大，不意味着要从头补读全部章节。

## 3. 当前最值得补的缺口

1. **生成与训练闭环**：目前 Step 017 刚建立，还要连上训练提交、等待、完成通知和生成侧权重更新。缺的是接口和运行顺序，不是新增训练理论。
2. **失败时业务语义是否正确**：已有取消、异常和队列知识；还要观察一次 Slime 中断后，哪些结果保留、哪些重新排队，完成结果是否错误地流进训练。
3. **真实接入与复跑的证据**：[Step 015](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/README.md) 明确记录尚未运行插件契约测试。已有讲解和模拟应复用，但仍要用一个小改动验证接口、评分/结果和失败行为，并保存可重复运行的输入、配置、版本与结果。
4. **部署排障案例待核实**：已有简单部署经验；未在本轮目录中找到完整故障诊断过程。如已有现成案例，整理它即可，无须重新学习基础或重复做项目。
5. **Trace 是应用验证缺口**：[Trace 主题](../topics/03-trace-diagnostics/README.md) 有工具用法、示例与部分真实函数运行输出。后续若恢复，目标是用现有 Trace 定位一次具体问题；仍遵守当前暂缓要求，不重新钻 trace_utils 全部内部。

阅读记录能够证明接触过什么、表达过什么理解；它不能单独证明线上经验或全部独立实施能力。上述缺口中，集成与排障项是目前未见足够证据，不断言用户在目录以外没有做过。

<a id="remaining-slime-scope"></a>

## 4. 2026-10-29 的 A/B/C 安排

| 单元 | 必须看的代码或已有记录 | 读到哪里就停 |
| --- | --- | --- |
| **A · 完成当前 Step 017：正常训练闭环** | [train.py:51–99](/home/hongshi/projects/slime/train.py:51)；[RayTrainGroup.async_train](/home/hongshi/projects/slime/slime/ray/actor_group.py:148) 与 [update_weights](/home/hongshi/projects/slime/slime/ray/actor_group.py:178) 的直接接口；[RolloutManager.training_completed](/home/hongshi/projects/slime/slime/ray/rollout.py:430) 及必要的一层委派 | 说清数据引用交给谁、何时等到训练完成、何时通知、权重怎样交回生成侧。默认 object-store 下只带过不适用的 batch 完成分支；不进入权重传输、模型 loss 或优化器实现 |
| **B · 复用已读 worker：中断结果与背压** | [AsyncRolloutWorker._make_done_cb](/home/hongshi/projects/slime/slime/rollout/fully_async_rollout.py:246) → [prepare_retry_group](/home/hongshi/projects/slime/slime/rollout/base_types.py:107)；回查 [_loop](/home/hongshi/projects/slime/slime/rollout/fully_async_rollout.py:178) 的接纳/报错条件及 [close](/home/hongshi/projects/slime/slime/rollout/fully_async_rollout.py:140) 的直接收尾 | 能对照完成组与 PENDING/ABORTED 组的去向；解释 flat partial 保留、分段失败回到原输入与已完成同伴保留；用一个中断用例验证，接清错误如何向外报告、停止时如何等待在途任务。背压只看已读条件，不再讲完整事件循环 |
| **C · 复用 Step 015 与评测链：做一个小接入验证** | 已读 generate_and_rm / 自定义 generate 或评分接口、[Step 015](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/README.md) 和 [插件契约测试入口](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:148)；已有 run_evaluation / filter 按改动回查 | 完成一个策略或评分规则的小改动，对固定样本跑正常与错误/中断情形，核对 Sample 状态、奖励和输出，保存复跑方法。CPU 替身、真实模型调用、GPU 训练分别标记；不新增整份测试框架课程 |

A、B 是剩余新增阅读的两个核心单元；C 主要补执行与验证，不是再读一遍所有已读函数。先完成 A，再进入 B；C 可利用已有接口准备，实际展开时仍确认具体改动与运行条件，不自动新建一串后续 Step。

B 的首选证据是 [test_unfinished_flat_group_is_requeued_without_discarding_partial_response](/home/hongshi/projects/slime/tests/test_fully_async_rollout.py:307)；需要比较分段任务时再用 [test_interrupted_segmented_group_retains_successful_siblings](/home/hongshi/projects/slime/tests/test_fully_async_rollout.py:264)。背压已有对应 [测试](/home/hongshi/projects/slime/tests/test_fully_async_rollout.py:317)，只在这一具体行为需要验证时使用。本次仅核对源码位置，没有运行这些测试。

## 5. 不再扩成必读的内容

完整 Megatron、更多训练算法推导、CUDA/NCCL、全部 DP/PP/CP/VPP 实现、Ray 调度器内部、straw/WAL/pack/GC 与完整容灾恢复不在当前必读范围。Dressage 等额外框架、所有 grader、所有高级 Agent 机制和三门跨语言课程也不追加。

Kubernetes 是 JD 的独立实践要求，不能用读 Slime 代替；这里利用已有部署基础补排障证据。Trace 恢复时使用已有工具与记录做诊断，不再默认建立内部实现专题。

本节及上节保存当时的安排；当前进一步复核建议以第 7 节为准。

本报告保存范围与停止标准，当前入口见[唯一路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。A 完成后按 B 的小范围确认下一步；本次审查不改写当前各函数的掌握状态，也不立即开启 B、C 或部署任务。

<a id="backend-depth-review-20261030"></a>

## 6. 2026-10-30 复核：Megatron 读多少，Slime 在哪里停止

用户已准备查看 worker 的 update_weights，但打开 backend 后感到内容过多，要求给出更好的读法，并重新按腾讯岗位判断必要性与整个 Slime 的停止位置。依据继续采用[用户确认的完整 JD](../../../../slime_photo/code-reading/job-evidence/2026-10-28-user-provided-jd.md)，不是当天招聘官网状态。本次是在原 A/B/C 范围内收紧粒度，没有增加课程。

### 6.1 岗位需要的是哪一层

| JD 原文依据 | 当前值得保留的能力 | 不由该条自动推出的必读内容 |
| --- | --- | --- |
| 职责 5：结合大模型训练视角，推进强化学习训练链路工程化落地；要求 4：了解训练流程和基本原理，至少一类 | 能接清 rollout 数据、奖励、训练调用和新权重回到生成侧的关系 | 通读 Megatron backend、全部 loss、优化器和并行算法 |
| 职责 2–3：统一组件，维护接入接口和验证机制 | 知道调用者、输入输出、可替换实现，以及怎样验证一次接入 | 每个第三方后端、每种权重传输器的内部实现 |
| 职责 4、要求 1/5：并发、资源、稳定性和行为一致性 | 能分清训练等待、同步等待、新任务接纳与在途任务；用一个失败场景核对结果去向 | 为理解正常流程就提前读完恢复、缓存、显存、通信和存储各分支 |

因此当前有必要的是权重更新的职责与交接，MegatronTrainRayActor.update_weights 的三处代码只是补充直接证据。它不是必须精读整文件的岗位要求。只有具体故障或改动碰到内部实现时，再增加该处阅读。

### 6.2 需要代码证据时才回查这个函数

用户再次询问这些行是否属于岗位必需后，撤回将其作为独立必读任务的建议。当前应回到 train.py 的暂停、同步与恢复，连接已经建立的职责模型。worker 的“取得生成引擎 → 需要时建立连接 → 委派已有 updater”保留为[裁剪后的证据](../topics/04-training-data-updates/steps/step-017-generation-training-loop/01-scope.md#worker-weight-sync-window)；只有解释仍缺依据或实际需求涉及这里时，再核对名称、返回项和分支条件。

这次选择直接同步的正常路径，已有引擎可用、无需故障恢复、offload_train=False。保留按需连接条件；健康恢复、日志、barrier、显存管理及具体传输器暂时折叠。全量磁盘的写入与组级 reload 已作对照，不能与本窗口的直接同步路径混为同一个执行过程。

**当前必要的停止点**：能沿 train.py 说明先等训练完成、再同步生成侧参数、随后按条件恢复新任务接纳，并定位周期评估。若按需进入 worker，取得对象、连接与委派这层关系已经足够；不要求写出连接与传输内部，也不以逐行读完该片段作为结束当前步骤的条件。

### 6.3 本轮 Slime 阅读的收尾标准

继续保留 A/B/C，不把当前 backend 扩展为第四个专题：

1. **A：结束当前正常闭环阅读。** 把任务/样本 → 训练字段与数据引用 → 训练并等待 → 完成通知 → 新权重交给生成侧 → 按条件继续生成连起来。用户已表达更新目标是生成侧；其余精确边界按真实反馈记录，不要求重读全部旧函数。
2. **B：再补一个中断场景。** 复用已读 worker，核对完成、未完成与部分结果的去向，观察错误如何报告、停止怎样收尾，并用已有小测试取得相应证据。只读与该场景直接有关的分支，不把它扩为全部容灾实现。
3. **C：完成一次小接入和可复跑验证。** 复用 Step 015 与既有评分/评测链，做一个有限的生成或评分改动，核对正常与错误/中断的输入输出。沿用真实运行条件，CPU 替身、真实服务和 GPU 训练的验证能力分别标记。

三项达到对应范围后，结束本轮按函数推进的 Slime 阅读；后续遇到具体改动或故障再回查。停止点是建立一条能说明、能改动、能验证的框架路径，不是读完目录或消除所有未知。

Kubernetes 部署/排障与用现有日志或 Trace 诊断真实问题仍属于岗位证据，不能用更多 Slime 阅读代替。用户已有简单部署基础，先复用已有案例；Trace 暂缓决定保持，不在本次复核中自动恢复。以上是停止新增源码范围的判断，不把阅读结束等同于所有岗位经验已经具备，也不提前开启 B/C 或标记完成。

<a id="jd-recheck-20261031"></a>

## 7. 2026-10-31 再对照原文：把能力要求与具体学习案例分开

用户在 Step 017 收束后，再次要求根据混元 Agent 强化学习框架岗位判断后续是否真的需要看。本次依据继续是[用户确认的完整岗位原文](../../../../slime_photo/code-reading/job-evidence/2026-10-28-user-provided-jd.md)，不作为当天官网招聘状态。

| 原文的直接要求 | 当前更合适的应对 | 不能直接推出的学习要求 |
| --- | --- | --- |
| 职责 3：支持 Agent 策略及评估接入，维护接口、组件和验证机制 | 复用已读接口完成或整理一个接入实例，说明输入输出并验证行为 | 必须用 Slime 再实现一套完整框架 |
| 职责 4：解决实际运行中的并发、资源、链路和行为一致性问题；要求 1/5：并发与工程验证 | 在同一实例中检查一个实际错误、取消或中断场景，能定位问题并解释处理结果 | 必须独立逐函数读完中断、重试、队列与恢复章节 |
| 职责 5 的训练链路工程化；要求 4 的至少一类训练或评估流程基础 | 利用已读 Agent、样本与 Step 017 主线说明生成、训练、同步、评估的配合 | 必须继续深入 Megatron、NCCL、优化器或所有权重更新后端 |

**调整后的建议**：Step 017 的正常主线阅读保持收束。原 C（小接入验证）更直接对应岗位核心，应作为后续优先实践；原 B（中断场景）不再固定为新增源码章节，而是作为该实践中的一种异常行为按需验证。若已有其他项目能够展示同等的接入、验证与排障经验，先整理已有证据，不为指定仓库重复做练习。

当前 Slime 记录里 Step 015 仍缺契约测试的运行证据，这说明现有阅读尚不能替代接入验证；但不据此断言用户在其他项目中没有相关经验。可从已有例子和可用环境完成接口级验证，验证边界按实际运行保留，不要求为此先具备完整 GPU 训练环境。

后续只有在这个小实例的接口、错误结果或资源行为确实需要解释时，才回查 `_make_done_cb`、`prepare_retry_group` 等最小实现；不先把它们列成新的必读目录。Kubernetes 部署/排障是原文明示的独立经验要求，仍需用实际案例支撑；Trace 的暂缓安排保持。

这是本轮复核后的建议与优先级调整，未启动新步骤、改写已读事实或标记任何未运行验证为完成。

<a id="next-priority-20261101"></a>

## 8. 2026-11-01：正常主线讲通之后，优先补哪项岗位证据

> 同日后续核对已修正本节的具体起点：不再默认回到 Step 015 的同一契约测试。岗位能力与实践证据仍需区分，但“测试未运行”不足以单独决定下一任务，见[第 9 节](#contract-history-correction-20261101)。

用户已连续复述 Step 017 从数据来路、训练、完成登记到权重交接和周期评估，随后要求再次对照混元岗位确定下一步。依据仍是[用户确认的完整 JD](../../../../slime_photo/code-reading/job-evidence/2026-10-28-user-provided-jd.md)，本次未将它冒称为当天官网状态。

本轮沿用第 7 节的方向，不重新增加必读源码章节。岗位的主轴是 Research Agent 框架的研发、接入、验证与实际运行问题处理；要求 4 为至少一类训练或自动化评估流程基础，不要求读完全部训练后端。

### 8.1 优先级与对应依据

| 顺序 | 岗位原文 | 当前已经有的基础 | 接下来需要形成的证据 |
| --- | --- | --- | --- |
| 先做一个接入案例 | 职责 2、3：组件封装、策略与评估接入、验证机制；要求 5、6：工程能力与持续迭代 | Coding Agent 主链、生成调用与返回合同、样本处理、Step 017 整轮职责已有阅读及用户表述 | 能接入或修改一个生成/评分实现，说明输入输出，固定输入下验证结果并保留复跑步骤 |
| 在同一案例里验证一种相关失败行为 | 职责 4：实际并发、资源与行为一致性问题；要求 1、5 | 已有原生异步知识、worker 正常调度、结果交付与等待模型 | 对生成或评分失败等实际相关情况观察错误传播、结果处理和必要资源释放，保留修正依据；不预先通读所有中断实现 |
| 随后核实容器与 Kubernetes 案例 | 要求 3：集群开发、部署、排障或性能优化经验 | 用户已报告 kubectl 与简单服务部署经验 | 优先整理已有集群案例的部署方式、问题、诊断依据与结果；若证据不足，再用已有小服务补一次相关实践 |

这些是能力和证据的优先级，不是必须另建三个项目。现成项目能够支持同样的说明时优先复用；本目录尚未找到充分证据不等于用户在其他地方没有相关经验。

### 8.2 建议首先处理的具体问题

**如果换成自己的生成或评分实现，怎样让它接入框架，并验证输出与失败行为？**

复用 [Step 015](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/README.md) 的已有合同，不重读全部生成链。该步已经读过最小 custom_generate 和单个测试，但记录明确没有运行契约测试、真实插件或训练。没有新写的独立插件或实验脚本。

可用的起步检查是本地源码 `tests/plugin_contracts/test_plugin_generate_contracts.py::test_custom_generate_function_path_supports_user_override`。以下仅为候选命令，本次未执行：

```bash
# 工作目录：/home/fredkeira/projects/slime
python3 -m pytest tests/plugin_contracts/test_plugin_generate_contracts.py::test_custom_generate_function_path_supports_user_override -q
```

采用测试默认的固定生成器、未设置自定义覆盖环境变量时，该用例从 Sample、配置和采样参数出发，经真实 generate_and_rm 调用固定生成器，检查返回值；NUM_GPUS=0，使用 FakeGenerateState，不启动真实模型或 Ray 集群。它仍需要导入依赖。10 月 28 日曾发现缺少 torch/numpy/ray 等；若实际开展，应重新检查当时环境，不能拿旧探测判断当前状态。

**跑通现有用例只是起步。** 本项结束时应有一个本人能说明的接入或小改动，以及固定输入、预期输出、实际结果、一种相关失败行为和复跑命令。CPU 替身检查、真实 API 调用与真实 GPU 训练的证明范围分别记录。现有测试的名称与单个 Sample 断言比真实 Coding Agent 的部分接口形式更窄，不把一条测试当成完整运行合同。

此前用户已明确取消 async def 改成普通 def 的 await 反例；本轮不恢复这个演示，也不将它作为接入验证的前置。

### 8.3 本轮继续保留的边界

- Step 017 的训练交接源码阅读按已确认深度收束；Megatron、NCCL、Ray 调度器、全部并行或存储恢复实现不增加为下一必读。
- 并发、资源和异常问题随上述具体案例补证据；不把所有恢复函数重新列成课程。
- Trace 仍是 JD 的相关能力，但沿用用户当前暂缓决定；恢复时围绕具体诊断问题使用已有工具。
- Kubernetes 是独立的岗位经验要求，不能用 Slime/Ray 阅读替代；已有简单部署经验不清零。
- 本轮只完成岗位对照与候选任务具体化，没有创建 Step 018、安装依赖、运行测试或部署。实际范围与当前状态由[唯一路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)维护。

<a id="contract-history-correction-20261101"></a>

## 9. 2026-11-01：生成接口已读，不能以测试未运行作为回退理由

用户指出生成接口与 plugin generate contract 应该已经在某一步处理，并要求查看后续讨论。此次直接回查实际原话、测试卡和 Step 016 的进入记录，确认用户记忆有依据。

| 先后 | 已有记录 | 能确认什么 |
| --- | --- | --- |
| Step 015 前段 | [路径加载和位置参数](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/04-flow.md#signature-is-not-the-whole-contract) | 用户已表述前三个参数按位置对应，讨论也已区分签名与完整调用约定 |
| Step 015 第三步 | [明确进入 plugin generate contract](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/04-flow.md#plugin-contract-test-entry) | 实际读过最小生成器、框架调用、签名与结果断言，不是只准备了候选材料 |
| 同步后的理解 | [用户区分两类检查](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/04-flow.md#contract-check-boundary) | 已区分生成函数的参数检查与 Sample/tokens/response/response_length 等结果检查；助手补过 reward 非空及测试覆盖边界 |
| 更后面的讨论 | [计数与潜在服务端中止](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/04-flow.md#possible-server-abort-branch) | 用户表达大致理解包装器计数与后续可能中止的联系，不能把这段历史遗漏 |
| 阅读转向 | [明确跳过 await 反例](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/04-flow.md#skip-await-demo-next-data-handoff)、[确认进入 Step 016](../topics/02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#step016-start) | 用户接受可等待要求，不继续该演示，随后已转向 Sample 到训练数据；当前又已走到 Step 017 的整轮主线 |

应当分别保存三个事实：

1. **接口学习已有内容和明确反馈。** 不能把“生成接口需要满足什么”重新列为尚未开始的学习任务；各项精确边界仍按对应卡片记录，不把整体已读扩展成全部掌握。
2. **这条 pytest 用例没有运行记录。** 这只说明缺少该次运行证据，不推翻已有理解，不表示用户拒绝所有实践，也不等于该测试现在必须执行。
3. **此前推荐的回退不充分。** 上一轮虽然写了“已读”，却直接把同一测试排为下一起点，没有充分尊重后续理解和已确认的推进。现撤回这一默认安排；测试保留为真实接入问题需要时可复用的工具。

后续选题应继续从尚未核实的实际项目经验和 JD 能力出发，包括已有接入/验证成果与容器、Kubernetes 经历，而不是再讲一遍生成接口。本次只纠正历史与推荐依据，不借此另开新章节、恢复已取消演示或启动实践。Trace 暂缓与 Step 017 主线收束保持。

<a id="slime-optional-directions-20261101"></a>

## 10. 2026-11-01：Slime 是否还有值得单独学习的方向

用户进一步限定问题为：针对腾讯岗位，Slime 内部还有什么需要单独学习。此次按实际步骤记录核对，未把 COVERAGE 中的“计划深度”当作学习状态，也未因文件未读完就增加必读项。

**结论：目前没有必须继续新增的 Slime 源码专题。** 生成接口及契约已在 Step 015 讨论，样本到训练数据在 Step 016 展开，Step 017 已有整轮职责复述；此前 Coding Agent、组级生成、持续调度和正常结果交付也计入已有基础。当前可以结束本轮通读；未执行的测试和未核实的工程经历单独处理，不能反推必须重读。

如果后续出现具体问题，只优先保留两类回查方向：

| 可选方向 | 与 JD 的直接关系 | 目前已读与尚未串通的部分 | 何时值得进入、读到哪里停止 |
| --- | --- | --- | --- |
| 运行中的结果与资源一致性 | 职责 4；要求 1、5：并发、资源、稳定性和行为一致性 | 已有 worker 正常调度、完成回调、队列交付、局部计数与 finally；[Step 013](../topics/02-rollout-reward/steps/step-013-completed-group-handoff/05-task-flow.md#scope-closure)仍把异常、取消、未完成组和重试列为按需边界 | 有具体取消、失败、重跑或积压问题时，选一条路径追清哪些结果保留、哪些重试、错误交给谁、哪些占用何时释放；不展开整套容灾或资源调度 |
| 评估与实验复现的实际交接 | 职责 1、3；要求 2、5：自动评估、实验复现、验证与结果分析 | 已读独立评分、生成结果字段及 RolloutManager.eval 的职责；这些不自动等于实际复跑经验 | 需要比较或复跑一次评估却不能解释配置与结果关系时，核对数据、代码/模型版本、采样与评分配置、结果保存；接清一次可复跑评估即可，不遍历所有评测器 |

第一项若被实际问题触发，比继续学习更多正常路径或训练后端更贴近当前剩余的源码边界；但不恢复“必须先读独立中断章节”的旧安排。已有沙箱收尾和计数理解也不因这项候选被清零。

一个足够小的可选场景是：Task 已返回，但平铺结果里仍有 ABORTED/PENDING 样本，这组怎样保留已有生成内容并退回输入侧，而不进入完成队列。只定位 [已读回调的未完成组分支](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L267-L273)，必要时看 [prepare_retry_group](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/base_types.py#L107-L121)，回到 add_samples 与 return 就停止；不把整个回调当成未读，也不继续下钻持久化或分布式恢复。此例仅供以后选择，当前未展开。

Trace 属于运行诊断的工具，仍沿用用户明确的暂缓决定；只有以后明确恢复时才接回，不能借第二项自动重新开启 Trace。评估复现也不等同于训练结果逐位一致或完整 checkpoint 恢复。

当前不单独排入下一必读的内容：完整 Megatron/loss/优化器、CUDA/NCCL 与并行细节、Ray 调度器、straw/存储恢复、更多 Agent 示例或另一套 RL 框架。相关实现可以在实际改动或故障中定点回查。

容器与 Kubernetes 仍是 JD 明示的外部经验要求，继续复用并核实用户已有部署经历；读取 Slime 的 Ray 服务代码不能替代这项经验。本次不以它为理由扩展 Slime 服务层通读。

本轮只形成停止位置与可选方向判断，没有创建下一 Step、选择并展开新的失败场景、运行测试或恢复 Trace。
