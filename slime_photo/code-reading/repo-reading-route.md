# Slime 源码阅读路线：Research Agent 框架工程

本路线把模型调用、工具执行、任务与上下文、Trace、结果评测、并发恢复、集群资源和训练交接组织成连续的源码阅读单元。第一遍能说明每个部分具体做什么、需求应接在哪里；第二遍能追踪关键数据、失败分支和验证方法。

<a id="当前优先沿-generate-读完-41"></a>

## 当前接续

2026-10-25 当前：用户已确认将包含共享 state 与执行控制的结构采用到 [Step 010 正式核心骨架](../../00-repo-reading/repositories/slime/topics/02-rollout-reward/steps/step-010-generate-and-rm/01-scope.md#execution-skeleton)。正文与导航统一为“共享状态 → 受控生成 → 结果处理 → 评分交付”，保留 semaphore 获取/释放、pacer 分批启动、中止检查、DP 计数上下文和关键结果交接；旧 scope 已归档。用户随后提出先看清 state 与 sample；已补入[两个对象的最小定位](chapters/03-strategy-evaluation/walkthrough.md#sample-and-state)，建议先短回顾 Sample 的任务数据角色，再看 GenerateState 在此处使用的控制成员，随后返回 acquire/try/finally。按用户要求，现已在 Step 010 的短期记忆建立 [Sample 类卡](../../00-repo-reading/repositories/slime/topics/02-rollout-reward/steps/step-010-generate-and-rm/02-short-term-memory/classes/slime/utils/types.py/Sample.md)与 [GenerateState 类卡](../../00-repo-reading/repositories/slime/topics/02-rollout-reward/steps/step-010-generate-and-rm/02-short-term-memory/classes/slime/rollout/sglang_rollout.py/GenerateState.md)，先保存对象职责、当前字段与使用位置。用户随后初步概括为“sample 是单个样本的状态，generate state 是群体的状态”；已保存原话，并校准 Sample 还包含数据、GenerateState 是进程内多份任务共享而非某一个 group 的状态，具体校准尚待反馈。当前已进入生成前控制段：用户询问 acquire、pacer、aborted 和 DP 上下文。已校准 acquire 为当前任务取得名额、aborted 为布尔值，补充分批启动说明及 dp_rank_context 的计数卡片；用户随后比较 dp_rank_context 与 HarnessContext，并询问记录切分；已补清方法产生上下文管理器与数据类保存运行参数的区别，调入旧 HarnessContext 类卡作对照，父函数保留四处控制语句的顺序。补充说明尚待反馈，读完回到 `338` 行的生成函数选择。未新增生成、并发或训练运行。[本轮采用记录](../../00-repo-reading/repositories/slime/topics/02-rollout-reward/steps/step-010-generate-and-rm/04-flow.md#execution-skeleton-adopted)。

2026-10-25 此前：用户要求开始第二主题，已建立 [Topic 02 · Rollout 接入与奖励](../../00-repo-reading/repositories/slime/topics/02-rollout-reward/README.md)与 [Step 010 · generate_and_rm](../../00-repo-reading/repositories/slime/topics/02-rollout-reward/steps/step-010-generate-and-rm/README.md)。首轮从 `sglang_rollout.py:338–344` 的生成函数选择开始，接回已读的 Coding Agent；本步 scope 围绕“选择实现 → 等待结果 → 判断是否补奖励”，先看新任务、非组评分的正常训练路径。已建初始函数卡、跨主题继承 Step 009 的 `03 + 02` 为 46 份记录，并保存[网页讲解正文](chapters/03-strategy-evaluation/walkthrough.md)；个人机制表述尚待反馈，没有将建卡记为掌握。用户随后反馈 scope 看不清骨架；已按既有 skill 固定 Coding Agent 的正常列表返回路径，先呈现“选实现 → 等生成 → 后处理 → 补奖励 → 返回”，其他分支折叠，旧稿保留。[本轮格式审阅](../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#step010-core-skeleton-review)。用户继续反馈精简后仍差一层，现已回查原有剪枝方法并另存[按业务结果分块、保留关键实参的对照方案](../../00-repo-reading/repositories/slime/topics/02-rollout-reward/steps/step-010-generate-and-rm/references/scope-by-data-handoffs-proposal.md)。用户本轮明确追问 state，要求直接依据源码判断完整骨架。已核对共享 GenerateState、准入、分批启动、中止与 finally 释放，并补入[连贯正文](chapters/03-strategy-evaluation/walkthrough.md#state-and-execution-skeleton)及本步函数卡；纠正 pacer 为分批唤醒而非手动暂停，标明名额在 hook 与 RM 前释放。当前先看清运行控制与数据处理两部分，尚无个人机制复述；`rm_hub` 内部、组调度、Coding Agent 失败与最终清理继续留待相应问题。源码本地 HEAD 与本轮只读查询的官方 main 均为 `18868a79`，无真实生成、沙箱或训练运行。岗位目标与投入条件沿用[既定安排](job-alignment.md#next-month-job-plan-20261025)。[本轮过程](../../00-repo-reading/repositories/slime/topics/02-rollout-reward/steps/step-010-generate-and-rm/04-flow.md#topic-two-start)。

2026-10-25 此前：用户确认按主题组织 Slime 阅读记录。现有 Step 000–009 已整体迁入 [Coding Agent RL 主题](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/README.md)，内容、编号、原话、未知与记忆继承关系保留；源码仍以各卡记录的版本为准。当时下一步继续全局编号 Step 010，后续主题实际展开时再创建，尚未开始新主题阅读。此前单题正常主线的收束与外层失败/最终清理等边界不因迁移改变；一个月投递目标和 Kubernetes 基础继续沿用。后续入口参考[当前目标推进的 Slime 阅读顺序](../../00-repo-reading/repositories/slime/slime后续阅读顺序/current-goal-slime-reading-order.md)，优先讨论 generate_and_rm 的接入契约。[本次迁移记录](../../00-repo-reading/repositories/slime/version-reviews/2026-10-25-topic-migration.md)。

2026-10-25 此前：用户指定进入 Step 009，重点询问沙箱执行时怎样把模型请求送到 SGLang。[本步 scope](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/01-scope.md)已从 2f231865 校准到 18868a79，围绕 CLI → HTTP → Adapter → HTTP → SGLang 与回复整理导航；`sb` 启动接口、CLI 请求地址和 Adapter 的模型服务地址已由助手静态核对。首个观察点是路由登记，再接 `_run_turn:394`、`423` 与 `call_sglang_generate:610`；服务准备、启动和模型处理按需复用前序现行记录。本轮未新增函数卡、刷新长期继承或运行真实服务，也未将用户当前疑问记为已理解。Step 008 保持既定深度的收束，Step 007、006 范围不变。[本轮问题与依据](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/04-flow.md#request-scope-18868a79)。

2026-10-25 此前：用户对 Step 008 的 launcher、脱机启动与防重、完成文件轮询反馈大致理解；已补准主机仍持续等待、超时不保证进程停止的边界。按当前 scope 收束启动与结果回传主线，task flow 对齐 18868a79，旧总结完整保留。具体 Shell、SDK 与清理机制继续留作未知，没有新增真实运行或刷新长期继承。下一候选是 Step 009 的 HTTP 接收入口，尚未开始该步新版校准；Step 007、006 保持原收束范围。[本轮反馈与收束](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#harness-execution-closure-20261025)。

2026-10-24 此前：用户在 Step 004 主线回顾后，明确希望继续理解 `get_trajectory`，正在讨论是否先补 TrajectoryManager 与 MessageNode 的对象模型。已按 `18868a79` 定位 manager 的三个字段、节点结构和 `leaves/path_from_root`；推荐只补这些必要前置，再回到路径导出、赋奖励与移除记录的主线，尚未建立新的类卡或确认更深算法范围。此前跨循环细节继续留待后续；已有主线总结不等于本轮对象模型已理解。[本次前置范围讨论](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/04-flow.md#trajectory-manager-prerequisites)。

2026-10-24 此前：用户明确将 `tasks[0]`、跨循环提交与等待等细节留待后续，要求先走完 Step 004。本轮已沿 `finish_session` 接清取配置、委托 `get_trajectory` 导出与赋奖励、补响应文本并返回 `Sample` 列表的正常主线；两张外层卡片与 task flow 已对齐 `18868a79`，旧稿及数值例子的历史来源保留。本步在列表交回 `_generate` 处收束，跨循环、拼接、分段和 mask 等问题继续保留，未新增个人掌握结论或真实运行证据。Step 003 已有收束状态保持，下一步具体范围尚未指定。[本轮主线与取舍](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/04-flow.md#step-four-mainline-closure)。

2026-10-24 此前：用户反馈 Step 004 的跨循环卡片更清楚，并复述了 `wait → 取消 pending → 收尾` 的顺序；完整原话已写入 [shutdown_session 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md#shutdown-user-restatement-2026-10-24)。当前需厘清 sid 与 Task 的对象层级、为什么用 `tasks[0]` 取得共同的 loop，以及 `run_coroutine_threadsafe` 的提交与等待关系。按用户确认，[BaseAdapter 类卡](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/02-short-term-memory/classes/slime/agent/adapters/common.py/BaseAdapter.md)已扩展为 13 个实例字段、4 个类级配置的浅层总览；使用关系先保留已讨论的 `closed`、`inflight`，具体操作仍在方法卡。函数本体与关闭登记规则已按 `18868a79` 核对，未认定跨循环机制已掌握。当前继续这一问题，读清后回到 `finish_session:331`；父函数及 `get_trajectory` 卡片、task flow 仍待校准，Step 003 主线维持收束。[本轮接续](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/04-flow.md#adapter-state-card-and-user-restatement)。

2026-10-24 此前：按用户确认，Step 004 的 scope 已按 `18868a79` 校准整体骨架、三项输入与局部导航，旧版全文归档。当前仍从 `generate.py:326` 进入 `BaseAdapter.finish_session`，先看清已有轨迹、基础字段、奖励和附加信息的交接，再沿收尾、取配置、导出与补文本继续。函数卡片与 task flow 尚待逐项校准，本轮未新增函数阅读或掌握结论；Step 003 主线维持收束，Step 002 与 Step 1 索引待办状态不变。本机可用源码位于 `/home/fredkeira/projects/slime`，HEAD 与既定版本一致。[本轮核对](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/04-flow.md#scope-core-refresh-18868a79)。

2026-10-23 此前：用户指定回到 Step 004，询问本步需要看什么。本轮先核对既有范围与新版入口：推荐从 `generate.py:326` 的调用进入 `BaseAdapter.finish_session:314–345`，先接清 `sid`、已有轨迹、`base_sample` 和 Step 003 的 `reward`，再依次回顾收尾、取配置、委托导出与补文本。`finish_session`、`shutdown_session`、`get_trajectory` 的函数体与旧版一致；内层 `_SampleBuilder.to_sample` 存在字段变化，不能据此认定输出完全不变。既有整体理解与未读边界保留；本轮未逐段校准函数卡片、scope 或 task flow，首个函数的具体展开待接续。Step 003 主线维持收束，Step 002 与 Step 1 索引待办状态不变。[本轮入口核对](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/04-flow.md#step-four-reentry-18868a79)。

2026-10-23 此前：Step 003 的 `scaleswe → eval_cmd` 主线按既定 scope 收束。用户已概括 `EvalResult` 含 `reward` 与 `applied_cleanly`，助手校准了 `_run_eval_cmd` 返回分数、`_grade_scaleswe` 组装结果、`run_evaluation` 交回外层的函数层级。新版 [task flow](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/05-task-flow.md)保留调用图、结果与边界，旧版完整归档；函数原话、scope 与索引已同步，`03` 快照保留。内部细节与真实验证未记为掌握或完成；沿用已有六种路径的替身验证，本轮未新增沙箱或测试运行。下一处候选是接回已有 Step 004 的轨迹与奖励导出样本，具体新版校准待用户确认；Step 002 维持原收束状态，Step 1 索引整理仍单独待处理。[本轮收束记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#evaluation-flow-closure-18868a79)。

2026-10-23 此前：用户已概括 `_run_eval_cmd` 的二值评分，助手补充命令来自配置、实际按退出码映射，原话已保存。按“继续”返回 [_grade_scaleswe 的结果段](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md#scoring-result)，接清 `r → EvalResult(r, True) → 环境退出 → run_evaluation → _generate`；父函数与分派入口已按 `18868a79` 校准，旧卡完整归档。六种结果或异常路径通过原函数配合替身验证，未运行真实环境或测试。两项返回字段及完整交接尚待用户反馈，长命令细节未声明掌握；本轮未改 `03` 和旧 task flow，Step 003 尚未收束。下一处先确认本步结果交接，再考虑更新本步总结；Step 002 维持原收束状态，Step 1 索引整理仍单独待处理。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#grade-result-return-refresh)。

2026-10-23 此前：用户明确进入 [_run_eval_cmd](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md)，已按 `18868a79` 校准现有卡片并完整归档旧版。先以短命令建立“执行 → 退出码 → 分数”的主线，再用分支图及折叠说明补齐超过 64 KiB 时写脚本、处理受支持 shell 包装的路径，以及 `eval_user` 的传递。已用替身核对输出和关键边界，未运行真实 shell、测试或远端环境；个人理解尚待反馈。读完返回 `_grade_scaleswe:340`，后续看 `EvalResult` 组装与环境退出；父函数旧卡、长期快照和旧 task flow 尚未随本轮改写，整步未收束。Step 002 维持原收束状态，Step 1 索引整理仍单独待处理。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#run-eval-cmd-refresh)。

2026-10-23 此前：用户已复述 [_apply_diff](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md) 的“保存补丁文件 → 应用修改 → 判断是否应用成功”主线，原话、最近认识时间与索引已更新。此处成功指补丁应用，测试评分仍在后续；工具冲突处理、通用方法边界和真实运行未新增确认。下一处候选仍是 `_grade_scaleswe:337` 的 `_run_eval_cmd`，本轮未展开其新版内容。长期快照、旧 task flow 与 skill 保留；Step 002 维持原收束状态，Step 1 索引整理仍单独待处理。[本轮反馈](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#apply-diff-user-model)。

2026-10-23 此前：用户要求进入上一轮指明的下一函数，已回到 `_grade_scaleswe:329` 的 [_apply_diff](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md)。当前卡片按 `18868a79` 校准 `/tmp` 补丁路径、普通 `git apply` 优先的命令顺序、工作目录引用及后端清理边界，旧卡完整归档；保留原有“保存补丁说明，再应用修改”的理解和认识时间。替身已验证调用与布尔返回，未执行真实补丁工具或远端任务，本轮变化尚待理解反馈。读完成功返回分支后，本例下一处是 `swe.py:337` 的 `_run_eval_cmd`，尚未展开其新版校准。长期快照、旧 task flow 和 skill 保留，Step 002 维持原收束状态，Step 1 索引整理仍单独待处理。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#apply-diff-refresh)。

2026-10-23 此前：用户已概括 `_evaluation_sandbox` 通过 `trace_span` 记录进入和退出，原话已入卡，完整环境交付职责仍按源码模型保留。现返回 `_grade_scaleswe:322`，复习并校准 [ensure_agent_user](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)：使用已有 `ev` 准备用户、按后端标记调整目录归属并配置 Git；已同步 `18868a79` 的条件、路径引用和 600 秒命令预算，旧卡完整归档。真／假／缺失标记的命令组成已用替身验证，没有执行真实 shell 或创建沙箱；新版分支的个人理解尚待反馈。读完在本例返回 `swe.py:329` 的 `_apply_diff`，尚未开始其新版校准。长期快照、旧 task flow 和 skill 保留；Step 002 维持原收束状态，Step 1 索引整理仍单独待处理。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#ensure-agent-user-refresh)。

2026-10-23 此前：用户已初步概括 `_metadata_scaleswe` 从原始样本取得所需任务资料，原话已补入卡片；未逐项确认字段回退。随后回到 `run_evaluation → _grade_scaleswe`，当前从 `swe.py:308–320` 的取值与环境调用进入新版 [_evaluation_sandbox 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_evaluation_sandbox.md)，集中看选择后端、进入、交付 `ev` 和退出；后端内部暂不展开。正常／异常交接已做替身验证，未进行真实沙箱运行，新函数理解尚待反馈。读完返回 `_grade_scaleswe:322`，再使用 `ev` 准备用户；父函数旧卡尚未完整校准。scope 与索引已接入新卡，长期快照、旧 task flow 和 skill 保留。Step 002 维持原收束状态，Step 1 索引整理仍单独待处理。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#evaluation-environment-entry)。

2026-10-23 此前：用户确认先看元数据字典并独立建立函数卡片。Step 003 已新增 [_metadata_scaleswe](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_metadata_scaleswe.md)，按 `18868a79` 对照原始 `Sample` 属性与完整 `md`，保留 `grading` 字段及默认值；已用原始函数与输入属性替身做局部输出核对。当前先阅读该卡，理解反馈尚未取得，之后回到 `run_evaluation` 的新版校准。scope、步骤入口和索引已接入新卡；原有七张函数卡、长期快照、task flow 与 skill 保留，未新增远端运行。Step 002 维持原收束状态，Step 1 索引整理仍单独待处理。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#metadata-scaleswe-card)。

2026-10-23 此前：按用户要求完成 Step 003 的[逐函数版本核对](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/references/scope-version-review-2026-10-23.md#3-源码变化与应更新的位置)：现有 7 张卡对应 5 个函数变化、2 个 E2B 方法原文不变；新增环境包装与工厂、返回类型及必要的元数据入口也已静态比较。针对用户指出的输入缺口，推荐先从 `get_metadata` 进入 `_metadata_scaleswe` 的返回字典，只补清 `md / grading` 的字段与来源，然后回到 `run_evaluation → _grade_scaleswe`；该前置阅读建议尚未展开或确认理解。现有 scope、函数卡片、长期快照、task flow 与 skill 保留，未新增远端验证；Step 002 保持原收束状态，Step 1 索引整理仍单独待处理。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#function-version-audit-and-entry)。

2026-10-23 此前：用户指出 Step 003 scope 的 3.2 包含尚未从 Step 001、002 获得的信息。已修正[输入衔接](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/01-scope.md#input-bridge)：接住已讨论的 diff_text 和目录含义，用最小 md 字典补本题评分信息；trace 先唤起已有用途，CONFIG、base_sample 与元数据构造保持未展开，后端选择留到环境观察点。当前先看该输入例子，再进入 run_evaluation 的新版校准；解释效果尚待反馈，未新增已掌握结论。函数卡片、长期快照、task flow 和 skill 未改，Step 002 保持原收束状态，Step 1 索引整理仍单独待处理。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#input-prerequisite-gap)。

2026-10-23 此前：用户确认按建议逐步推进，已先将 Step 003 的 [scope](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/01-scope.md#reading-path)按 `18868a79` 更新为整体定位、输入来路、局部执行骨架与七个阅读观察点；[旧版 scope](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/references/scope-at-2f231865.md)完整保留。仍沿 `scaleswe → eval_cmd` 读评测；环境先读 `_evaluation_sandbox → create_sandbox` 的共同调用边界，默认 Sunabako 的内部实现暂不展开，E2B 旧卡只作显式分支回查。下一处从图①的 `run_evaluation` 校准输入、分派、trace 传递与返回合同，再进入编排函数。函数卡片、长期快照、task flow 与 skill 本轮未改，没有新增掌握或运行结论。Step 002 保持按范围收束，Step 1 索引分工整理仍单独待处理。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#scope-current-18868a79)。

2026-10-23 此前：用户要求检查 Step 003 是否需要修改。已完成[scope 与版本审查](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/references/scope-version-review-2026-10-23.md)：评测主线和返回合同可保留，需补阅读图、更新整体入口及环境工厂关系，并校准有变化的函数卡片。新版默认经工厂选择 Sunabako，旧 E2B 卡片只对应显式选择的分支；尚未展开新后端内部。当前仅保存审查结论，Step 003 的 scope、卡片、长期记忆与 task flow 正文未改，未新增掌握或运行结论。下一项是依据该审查确定新版 scope 的阅读导航与后端边界；Step 002 保持已按范围收束，Step 1 的索引分工整理仍单独待处理。[本轮问题与结论](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#scope-version-review)。

2026-10-23 此前：按用户确认，已给 Step 001 的 [scope 3.4](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md#reading-path)补充阅读路径图，并将 [task flow](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/05-task-flow.md)按 `18868a79` 的执行与数据交接校准；旧版全文独立保留，函数卡片、长期记忆及 skill 未改。此次为已读步骤的文档整理，不新增掌握结论；Step 1 的索引分工整理仍单独待处理。主线仍在 Step 002 按“运行统计与补丁提取”范围收束之后，下一处为既有 Step 003 的独立评测，尚未开始其新版校准，入口与深度待接续确认。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#scope-map-and-task-flow-refresh)。

2026-10-23 此前：用户表示 Step 002 的内容已差不多并询问能否结束；对照 scope，已按“运行统计与补丁提取”范围收束，保存 [task flow](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/05-task-flow.md)及[收束记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#agent-results-closure)。统计的产生、读取转换、工作区快照到补丁、两份结果的下游用途均已有说明；具体理解仍以各卡片原话为准，Git 内部、hook 完整停止处理和真实远端验证继续留白。本轮没有新增运行或修改长期记忆。下一处主线是既有 Step 003 的独立评测，尚未开始该步的新版校准，具体入口与深度待接续确认。Step 1 的 task flow 与索引分工整理仍待继续。

2026-10-23 此前：用户已复述 `swe.git_diff` 比较工作区内容变化，并将 `_repository_tree` 与 Git 联系起来。本轮澄清 `baseline/current` 是前后两份文件状态快照，改动不必先提交；比较的是最终内容，不是中间提交历史。原话和澄清已保存到 [git_diff 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/git_diff.md)与[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#git-diff-snapshots-not-commits)，新增区别尚待反馈。`_repository_tree` 仍按接口理解，本轮没有新增运行或提前生成 task flow。Step 1 的 task flow 与索引分工整理仍待继续。

2026-10-23 此前：用户确认阅读 `swe.git_diff`。已在 Step 002 建立[函数卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/git_diff.md)，接清运行前 `baseline`、结束时 `current` 与返回补丁 `diff_text`；快照辅助函数暂按接口理解。原函数在本地临时 Git 仓库的无差异、源码修改、排除项及暂存/提交场景中已验证，未运行真实 Agent 或远端评测。尚无个人复述，按后续疑问决定是否展开 `_repository_tree`；本步 task flow 未提前生成。[本轮阅读记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#git-diff-first-read)。Step 1 的 task flow 与索引分工整理仍待继续。

2026-10-23 此前：用户询问统计收集部分是否已结束。按当前阅读目标，`collect_metrics` 的输入产生、读取转换与结果用途已可连贯说明，助手判断这一支线可以收束；个人理解与未展开细节不升级为完全掌握。下一项建议留在 Step 002，回到 `generate.py:298` 阅读 `swe.git_diff`，弄清 `sb、workdir、baseline → diff_text`；尚未展开或建卡，整个 Step 002 的 task flow 也未提前生成。见[收束判断与后续入口](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#collect-metrics-reading-checkpoint)。Step 1 的 task flow 与索引分工整理仍待继续。

2026-10-23 此前：用户已复述 `write_config` 同时保存原有确认配置与 PreCompact/PostCompact，两个事件指向提前放好的同一脚本。已保存原话，并补清配置位于安装后、本次 CLI 启动前，以及同一脚本接收不同事件名；这些澄清尚待反馈。详见 [write_config 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md)与[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#write-config-shared-script)。`launch_and_wait` 的初始化细节尚待反馈，进程管理与 `git_diff` 未展开；本轮没有追加运行。Step 1 的 task flow 与索引分工整理仍待继续。

2026-10-23 此前：用户确认继续看第 1、2 步，并要求 `run_hook` 只保留自身职责。本轮调取既有 `write_config`、`launch_and_wait` 卡片到 Step 002 的 `02`，按 `18868a79` 展开脚本复制与事件注册、统计清零与启动次序；完整旧版记录折叠保留。两步以同一工作目录连接，详见[机制参考](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/references/compaction-metrics-lifecycle.md#function-coverage)。原方法的配置和交接参数已用记录器验证，未执行 shell 或远端 CLI；新增细节尚待用户反馈，进程管理和 `git_diff` 未展开。[本轮阅读记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#hook-upstream-preparation)。Step 1 的 task flow 与索引分工整理仍待继续。

2026-10-23 此前：用户追问 `run_hook` 的心智模型是否覆盖前述三步，以及是否需要看其他函数。已在模型中补上游前提，在[机制参考](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/references/compaction-metrics-lifecycle.md#function-coverage)区分脚本文件、事件处理函数与统计文件。当前建议局部回看 `write_config:62–79` 的复制与注册，再看 `launch_and_wait:103–109` 的清零命令，然后返回 `run_hook`；未展开整个上游函数或建立新步骤。[本轮边界澄清](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#hook-function-coverage)。用户已有的初步理解保留，具体边界尚待反馈；`git_diff` 未展开。Step 1 的 task flow 与索引分工整理仍待继续。

2026-10-23 此前：用户已初步串起“预先准备 → 事件触发 hook → 写入 JSON”。本轮补清预先复制脚本并注册 hook、启动时初始化统计文件、事件发生后读改写累计状态是不同动作；这些细分关系尚待进一步反馈。原话已补入 [run_hook 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/compaction.py/run_hook.md)，跨函数顺序仍由机制参考连接。此前普通事件的文件变化与返回值已在本地验证，本轮未追加运行；文件锁与触限停止尚未深入，`git_diff` 未展开。读完回到 `collect_metrics` 的输入。[本轮复述与澄清](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#hook-setup-and-state-understanding)。Step 1 的 task flow 与索引分工整理仍待继续。

2026-10-23 此前：用户指出完整统计产生过程应归于机制说明，函数卡只保留链接，并说明已知 hook。已将上轮新增段落移到[压缩统计的产生与收集机制](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/references/compaction-metrics-lifecycle.md)，`collect_metrics` 卡片恢复为本次调用的模型、输入输出及机制入口。当前讨论的是记录职责和下一项 `swe.git_diff` 的阅读组织，未实际展开该函数或新增机制类 memory；具体机制的理解状态不因移文改变。[本轮纠正](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#function-mechanism-boundary)。Step 1 的 task flow 与索引分工整理仍待继续。

2026-10-23 此前：用户提出 `collect_metrics` 读取已有统计的理解，并追问这些统计何时、由谁写入。上轮在函数输入部分补充初始化、事件更新与读取的解释；后续按用户反馈移至独立机制参考。原 hook 的本地文件更新已验证，未运行真实 CLI 或远端沙箱；初始化与运行中更新的区分尚待用户反馈。[原始追问](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#compaction-file-origin)。

2026-10-23 此前：用户确认先看 `harness.collect_metrics`。已在新 Step 002 建立 [ClaudeCodeHarness.collect_metrics 函数卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.collect_metrics.md)，对齐 `18868a79` 的具体实现、统计文件与三个返回字段；正常、空白、空 JSON、错误 JSON 四种局部转换已验证。[初次阅读记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#collect-metrics-first-read)。

2026-10-23 此前：用户明确要求将运行统计与补丁提取独立为新的 Step 2，先看清每一步发生什么，再进入评测。已建立 [Step 002 的 scope](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/01-scope.md)，按 `ClaudeCodeHarness.collect_metrics → swe.git_diff` 阅读；完整继承 Step 1 的 20 份记录到 `03`。原 Step 002–008 顺延为 Step 003–009，路径和当前导航同步，历史编号、版本和旧快照保留，见[编号对照](../../00-repo-reading/repositories/slime/step-numbering-2026-10-23.md)。[范围确认](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#scope-confirmation)。

2026-10-23 此前：用户表示目前已清楚，询问下一步应看运行指标、补丁提取还是评测。已按 `18868a79` 核对职责与交接；建议沿用已有 Step 002 做新版校准，先补 `swe.git_diff` 的 `baseline → diff_text` 输入关系，再进入 `swe.run_evaluation`。`collect_metrics` 先在骨架上说明压缩统计与样本截断标记用途。此为当时推荐，用户随后明确将结果收集独立成步；Step 1 的 task flow 与索引分工整理仍待继续。[候选比较与建议](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#next-step-metrics-patch-evaluation)。

2026-10-23 此前：用户要求检查 `_run_turn` 卡片的内部顺序。已整卡同步 `18868a79`，保留三段格式，按源码实际执行组织输入与生成、解析与响应准备、响应与记录及收尾；补齐追踪嵌套、`_session_prompt_ids` 与前缀候选。旧稿独立留存，个人原话、认识时间和旧锚点保留，其他函数卡片及 task flow 未改。scope 3.4 继续表达观察顺序；task flow 与索引分工的整理仍待继续。[当前函数卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) · [本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#run-turn-execution-order-sync)。

2026-10-23 此前：用户要求 scope 的 3.4 按这一轮观察顺序展开。已将最初四项补成从 `_translate` 到返回清理的 12 个观察点，区分追踪的回看顺序与真实执行嵌套；每项链接卡片、源码位置与下一交接，四个辅助函数放在折叠的回查表中。3.1–3.3 骨架及函数、类卡片保留，`_run_turn` 整卡、task flow 与索引分工的整理仍待继续。[完整观察导航](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md#confirmed-reading-order) · [本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#complete-observation-order)。

2026-10-23 此前：用户要求先核对四个辅助函数，有变化才修改。已完成 `apply_chat_template`、`_render_response`、`json_response`、`_render_stream` 的固定版本与本地实现比较；四个函数均未发现实现变化，四张卡片逐字保留。Transformers 参考版 4.57.1 与本地 4.57.6 的函数、选模板方法及模板工具文件也相同；本轮为静态核对，没有扩大阅读范围。[核对记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/references/auxiliary-functions-version-check-2026-10-23.md)。`_run_turn` 整卡、task flow 与索引分工的整理仍待继续。

2026-10-23 此前：用户要求审视 Step 1 的短期记忆，询问为何还有本轮未直接讨论的函数。已逐项清点：20 个文件包含主线及直接使用的 12 项、已有辅助函数 4 项、Anthropic 实现引用 3 项和早期上游背景 BaseHarness.run 1 项；实际为 16 张函数记录、1 张类卡和 3 个引用入口。建议先明确索引用途与版本状态；本轮未移动或删除卡片，`_run_turn` 整卡与 task flow 的新版整理仍待继续。[完整清单](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/references/short-term-memory-audit-2026-10-23.md) · [讨论记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#short-term-memory-inventory)。

2026-10-23 此前：用户已初步概括 PromptPrefix 保存本轮信息，并要求继续。类卡已保存原话，助手补充消息、工具定义复制而 turn 保留引用的区别。按 scope，追加后只剩 `return response` 与 inflight 清理；静态核对末尾清理与旧版相同，正常路径先移除本请求的登记再返回。建议下一项先统一 `_run_turn` 新版锚点卡与 task flow，再接 Step 2 的 `swe.run_evaluation` 校准；这些后续工作尚未启动。[复述与末尾接续](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#prompt-prefix-understanding-and-tail)。

2026-10-23 此前：用户确认单独保存，并澄清源码是类时应使用 class 类型的记录。已在 Step 1 的 `02/classes/` 建立 [PromptPrefix 类卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/classes/slime/agent/adapters/common.py/PromptPrefix.md)，沿用 Session 的栏目，记录三个字段、构造例子、追加结果与后续取用。索引、调用方及读取方已接入导航；`_run_turn` 主体仍保留旧版，仅增加明确标为新版的保存入口。该轮尚无字段职责的个人复述，卡片详略待反馈。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#prompt-prefix-class-card)。

2026-10-23 此前：用户询问 `prompt_prefixes.append` 应生成怎样的短期记忆。助手建议沿用 Session 的类卡形式，独立记录 `PromptPrefix` 的三个字段、构造结果与候选用途；追加动作留在 `_run_turn` 内部阶段，检查与拼接留在 `_session_prompt_ids`。该轮只保存方案，类卡尚未创建，用户尚未确认成稿；落实时还需明确 `_run_turn` 旧卡与新版源码的版本边界。[分工建议](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#prompt-prefix-memory-shape)。

2026-10-23 此前：用户指定回看 `prompt_prefixes.append`，询问旧版是否没有。已核对 `2f231865 → 18868a79`，`PromptPrefix`、`Session.prompt_prefixes` 与 `_run_turn:470–472` 的保存语句均为新增。已在 [_session_prompt_ids 的输入来源](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/_session_prompt_ids.md#prompt-prefix-save)补齐三个保存字段及后续取用：消息与工具定义复制，turn 保留引用，追加的候选仍需后续检查才能复用。该语句属于 `_run_turn` 的局部保存阶段，未另建 append 函数卡片，未修改已认可的完整前缀检查解释；理解状态待用户反馈。[本次记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#prompt-prefix-save)。

2026-10-23 此前：用户明确继续核对 Anthropic `_respond` 与 `manager.record_turn`。两处入口及直接处理逻辑未变；已校准本步响应卡、两个渲染子卡、引用入口和轨迹记录卡。响应侧保留普通分支返回未发送对象、流式分支已写事件的区别；记录侧补齐新版 `TurnRecord` 附加字段，以及 Coding Agent 默认阈值 0 会关闭特殊历史改写合并。17 项相关测试与当前主例验证通过，无真实模型、CLI 或训练运行。当前仍在这两处的职责与场景差异，待用户反馈；没有把入口不变视为全部机制已掌握。[本轮记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#respond-record-version-calibration)。

2026-10-23 此前：用户再次用“按当前协议整理回复”概括 `_build_reply` 并要求继续。已澄清两份材料的去向：`wire → _respond → CLI`，`manager_message → manager 记录`，记录用的正是后者。当前回到 `common.py:433–436`，衔接格式标记回填、token 数量统计与流式判断；三句与旧版相同，属于 `_run_turn` 的连续准备阶段。下一处推荐为 `:442` 调用的 `_respond`，本场景实际实现位于 `anthropic.py:71–75`，其新版卡片仍待展开；不因“下一步”推定全部内部机制已掌握。[本轮复述与交接](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#reply-to-respond-preparation)。

2026-10-23 此前：用户确认继续看 `_build_reply`，询问是否已有记录、是否需要修改。已复用并校准 [共同函数卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md)及 Anthropic 引用入口：共同接口、具体实现、`Reply` 与辅助函数均未改变，原五种局部场景结果一致，仅随机工具 ID 不同。主体心智模型和示例保留；更新定位，并补充调用方将内部消息复制进 `prompt_prefixes` 的新用途。没有运行 HTTP 或模型，也未新增个人掌握结论。读完拟回到 `common.py:433–436` 的标记回填、token 计数和模式判断，再接 `_respond`；尚未展开该段新版校准。[本轮讨论](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#build-reply-version-calibration)。

2026-10-23 此前：用户已再次表述 `parse_model_output` 将原始内容拆成思考文本、正文与工具调用描述，并确认这一职责未变，随后询问下一处入口。按 [Step 1 scope](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md#run-turn-normal-path)，建议接 `common.py:432` 的 `self._build_reply`；Anthropic 场景实际实现位于 `anthropic.py:63–69`，先看清 `parsed → Reply`，再回到 `433–436` 的响应前准备。当前只推荐下一处，尚未开始 `_build_reply` 的新版校准；解析分支的既有未知保留。[本次复述与导航](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#parsed-to-reply-reading)。

2026-10-23 此前：用户明确转读 `parse_model_output` 并询问是否与旧版相同。已校准 [本步解析卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)：Slime 解析模块与调用实参完全相同；Docker 所列 SGLang 已升级，其 Qwen 内部有扩展，原卡四组局部输入输出仍一致。现有解析测试 3 项通过、1 项因完整 SGLang 缺失而跳过，另行运行 Qwen 原方法体的局部对照。当前停在解析职责与版本校准，个人原话和未知保留；未展开 `_build_reply` 的新版校准。[本次讨论与证据](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#parse-model-output-version-calibration)。

2026-10-23 此前：用户在用 logger 类比概括追踪职责后，要求按当前 scope 继续，询问下一处函数。依照 [scope 的已确认顺序](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md#confirmed-reading-order)，建议回到 `common.py:425` 的 `tok.decode`，短回顾 `turn.output_ids → raw_output` 及保留特殊标记，再接 `426–431` 的 `parse_model_output`。已静态核对该解码调用与旧版 `common.py:346` 相同；本轮只推荐入口，尚未展开新函数或迁移旧卡，不将“继续”视为掌握追踪内部机制。[本次导航记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#trace-to-decode-navigation)。

2026-10-23 此前：用户明确暂放 `call_sglang_generate` 内部细节，按既定顺序转读 [trace_span](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md)。本轮仍在 Step 1，回看 `common.py:412–423` 的包围关系及 `trace_utils.py:345–425` 的局部职责：向共享事件列表记录开始/结束、关联父子阶段，区分于保存生成数据的 `TurnRecord`。已建卡片，现有 Trace 测试 3 项及局部嵌套/异常实验通过；没有运行完整追踪链路。用户此前明确表示不理解数据结构与实际行为；补充 `s.trace → carrier → events → 单条事件` 后，最新尝试用“通过 TraceHandle 向列表写事件，类似 logger”概括职责。已认可该类比，并补清当前使用已有 handle、trace_id 用于归属而非查找写入位置、span_id 用于起止配对；这些细化尚待反馈。[本次复述](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#trace-logger-understanding)。原嵌套细节收进折叠区，不将先前材料或测试通过视为已理解。ContextVar 栈、跨边界传播、导出及下一函数继续暂放。[本轮澄清](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#trace-data-structure-depth)。[本轮讨论](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#trace-span-local-reading)。

2026-10-23 此前：用户确认接续 [call_sglang_generate](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/call_sglang_generate.md)，询问新版变化。已对照 `2f231865 → 18868a79`，更新本步卡片并保存旧稿：一轮可经多次 POST，`captured` 累计输出，仅在 `abort + partial_rollout + 剩余额度` 条件下续生成；同时补齐预算、响应校验和返回附加字段。14 项已有 token/预算测试及五个局部 HTTP 场景通过；重放套件缺少 `wandb` 未运行，无真实模型运行。用户随后尝试以“按 SGLang 格式处理输入、输出和对应概率”概括职责，并询问是否可暂放细节；当前停在请求生成、接收结果、形成本地 `TurnRecord` 的职责模型，已澄清原输入来自调用者、logprob 对应生成 token。具体机制仍未确认理解，不自动下钻；需要继续时再从 `common.py:574–588` 进入，`trace_span` 仍放在业务之后。[本轮职责澄清](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#call-sglang-responsibility-model)。[讨论与证据](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#call-sglang-version-calibration)。

2026-10-23 此前：按已确认顺序进入 [_session_prompt_ids](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/_session_prompt_ids.md)。核对它是 `18868a79` 新增的会话输入准备层：先普通模板编码，再在历史与边界可确认时接回原始 token；否则使用普通编码结果。已新建本步卡片，并校准 `_render_token_ids` 的调用者与模板参数；旧卡归档，后续步骤累计快照保留。现有非 HTTP 测试 9 项通过，并用已下载 Qwen tokenizer 验证“读取 README”场景；旧输出为教学构造，未运行真实模型或 CLI。用户随后明确反馈分支及各分支行为仍不清楚，要求用图说明；已补候选检查循环、`continue` 与最终返回的区别，以及两处模板编码用途，详见[分支澄清](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#session-prompt-branches)。用户随后尝试用“历史消息重叠后再加上去”理解，并明确仍不清楚意义及不匹配时的行为；已补[比较对象与回退例子](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#session-history-purpose)，说明比较当前请求的历史、选择旧 token 的复用方式，无合格匹配时仍编码当前完整消息。用户最新提出检查 prefixes 后决定能否拼接的初步框架，但把 anchor 视为失败后的另一策略，并对摘要与工具结果是否构成固定回退结果有疑问；已补[连续检查与回退内容澄清](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#anchor-is-a-sequential-check)。用户随后明确反馈这两项解释比较清楚，并选用完整文字和两张图作为详细理解；[当前卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/_session_prompt_ids.md)现由详细说明提炼简短心智模型，并提供展开链接。具体条件尚未逐项确认。当前仍在输入接续；下一项仍为 `call_sglang_generate`，尚未展开。[本轮讨论与证据](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#session-prompt-ids)。

2026-10-23 同日此前：按用户确认的 `_translate → _session_prompt_ids → call_sglang_generate → trace_span` 顺序，已校准 Step 1 的 [_translate 共同记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md)与 Anthropic 引用入口到 `18868a79`。两路输出、原单工具样例和工具 schema 转换不变，补充可匹配 ID 的多工具结果排序。新旧局部纯函数执行验证通过，未运行真实模型或工具；用户随后准确复述了按调用顺序整理工具结果，已登记这项局部理解；已有原话和其他未知保留。整理发生在已有请求数据中，异常 ID 分支为助手补充，未计为用户独立掌握。旧版卡片、其余函数及后续累计快照保留。下一项按已确认顺序为 `_session_prompt_ids`，尚未展开。[本次依据](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#translate-version-calibration)。[后续复述](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#translate-order-understanding)。

2026-10-23 同日此前：Step 1 新版校准中，用户明确本轮按 **`_translate → _session_prompt_ids → call_sglang_generate → trace_span`** 阅读，先理解业务输入输出，再解释追踪包装。已更新 [scope 阅读导航](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md#confirmed-reading-order)，真实源码嵌套继续保留。当前首个入口是 `_run_turn:415` 调用的 `_translate`，沿 Anthropic 场景核对消息与工具定义；追踪的完整传播、导出仍留作后续专题。本轮是顺序确认，未新增函数掌握或运行结论。[原话与调整](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#business-before-trace-reading-order)。

2026-10-23 同日此前：用户明确从 Step 0 进入 [Step 1 新版校准](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md)，要求先看哪些实现发生变化。已核对 `2f231865 → 18868a79`：请求主线保留，新增历史原始 token 接续、部分生成续接、扩展记录与工具结果排序。scope 已更新，旧 scope 归档；旧函数卡片、task flow 与后续累计快照仍保留原版本。建议先观察 `_run_turn:416–421、470–472` 的前缀取用与保存，再读 `_session_prompt_ids:93–136`；新增机制尚未逐个带读或确认理解。[本次原话与边界](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#recalibrate-step-one)。 用户随后提出 `trace_span` 日后单独阅读，已登记为[执行追踪专题候选](chapters/04-trace-validation/README.md#coding-agent-trace-candidate)；当前仍在 Step 1，不提前开启该专题。用户进一步追问骨架是否应先解释追踪；已在 [Step 1 局部骨架](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md)显示两层包装并说明职责与范围，内部机制保留给专题，呈现效果尚待反馈。

2026-10-23 同日此前：用户明确要求 Step 0–8 全部按新版重新校准，不能仅按需修订少数旧卡。已完成 [49 份短期卡片的本体与依赖差异盘点](../../00-repo-reading/repositories/slime/version-reviews/2026-10-23-step-card-audit.md)，用户已选择“先更新 Step 0，确认理解后逐步往下”，已整理 [Step 0 新版 scope](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-000-coding-agent/01-scope.md)：定位 `generate → _generate`，补清按样本选择对象、`baseline → git_diff` 与运行统计。旧 scope 完整归档；Step 1–8 尚未逐卡迁移，原认识与未知保留。用户继续追问新增 `trace_span` 是否应进入核心骨架；已在 [Step 0](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-000-coding-agent/01-scope.md#trace-span-boundary) 补充执行追踪的职责与折叠对照，并区分会影响样本状态的 `collect_metrics`。静态校准不记为掌握。全体步骤的校准范围与逐步共同校准的节奏均已确认，当前仍停在 Step 0，等待对上述关系的理解反馈。[本次原话与边界](../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#slime-all-steps-recalibration)。

2026-10-23 同日此前：用户询问 Slime 更新后是否需要从 Step 0 重建每一步的理解。本地 checkout 与实时查询的官方 main 已同为 `18868a79`，旧 Step 0–8 仍绑定 `2f231865`。[版本影响评估](../../00-repo-reading/repositories/slime/version-reviews/2026-10-23-2f231865-to-18868a79.md)确认七个业务环节仍在，入口、沙箱选择、工作区基线、单轮生成与样本附带信息等需要校准。建议先对照新版 Step 0 骨架，再接准 Step 7/8 当前入口；不清零已读事实，不批量覆盖旧卡。后续采用新版继续还是先读完旧版，尚未替用户确认；本次只有静态评估，没有新增函数掌握或运行记录。[原话与建议](../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#slime-version-update-impact)。

2026-10-23 同日此前：用户指出 Step 008 的 scope 看不到 Step 1。已补回其在 `HARNESS_CLS().run(...)` 等待期间的位置：CLI 经 HTTP 请求进入 Step 8 接收与路由，再接回 Step 1 已读的 `_run_turn` 模型处理与回复；补上原范围与本步旧卡入口。[定位修正记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/04-flow.md#restore-step-one-in-scope)。本次仅修复导航遗漏，Step 8 的接收链仍为已确认的接续范围，没有新增函数阅读或掌握结论。

2026-10-23 同日此前：用户表示大致理解当前 Harness 通信部分，并比较“继续 Step 008”与“先用新 skill 重写旧流程”。助手建议优先接续已确认的 [Step 008 HTTP 接收范围](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/01-scope.md)，旧 task flow 在实际回顾受阻时按需修订。首个观察点仍是 `AnthropicAdapter._register_routes:48–50`，接清路径与处理器后，再回查监听并返回 `_run_turn` 的 `request → body`。[原话与建议](../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#continue-step-eight-before-bulk-flow-rewrite)已保存；本次没有新增接收机制的函数阅读、掌握结论或运行证据，也未执行批量重构。

2026-10-23 同日此前：用户明确 Step 7 的图应以 `BaseHarness.run` 的四个直接部分为主层，各函数继续展开自己的子调用。已将 [task flow 第 2 节](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/05-task-flow.md#launch-flow-diagram)改为层级树，把 `run_agent → exec_and_wait → _await_done_marker` 放入第四分支；返回、源码与卡片导航保留。[本次反馈与修订](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#task-flow-call-hierarchy)。阅读范围不变，Step 8 继续承接 CLI 运行期间的 HTTP 接收；本次未新增函数阅读或机制掌握状态。

2026-10-23 同日此前：用户反馈 Step 7 的 task flow 缺少图，逐行阅读仍难以建立关系。已在 [第 2 节](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/05-task-flow.md#launch-flow-diagram)补上准备、嵌套调用、远端运行与本地等待、退出码返回的主流程图，将原源码表折叠为查询对照；[原话与修正](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#task-flow-visible-diagram)保留本次反馈。源码阅读范围与认识状态沿用前次，[Step 8](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/01-scope.md)仍为已确认的后续接收入口。

2026-10-23 同日此前：根据用户此前的启动链整体复述，按已确认的 task-flow skill 与 Step 003 主 reference 修订 [Step 7 的 task flow](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/05-task-flow.md)。保留执行顺序表，合并重复交接说明，补齐结果去向与收束边界；[本次记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#task-flow-step-three-format)沿用原复述及校准状态。本轮没有新增函数阅读或掌握记录；[Step 8 接收入口](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/01-scope.md)继续作为已确认的接续范围。

2026-10-23 同日此前：本轮回应用户对 [Step 7 task flow 第 2 节](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/05-task-flow.md#2-按执行顺序接起来)调用树的质疑，按正常执行先后改为“当前代码、动作、下一站”的顺序表，并单列退出码返回链；原有交接解释保留，新写法待用户反馈。此前确认的 [Step 8 接收入口范围](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/01-scope.md)继续有效，尚未进一步展开或新增接收机制的理解记录。[本次原话与修订依据](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#execution-order-table)。

2026-10-23 同日此前：按用户确认先完成 [Step 7 的 task flow](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/05-task-flow.md)，收拢“准备账号与配置 → 组成命令和环境 → 启动 CLI → 等待退出码返回”；配置位置与执行边界的原校准仍保留其待反馈状态。新建 [Step 8 · Adapter 接收请求](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/01-scope.md)，专门接清 CLI 请求怎样到达监听服务、按路由进入 `_run_turn` 并解析出 `body`。本步范围已确认，首个补读点为 `adapters/anthropic.py::AnthropicAdapter._register_routes:48–50`，监听准备按需回查；两张所需旧卡已调入本步 `02`，`03` 合并前一步记录共 43 份。现阶段是导航与既有材料接续，尚未登记接收机制的新理解或真实网络运行。[本次分工记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/04-flow.md#request-entry-scope)。

2026-10-23 同日此前：[Step 7](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/README.md) 已收到用户对 `ensure_agent_user → HarnessContext → write_config → launch_and_wait → run_agent / exec_and_wait` 的整体复述，记录为阶段级认识；配置写入位置、ctx 与远端环境的区别、准备与执行分界的本次校准仍待反馈。当前明确问题转到“CLI 请求怎样到达 Adapter，`request` 怎样变成 `body`”。已将[既有 _run_turn](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)从本步 `03` 调入 `02`，并在[通信参考](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/references/run-communication-path.md#adapter-request-entry)补齐监听、路由与 JSON 读取的交接。下一处建议观察 `AnthropicAdapter._register_routes:48–50`，监听内部按需回查；未新建接收侧函数卡片或收束本步。[完整原话与校准](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#launch-restatement-and-http-entry)。

2026-10-23 同日此前：[Step 7](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/README.md) 继续研究 Harness 启动与跨组件通信，最近深入到 `run_agent → exec_and_wait`，底层等待机制仍待反馈。用户要求本步用到的旧函数也从长期记忆调入短期记忆；已将 [ensure_agent_user](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) 从本步 `03` 完整复制到 `02`，接到 `BaseHarness.run:97 → 98`，并更新当前入口。首次接触、原话、未知与最近认识时间保留；这是记录取用调整，不是重新开始阅读或新增掌握。[本次反馈与处理](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#reactivate-prior-function-memory)。

2026-10-23 同日此前：[Step 7](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/README.md) 继续研究 Harness 启动与跨组件通信；scope 保留完整骨架与第 4 项局部导航，`03` 从 Step 6 合并 38 份累计记录。用户提出主体与面包屑卡片的架构分工：敏锐指出 `run_agent`（`harness/common.py:107–122`）仅为 15 行特化启动包装，而 `exec_and_wait`（`sandbox.py:82–145`）则是跨越安装工具（Step 5 `install_npm_cli`）与运行 Agent（Step 7 `run_agent`）的底层通用长任务基础设施；要求建立两者双向链接并确立调用链面包屑机制。已在两卡片及父卡顶部建立统一的面包屑导航条（Breadcrumb Trail），修正精确相对链接；并根据用户确认将该机制正式沉淀为 Skill 库的第四种标准样例 [面包屑链路与通用基座参考](../../.agents/skills/repo-reading-short-term-memory/references/breadcrumb-navigation-and-shared-infra.md)。底层脱机与保活机制尚待用户反馈确认。

2026-10-23 同日此前：针对 `run_agent`，用户提炼出第 1 阶段特权建目录、第 2 阶段赋权并脱机执行、第 3 阶段等待完成标记（await done marker）三部曲；已澄清执行主体是 Agent CLI 自身而非评测测试脚本。已建立 [run_agent 短期卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md) 与 [exec_and_wait 短期卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)。

2026-10-22 同步：在 `run:104` 的 `ClaudeCodeHarness.launch_and_wait` 认知闭环后，用户确认进入下游通用调度函数 `run_agent` 并指示先建卡。当时已建初始卡片，尚未展开内部脱机机制。

同日此前：在 `run:104` 的 `ClaudeCodeHarness.launch_and_wait` 中，用户已完整复述“`launch_and_wait` 组装材料并修改环境变量，使读取环境变量的 Claude CLI 后续交互时向后端 HTTP 服务发请求”的心智模型，并敏锐指出单函数源码职责与下游背景的区别，进而推广到 Codex 等通用 Harness 机制（`write_config` 负责静态配置，`launch_and_wait` 组装 `env` 负责运行时请求重定向）。据此已在卡片中用双线框明确区分**本函数直接职责（57–71 行）**与下游协同背景，并将本卡沉淀为 Skill 模板库的第三种标准样例。[本轮原话与架构归纳](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#cmd-env-mental-model)已同步入库。

同日此前：用户追问准备完成后，信息怎样在本地调度、执行沙箱、Adapter 与 SGLang 之间传输。当时在 Step 6 补充的[跨组件通信参考，现迁至 Step 7](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/references/run-communication-path.md)，区分沙箱 SDK 启动、CLI 到 Adapter 的 HTTP 请求、Adapter 到 SGLang 的 HTTP 请求及两种完成时刻。旧 Step 1 已有折叠的上游说明，但不能据材料存在认定用户已建立整体关系。[原话与判断](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#run-cross-process-communication)保留。那时尚未新建 step 或函数卡片，原 Step 6 尚未收束，没有新增远端运行证据。

同日此前：用户在两个准备入口讲解后反馈“大概明白了”，并追问是否将 SWE 逻辑写入沙箱后交给下游。已在 [prepare_workspace 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md)澄清：题目命令在远端执行，Python 编排仍在本地；函数返回 `None`，`generate` 随后把同一个 `sb` 传给 Harness。下一处建议回到 194–198 行，看题目文本怎样写成 `PROBLEM_STATEMENT.md`。[原话与澄清](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#preparation-effects-and-sandbox-handoff)保留在 Step 6；尚未新建写文件卡片或结束本步，没有新增远端运行证据。

同日此前：用户在统一 md 输入入口后，明确要求阅读 `apply_pre_commands`。已创建[本函数卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md)，沿用真实题目的完整命令，解释“整理文本 → 写入远端脚本 → 进入工作目录执行”，并接回父函数 194 行。[本次原话、解释与验证](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#apply-pre-commands-function-card)保留在 Step 6。局部核对使用操作记录器，未执行 shell 或远端任务；当时机制解释尚待用户反馈，Step 6 未结束。

同日此前：用户进一步明确先读清 `md` 中的启动资料，包括 `grading`、`swepro`、`pre_commands` 和 `problem_statement`，再依次看 `apply_before_repo_set_cmd`、`apply_pre_commands` 与最后的 `sb.write_file`。已在 Step 6 补充 [md 输入说明](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/references/metadata.md)，并按用户后续确认将独立 grading 文档并入其中、删除原文件；scope 导航仍从 md 开始，`ensure_agent_user` 沿用已处理状态。[顺序修正](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#metadata-before-preparation-functions)与[入口合并](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#merge-grading-into-metadata)保留在当前步骤。后续函数未因此视为读完，Step 6 未结束。

同日此前：用户说明 `ensure_agent_user` 已处理完毕，要求结合刚才的真实题目重新确定 `prepare_workspace` 的阅读顺序和优先级。当时推荐为：简短核对 186–193 行配置分支 → 重点读 `apply_pre_commands` → 回到 194–198 行接清题目写入 → 收拢本函数与 Harness 的交接。[当时的顺序与理由](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#prepare-workspace-reading-order)保留。本例不触发 `apply_before_repo_set_cmd`，因此当时列为按需回顾；该安排现按上面的用户反馈修正。

同日此前：用户明确表示仍不清楚 `prepare_workspace` 的整体职责，追问 `eval_cmd`、`f2p_script` 的来源并要求真实例子。已在当前父卡采用公开 Scale-SWE 的 `auth0_auth0-python_pr671` 字段，区分准备命令、题目文字与后续测试代码；[真实例子与来源](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/references/scaleswe-auth0-example.md)标注了输入映射、脚本退出码及镜像接入的限制。[当时的问题与修正](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#real-task-preparation-example)保留在 Step 6。局部验证使用假沙箱记录真实准备函数的调用，没有执行 shell 或远端评测；新解释尚待反馈，本步未结束。

同日此前：用户对按题目配置执行提前准备的用途反馈“大概理解了”，类比 `pre_commands`，并明确希望先处理 `metadata` / `grading`。已在 Step 6 补充 [grading 输入参考（现已合入 md）](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/references/metadata.md#grading)，承接 Step 4 的 `md` 说明，区分原始 metadata、整理后的配置分组，以及准备命令与评测资料。[当时的反馈与解释](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#grading-input-context)保留在当前步骤；`apply_pre_commands` 尚未单独展开，没有远端运行，也未结束 Step 6。

同日此前：在 [Step 6 · 准备任务工作区](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/README.md) 中，用户指定先展开 `agent_sandbox.ensure_agent_user`。从 `prepare_workspace:185` 进入 `sandbox.py:390–399`，已在当前 `02` 整理执行沙箱场景的卡片，解释账号、目录归属与 Git 准备，正常返回后接回父函数 186 行。[当时的问题与讲解](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#ensure-agent-user-entry)保留在当前步骤，Step 2 的已有复述继续保留。

同日此前：用户确认开始阅读 `swe.prepare_workspace`，据此建立 Step 6。[scope](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/01-scope.md)继承完整骨架并聚焦第 3 项；[父函数卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md)接清用户准备、可选初始化、题目写入及返回 Harness 的关系。`03` 完整继承前一步 35 份记录；[当时的确认与讲解](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#prepare-workspace-entry)保留为形成过程。

同日此前：用户表示已基本完成对 `boot_agent_sandbox` 的理解，并询问是否可以总结本步。对照原 scope，已将 Step 5 的“镜像输入 → 环境与 CLI 就绪 → 交出 sb → 调用方使用 → 退出回收”收拢为 [task flow](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/05-task-flow.md)。[本次反馈与收束依据](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#agent-sandbox-flow-closure)分别保留用户表述与助手判断；命令等待、并发和完整故障恢复仍为按需深入项，没有新增真实沙箱运行。下一候选为 `swe.prepare_workspace`，尚未确认开启新 step。

同日此前：用户已复述本机材料上传后由远端命令完成安装，并将 for 理解为退出码与尝试次数的控制。已在 [install_npm_cli 主记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)保存原话，进一步区分 Node 与 CLI 包的处理路径、零与非零退出码、最多三次的 CLI 命令重试；这些细分解释尚待反馈。[本次复述与澄清](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#install-restatement-and-retry-boundary)沿用 common 为主记录、Claude Code 为传参入口的分工，未运行安装或结束 Step 5。

同日此前：用户已将已有远端沙箱与本机安装材料联系起来，追问究竟是发送包还是在沙箱中安装，并提出接着读公共安装函数。继续 Step 5，建立 [install_npm_cli 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)，按源码区分 Node 准备、CLI 包上传、远端安装与检查。用户初步复述和助手补充解释分别保存在[本次讨论](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#upload-and-remote-install)；新解释尚待反馈，未运行安装，也未展开命令等待和重试的内部机制。

同日此前：用户表示基本理解 `cand` 与 E2BSandbox，要求进入下一部分 `HARNESS_CLS().install_cli(cand)`。继续 Step 5，沿用 Claude Code 路径建立 [ClaudeCodeHarness.install_cli 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md)，先接清已有沙箱、两个本机安装包路径、检查命令与公共安装函数的交接。当时用户对对象模型的明确反馈已保存，安装交接尚无机制复述，下层安装、上传与命令等待仍待按需展开。[当时的问题与边界](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#install-cli-entry)保留原话和静态证据，不标记 Step 5 完成。

同日此前：用户确认将 E2B 沙箱的共用对象模型整理成独立卡片。已在 Step 5 的 `02/classes/` 建立 [E2BSandbox 类卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)，保存构造与进入后的字段状态、本地客户端和远端环境的关系、五个操作入口；父函数保留编排并链接类卡，进入与退出复用既有记录。[当时的确认与整理](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#e2b-class-card)与后续阅读反馈分开保留。

同日此前：用户表示大概理解 `boot_agent_sandbox`，已复述本地构造 `cand`、进入 `__aenter__` 时申请远端环境，继续追问服务地址、`_sb` 和后续通信。曾在 [Step 5 的函数卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md)补充“Slime 本地封装 → SDK 本地客户端 → 网络请求 → 远端环境”的关系；[完整原话、解释与版本边界](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#sandbox-client-and-address)分别保留。该共用模型现由上面的类卡承接，补充解释仍待反馈。

同日此前：用户明确要求分析 `boot_agent_sandbox` 并单独建立短期函数记录，已整理整体输入输出以及准备、交付和回收两段实现；进入与退出复用既有卡片。曾用原函数和替身核对四条局部路径，未运行真实沙箱或 CLI。建卡时尚无机制复述，完整问题与证据见[当时记录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#boot-agent-sandbox-function-card)。

同日此前：用户要求简单建立启动执行沙箱的步骤，并明确先弄清 scope、不提前填写具体函数。已创建 [Step 5](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/README.md)。用户随后指出 scope 仍有缺项；在 [scope](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/01-scope.md)的完整骨架下补出第 2 项 `boot_agent_sandbox` 的局部骨架、阅读导航和返回位置，见[本次修正](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#scope-local-skeleton-correction)。当时 `02` 尚无新函数卡片，`03` 完整继承前一步的 31 份记录；[最初范围确认](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#scope-confirmed)及格式修正均不代表已经读懂新的实现。

同日此前，用户询问下一处是否适合读 `boot_agent_sandbox`。助手推荐从 `generate.py:203` 的调用进入同文件 `96–134` 行，围绕“准备执行沙箱与 CLI → 交出 sb → 退出清理”收窄下一步范围；复用 Step 2 的沙箱进入与退出记录。[推荐理由与建议边界](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#boot-agent-sandbox-recommendation)保留为范围确认前的讨论。

同日此前，用户提出结束 Step 4 并整理 task flow。本步“取得 Adapter → 取得执行编号 → 登记配置 → 后续取用”的阅读主线已收拢为 [任务总结](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/05-task-flow.md)。最新复述中的“题目基础信息都存入 store”已校正为“仅登记采样默认值与上下文长度，题目信息仍由 base_sample / md 承载”；[原话与本次收拢](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#session-registration-flow-closure)分别保留用户表述和助手解释。该字段边界的校正尚待反馈，收拢不等于全部实现已掌握。

同日此前，用户从 Session 类卡回到 open_session，复述编号与两项配置保存在 Adapter 中、作为会话状态的关系。已在 [open_session 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)保存原话，并校准“调用前由 _session_id 取得编号 → open_session 按编号登记配置”的职责边界。[当时的复述与校正](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#open-session-state-restatement)不自动算作完整编号规则或参数使用机制已掌握。

同日此前，用户认可类卡片方向，要求生成 Session 卡片，并提出它是 per-session state 的理解。已将主体说明整理为 [Session 类卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md)，沿用同一编号例子，区分类、实例、变量与 store 中的关联；源码中的 Session 只承载两项会话配置。原 reference 保留入口和语法依据。[当时的原话与解释](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#session-class-card)保留为形成过程；卡片详略与补充区别待反馈，未标记本步完成。

同日此前，用户指出应区分真实定义的 class / dataclass 与场景变量。助手修正此前“不是函数就放入 reference”的分类理由，提出在正式记忆中增加类卡片；[具体方案](../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#class-memory-vs-reference)与[当时的问题](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#session-class-record-question)继续保留，现由上面的 Session 卡片试用承接。

同日此前，用户初步复述 open_session 将编号与采样配置保存在 store 中，进一步追问 Session 是什么及其记录归属。已建立 [Session 对象参考](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/references/session.md)，区分根据两项配置创建对象与按 sid 将对象登记到字典；Session 自身没有 sid 字段。原 open_session 卡片保留完整函数模型并链接参考，对象与编号关系仍待后续反馈。[此前原话与说明](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#session-object-reference)继续保留。

同日此前，用户要求沿用 `_session_id` 的例子，单独阅读 Adapter 的 `open_session`。已更新 [BaseAdapter.open_session 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)，说明当前 AnthropicAdapter 继承该方法、`self` 对应 `state.adapter`，并用 `cagent-demo-1-0-0` 展示登记前后的 store。当时聚焦“编号 → Session 配置”的对应、返回 `None` 与后续按编号取用。[此前原话与解释](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#open-session-same-example)继续保留。

同日此前，用户复述执行编号与题目、样本字段的关系，并要求保存在编号函数记忆中。已建立 [_session_id 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_session_id.md)，校正为旧编号优先、索引齐全时拼接、索引缺失时使用随机串三种规则，并区分返回编号、调用方保存编号和 open_session 登记配置。`metadata`、`prompt` 不由该函数读取。上述校正未逐项确认，不据建卡标为全部掌握。[此前原话与校正](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#session-id-function-memory)、[此前 md 的初步理解与 Sample 示例](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#sample-definition-and-example)均保留。

此前用户提出将几个名称保存在 reference 中，并要求参照 Step 003 分开解释。合并说明已改成[输入背景参考目录](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/references/generate-input-context.md)，分别进入 base_sample、protocol、md、instance_id 四份说明，session_id 的概念直接复用 Step 003。当前编号规则另由函数卡片承接，名称说明不替代函数实现与理解反馈。

同日此前，用户首次复述 tokenizer、SGLang 地址和解析器集中到 Adapter，用于提前“把基础服务层先搭建好”。已在 [_AdapterService.__init__ 卡片](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md)保存原话，并补充对象、地址和解析器名称的区别，以及创建 Adapter 与启动其 HTTP 服务的先后。此次职责层面的理解不等于完整初始化、对象归属或服务机制已掌握；[原话与澄清](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#adapter-dependency-restatement)保留为形成过程，尚待后续反馈。

同日此前的范围纠正：用户明确 [Step 004](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/README.md)只看 `adapter.open_session`，并要求沿用 Step 001–003 的 scope 构建方式。现已恢复完整骨架，只展开第 1 项会话配置登记；`boot_agent_sandbox` 与 `prepare_workspace` 留在骨架中定位，不属于本步范围。[本次范围纠正](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/04-flow.md#scope-narrowed-to-open-session)保留了初始解释及用户反馈。27 份前序函数记录和已有 open_session 卡片保留；用户尚无新函数的独立机制复述，不能将格式反馈记成掌握。[Step 3 任务总结](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/05-task-flow.md)及其大致理解反馈保留，内部组装算法、改动提取与外层清理的未知继续保留。

2026-10-22 此前的轨迹复述：用户明确提出回到 `manager.get_trajectory`，进一步复述取树、遍历叶子、取得 chain 并转换为 samples，追问不同叶子是否消除了重复。本轮区分共享历史与重复训练信号，建议先保留组装函数的输入输出和处理结果，具体算法后置。[当时的复述与澄清](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/04-flow.md#trajectory-leaves-and-shared-prefix)保留为形成过程；后续 rollout 方向仍仅为建议。

2026-10-22 此前的收尾回补：拆开 sid 与 inflight 说明后，用户再次复述 shutdown_session，已初步将 sid 对应到某道题的一次会话，并说明关闭标记的目的。核对了四处区别：已有会话的关闭、仅取当前 sid 请求、先等再取消、提交协程与等待结果。[原话与校正](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/04-flow.md#shutdown-restatement-after-split)继续保留，未将后续整体反馈扩写成逐项机制确认。

2026-10-21 的接续背景（当前状态以下方条目为准）：用户在 Step 3 已初步复述 `get_trajectory` 从 manager 的 routing tree 取得轨迹的外层职责，并明确拼接、分段与 mask 仍需深入。助手推荐继续组装后，用户指出尚需先理解 `shutdown_session` 与 `store.pop`，随后明确先处理 `shutdown_session`。已建立该函数卡片，核对关闭标记、等待、超时取消与跨循环交接；下一处返回 `finish_session:262–263` 接清配置取出与长度上限，轨迹内部组装后置。此前轨迹局部验证和初步复述保留，不升级为全部机制掌握；`finish_session` 尚无独立机制复述；`shutdown_session` 已有关闭入口与收尾目的的初步复述；用户最新明确 `sid`、`inflight` 的含义仍不清楚，当前先补状态背景，不推进下一函数。此前 `_run_turn`、评测与 Sandbox 的已读事实继续保留。Step 0–2 保留快照，Step 3 的 `03` 继承前序全部 24 份函数记录，旧 initial-model 继续归档。这里是唯一的学习接续记录；下方章节合同、旧材料和源码索引不能覆盖它。

- **目标与条件：** 按用户提供的腾讯混元 Agent 强化学习框架工程师 JD 决定详略。本地无 GPU，以读明白和模型 API 辅助验证为主；前置与初始时间预算见[岗位对照](job-alignment.md#当前学习条件与投入安排)。
- **当前协作：** [Step 7](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/README.md) 已由用户确认独立研究本地启动、沙箱 CLI、Adapter 与 SGLang 的通信关系；Step 6 保留原准备函数与未收束项。
- **认知记录入口：** 使用[通用工作流](../../00-repo-reading/workflow.md)与 [Step 7](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/README.md)。本步 `03` 合并 Step 6 的 35 份累计记录与 4 份本步记录，按符号合并为 38 份（36 个函数入口，含引用文件；2 份类记录）；同名 `ensure_agent_user` 的两种场景完整保留。`02` 保存 `BaseHarness.run`、`ClaudeCodeHarness.write_config`、`ClaudeCodeHarness.launch_and_wait` 及 `HarnessContext` 类卡片。前序卡片保留，形成过程链接回到真实来源。
- **已读范围与记忆提醒：** 用户明确表示 `generate()` 的完整任务链已经走过，同时提醒走过不等于全部记住。保留已读事实；续读时先短回顾职责、输入输出与主线位置，根据具体问题补细节，不默认重讲全链，也不自行断言忘了哪些部分。
- **当前问题：** Harness 怎样把命令和环境送入沙箱；CLI 根据哪个地址请求 Adapter，Adapter 又怎样请求 SGLang；各自的响应回到谁。
- **当前入口与下一处：** 当前沿 [Step 7 scope 的局部导航](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/01-scope.md#harness-local-navigation)展开 [ClaudeCodeHarness.launch_and_wait](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) 的命令、环境变量和委派执行，尚待理解反馈。下一处候选是 71 行调用的 `run_agent`，看启动材料怎样交给实际执行与等待流程。需要全局位置时回查[通信参考](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/references/run-communication-path.md)。
- **本轮停止点：** 已解释并用本地记录器核对 `launch_and_wait` 的参数组装和退出码传递；下层脚本、启动和等待标记仅定位，CLI 内部请求循环仍留白。用户此前的运行信息与配置准备复述保留，没有新增远端运行证据；Step 7 的 task flow 留待阅读后总结。
- **资料用法：** 官方整体实验入门的 “The loop you are building” 用于概念对照；`agent.html` 用于查 Agent 接入点；本地 00 用于职责定位；实际调用以当前固定源码为证据。它们服务同一条阅读主线，不互相替代成新的课程顺序。
- **心智模型与正文：** 通用方法在 `00-repo-reading/`。Step 7 的 [02 索引](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/overview.md)指向本步函数，[03](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/overview.md)保存前序累计记忆。scope 负责导航，函数卡片解释单函数模型，04-flow 保存过程，通信参考连接运行位置和接口，task flow 在读通后总结。本轮继续写入本地 repo-reading，公开 walkthrough 保留既有内容，当前状态只在本节维护。

### 阅读与验证记录

| 范围 | 阅读反馈 | 理解与运行证据 |
| --- | --- | --- |
| 00 全局职责与启动主线 | 保留框架背景材料；2026-10-20 用户明确本轮从 Coding Agent 开始 | 不作为当前起点；外层机制按需再展开 |
| 01、02 中的 `generate()` 完整任务链 | 用户 2026-10-19 明确反馈已完整走过，并说明内容可能未全部记住、需要提醒 | 具体记忆缺口未逐项反馈；已读不等于全部分支验收，本轮没有真实 Agent、GPU 训练或集群运行证据 |
| Step 1 的 `call_sglang_generate` | 曾反馈内部黑盒感，已保存六段执行地图与 `sp` 合并示例；后续对生成 token 的 logprob 与全词表概率的区别反馈“大概理解了”并继续下游 | 原 `_sampling_params` 已局部验证；完整生成函数的字段与分支不据此全部计为掌握，旧讲解继续保留 |
| Step 1 的 `_respond` | 用户提出将已有内容组织成可传输响应的理解，在结构示意后反馈“大概理解了” | 记录其总体理解；协议字段、流式行为及发送时机未逐项确认 |
| Step 1 的 `TrajectoryManager.record_turn` | 用户提出逐轮存入树、复用已有部分的初步理解，并联想到按成功率剪枝；记录与搜索决策的区别已解释，尚待反馈 | 原类局部验证首次记录、历史复用、短回复改写及分叉对照；奖励和导出用途仅静态核对，不代表完整训练轨迹或模型运行 |
| Step 1 的 `_run_turn` 整体交接与收尾 | 用户 2026-10-21 明确表示“当前这里run turn理解完了”，并开始询问面向 Coding RL 的下一处入口 | 本次函数整体阅读范围记为已理解；未逐项延伸为全部子函数和异常边界已掌握，没有新增端到端或取消测试 |
| Step 2 的独立评测与奖励来源 | 用户 2026-10-21 确认开启；主读 `run_evaluation → _grade_scaleswe` 的 `eval_cmd` 分支，配套 `_apply_diff` 与 `_run_eval_cmd` | 已准备同场景函数卡片；用户已复述进入时按镜像配置申请远端沙箱，内部过程暂作黑箱。环境进入已有替身 SDK 的局部验证，不计为真实沙箱、测试或训练运行 |
| Step 3 的会话轨迹到训练样本 | 2026-10-22 明确表示已大致理解 get_trajectory 与 finish_session 的整体内容，已整理任务总结；具体 mask、拼接和外层清理仍有后续阅读项 | 单轮、四组两轮和共享前缀分叉的构造数据核对导出字段、续接/拆分、共享 mask、遍历后移除与其他会话保留。本轮只静态复核，没有新增运行实验。没有真实 CLI 压缩、模型生成、HTTP 请求或训练；整体理解与完整算法、真实运行分开记录 |
| Step 3 的 `shutdown_session` 请求收尾 | 2026-10-22 拆分说明后再次复述：sid 与单次会话已有对应；当前校正创建/关闭、当前 sid/全部请求、等待/取消及提交/等待结果的区别 | 沿用原方法的四组本地 Task 验证；本轮只静态核对与补充原话，没有新增实验，未验证真实远端取消、循环停止或异常收尾 |
| Step 4 的 Adapter 服务准备 | 2026-10-22 首次复述将 tokenizer、SGLang 地址与解析器放入 Adapter，提前搭好服务层；已补充材料类型和服务启动边界，尚待进一步反馈 | 静态核对创建参数、保存属性及 HTTP 启动位置；未执行初始化或新增运行实验 |
| Step 4 的输入背景 | 2026-10-22 自述大概理解 md，已联系题目字段、get_metadata 与取出 instance_id；继续追问 Sample 的定义和实例 | 静态核对 types.py 的相关字段及 CPU 测试中的构造示例；对象与字典的补充说明尚待反馈，未将完整元数据规则或编号算法计为掌握 |
| Step 4 的执行编号 | 2026-10-22 复述题目编号与样本索引的组合，要求建立 `_session_id` 函数记忆；实际使用字段、旧编号优先与随机分支已校正，尚待反馈 | AST 提取原函数，以字段对象核对六组局部输入、返回格式及输入不变；未运行完整 Sample 加载、会话登记或远端任务 |
| Step 4 的会话配置登记 | 2026-10-22 提出结束本步并整理 task flow；按已读交接收拢主线，最新“题目基础信息都存入 store”的表述已补充字段边界，尚待反馈 | 沿用此前登记、默认值、重复编号、同一编号连续交接与 Session 构造的局部验证；本轮仅静态核对，没有新增完整 Adapter 或远端运行 |
| Step 4 的 Session 类卡片 | 2026-10-22 确认生成类卡，并提出 per-session state 的理解；实例与变量、配置与全部状态的区别已补充，尚待反馈 | 沿用上一轮字段与构造的局部验证；本轮静态核对源码、卡片和链接，没有新增完整运行实验 |
| Step 5 的启动执行沙箱 | 2026-10-22 用户表示基本完成对 boot_agent_sandbox 的理解；已复述本地对象、远端申请、上传与安装，并按原 scope 收拢 task flow | 原函数配替身的四条局部路径验证保留；准备、交付、使用与回收已静态核对。底层等待和完整故障恢复尚未展开，没有真实远端沙箱、CLI 安装或 Agent 运行 |
| Step 6 的任务工作区准备 | 2026-10-22 用户在两个准备入口讲解后反馈“大概明白了”，继续追问沙箱交接；已补充本地编排与远端效果的区别，末尾题目写入待继续 | 已用真实字段和操作记录器核对准备调用，以及 apply_pre_commands 的字符串、列表和非零结果情形；本轮静态核对下游交接，未执行 shell、沙箱或评测，原始评测脚本仍有退出码适配缺口 |
| Step 7 的 Harness 启动与等待 | 2026-10-23 用户已整体复述启动链，随后确认先收拢 task flow；配置位置、ctx 去向与执行边界的校准仍待反馈 | 沿用既有局部验证；本轮静态核对和整理，没有新增真实启动、网络报文或模型运行 |
| Step 8 的 Adapter 请求接收 | 2026-10-23 用户确认将 HTTP 接收入口独立成步；目前建立 scope 并调取旧卡，接收机制待逐处带读 | 已核对固定版本的应用、路由、监听与 Request/body 入口，没有新运行实验或个人掌握记录 |
| 02 的轨迹分叉、改写与 token 对齐专题 | 入口保留为深入材料 | 没有整章或专题完成反馈，不自动续读这些内部细节 |
| 03–07 的独立深入单元 | 按当前主线与岗位优先级继续；本轮无逐单元完成反馈 | 不从 planned/ready 或测试材料存在推断已读、掌握或运行 |

用户明确反馈已读、卡住、跳过或改读另一层时，同轮更新本节的范围与下一步；章节 README/review 只链接本节。源码版本变化保留已读事实，另记需重新核对的接口差异。

### 当前源码与已有材料的版本边界

- 2026-10-23 当前实测仓库：`/home/hongshi/projects/slime`，HEAD `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；工作区干净。实时 `git ls-remote https://github.com/THUDM/slime.git HEAD refs/heads/main` 返回同一 SHA。Step 0、Step 1 scope 已按 `18868a79` 校准、旧版已归档；Step 1 已校准 `_translate`、`_render_token_ids`，新增 `_session_prompt_ids` 卡片；其余函数卡片与 task flow、Step 2–8 的记录仍保留各自原版本，待逐项迁移；[差异与迁移建议](../../00-repo-reading/repositories/slime/version-reviews/2026-10-23-2f231865-to-18868a79.md)单独保存。
- 此前核对时，本地 HEAD 为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，曾有 `swe.py` 空白改动及未跟踪的 `asyncio_concurrency_best_practices/`、`pelican-bicycle.html`、`qin-polar-bear.html`；这是历史工作区记录。本轮只读核对，没有删除或重置这些内容。历史 `/home/fredkeira/projects/slime` 在本机不存在。
- 2026-10-22 开始 Step 4 时再次查询官方 `THUDM/slime` main，仍为 `a4202e0595467d9374d9a68d45a34f45c3f8d230`；沿用此前官方比较结果：领先本地 22 个提交，返回的改动列表包含 `agent/adapters/common.py`、`agent/trajectory.py` 及 Coding Agent 的 `generate.py`、`swe.py`。本轮未更新 checkout，讲解与行号继续绑定 `2f231865`；没有把 main 的变化混入已读模型。
- 同日继续阅读 open_session 时，官方 main 已为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本地 HEAD 仍为 `2f231865`。本次只核对远端引用，未比较这一新提交的文件差异，以上 22 个提交的比较仍归属于此前的 `a4202e0`。本轮不更新 checkout，函数解释与验证继续绑定本地固定版本。
- 旧版 `2f231865` 已核对的入口：`train.py::main` 第 103 行、`create_rollout_manager` 第 293 行、`RolloutManager.generate` 第 303 行、`generate_and_rm` 第 289 行、Coding Agent `generate` 第 182 行、`BatchBuilder.convert` 第 237 行。新的讲解继续核对实际调用，不将此定位记录当作运行证明。
- 下方 26 项索引和原章节合同仍保留 `22a89f9` 的固定来源，4.1 图文还含 `8c17b67`；未逐项迁移，不批量替换提交链接。官方版本查询见[总入口](README.md#每次开始前确认源码与官方最新版本)。

## 4.1 单任务导览与回查入口

既有 **4.1 Agent Rollout Adapters and Harnesses** 导览以 `generate()` 的整次任务为主线，现有 01 任务执行与 02 模型/上下文单元共同说明其内部交接。以下材料保留供已读任务链回查，不作为当前必须重读的安排；26 项清单用于定位和扩展。 连续讲解见 [01 单元 walkthrough](chapters/01-task-execution/walkthrough.md)，回顾见 [review](chapters/01-task-execution/review.md)。 调用 Harness 前先读 [Pre-4：启动前准备](chapters/01-task-execution/pre-4-preparation.md)。目录放在 3.5 后、4 前，真实执行仍按准备、启动、模型请求、收尾推进。 Pre-4 已按 Adapter Service、任务信息、会话/默认采样、环境/CLI、工作区/题目逐项展开，并在末尾核对 run 的六个参数和隐含条件。 总览图先汇集五项准备及其成果，再接入 Harness.run。 章节完整存档见 [Pre-4 文件夹](../../slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/Pre-4.启动前准备/README.md)；内部导览可从 [Harness.run 主线](../../slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/4.Launch%20Agent/4.Harness.run调用与职责.md) 进入 [动作5环境能力](../../slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/5.Manage%20Sandbox/README.md)，读清后回到调用处继续。

推荐路径：准备任务、模型入口和会话 → 创建沙箱、准备工作区 → Harness 配置并启动 CLI → CLI 回连 Adapter → 消息转换、模型生成、响应与本轮轨迹 → CLI 继续或结束 → 回到 generate 收集 diff、独立评估、训练轨迹导出与清理。模型请求阶段是 CLI 运行中的嵌套循环，Sandbox 操作贯穿准备、运行与回收。

每步只需走通相关函数的输入、主要行为、输出/副作用与下一次交接；组件展开完就返回主线。先完成正常路径，再补超时、非零退出、空轨迹和失败清理。完成标准是能拿一份具体代码任务连续复述完整闭环，而不是逐行读完全部文件。

## 各 Action 的语境与文件范围

每章局部图后单独说明当前主线、本章职责与返回位置；主要源码文件和入口默认收起。统一划分见 [action-contexts.md](action-contexts.md)，具体文件/符号清单由 [action-contexts.json](action-contexts.json) 维护并生成网页。`generate()` 编排一次样本任务，2 → 3 → 3.5 展开一次模型请求，5、6 展开环境能力及长命令执行机制；它们是嵌套调用和职责划分，不是依编号依次运行的阶段。这里不另建阅读顺序或学习状态。

## 需求对照

[目标需求与阅读单元对照](job-alignment.md) 保存岗位来源、能力映射和待补实践。开始一个单元时选对应需求，再用“模块责任 → 扩展接缝 → 失败情景 → 验证证据”四问检查阅读是否对准目标。具体顺序和学习状态仍由本路线维护。

## 既有材料的固定来源（2026-10-10）

本节保留既有材料的历史来源；本机 checkout 和当前阅读接续以上方记录为准。历史段落中的“本轮”指 2026-10-10 的材料整理，不表示当前会话。

- 本地仓库根目录：`/home/fredkeira/projects/slime`；核心包：`/home/fredkeira/projects/slime/slime/`。`examples/`、`train.py`、`tests/`、`tools/`、`docker/` 也在范围内。
- 本轮核对版本：`22a89f96835969a47055a659c588f46151f8b07a`（本地 HEAD，2026-10-10）。固定源码链接指向这一提交，入口、行号与文件内容核对见 [source-map.json](source-map.json)。
- 已直接查询官方 THUDM/slime main：核对时为 `d06df4d77a1fbcf7bdc48e13071cf649e670133a`，比本地领先 1 次提交，仅改动 CPU CI 和回归测试。本轮保留本地快照；核对命令与状态见 [README](README.md#每次开始前确认源码与官方最新版本)，数据证据见 [upstream-check.json](upstream-check.json)。
- 仓库存在未跟踪的旧阅读记录；本路线保留它们。本轮范围内的源码文件与 Git blob 一致，未修改源码仓库。
- 现有 4.1 动作材料基于 `8c17b676cb57af1d17ee4402e91e9209af84b60b`；旧短课/复用路线使用 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。旧资料辅助定位，具体调用与行号以本轮固定源码为准。
- 新路线只在本 `code-reading/` 目录和网站“源码阅读顺序”页作为当前记录；源码仓库旧 `docs/repo-reading-route.md` 保留原目标与状态，不能混合计入本轮进度。
- 本轮为静态源码定位与路线材料，未运行 Agent、沙箱、模型服务、训练或 Kubernetes；没有用户掌握状态的推断。
- 历史检查报告 `historyTruncated=true`：本轮不做历史成长讲解，也不把最近提交窗口当作全仓历史。

## 快速浏览与深入的分工

从[当前接续](#当前接续)进入。先建立基本工作流，再按当前问题逐步展开；主线遇到已读的 4.1 任务组件时短回顾。进入新组件时先读问题、职责、少量入口和理解检查，函数太长时先列调用与数据交接。材料已展开的范围不等于用户已读、记住或掌握。

00–07 表达职责与依赖，投入重点按[岗位对照](job-alignment.md#当前学习条件与投入安排)调整。01、02 供已读任务链回查，03–05 优先补扩展、验证和稳定性，06、07 先定位资源与训练交接再按需深入。trace、explain、locate 表示目标阅读深度，不是已完成的学习状态。

| 顺序 | 单元 | slime_photo 对照 | 先能说明什么 | 前置 |
| --- | --- | --- | --- | --- |
| 00 | [全局职责与三种运行粒度](chapters/00-overview/README.md) | 1.1、4、7.1 | 先认识各模块做什么、在哪里运行，以及任务、请求、训练的包含关系。 | 无；从这里开始。 |
| 01 | [完整任务、Harness 与执行环境](chapters/01-task-execution/README.md) | 4.1 的动作 4、5、6、7；7.1 | 掌握任务执行的责任划分、环境接口、成功和失败的清理位置。 | 00；已知道任务、请求和训练的区别。 |
| 02 | [模型协议、上下文与训练轨迹](chapters/02-model-context/README.md) | 4.1 的动作 2、3、3.5；补读会话结束 | 掌握模型调用封装、工具消息处理、上下文变化和轨迹导出的接口。 | 01；已连接 CLI 配置、HTTP 路由与任务会话。 |
| 03 | [策略接入、数据生成与评测合同](chapters/03-strategy-evaluation/README.md) | 4.5、3.4、3.3、3.2、3.1；7.5/7.6/7.10 作为对照 | 掌握单样本生成、整批 rollout、评分、hook、过滤和评测配置的区别。 | 00–02；知道 Sample 与一次任务的返回边界。 |
| 04 | [Trace、结果分析、测试与复现](chapters/04-trace-validation/README.md) | 9、8.2、3.5；源码 tests/ 和复现文档 | 掌握 Trace 与日志的区别、结果分析、接口测试、实验配置和可复现性边界。 | 01–03；已能指出执行与评测的关键交接。 |
| 05 | [并发、任务数据、背压与恢复](chapters/05-concurrency-recovery/README.md) | 7.7、4.5、4.6；6.2 为独立服务对照 | 掌握 Asyncio 调度、并发预算、任务队列、传输、持久化、取消和恢复的职责。 | 03、04；知道组级输出合同与验证方式。 |
| 06 | [模型服务、Ray 资源与容器边界](chapters/06-serving-resources/README.md) | 4.3、4.4、2.1；Kubernetes 为独立实践 | 掌握运行位置、服务生命周期和资源治理，能定位 Kubernetes 需要补充的适配。 | 01、05；知道执行环境与并发预算的边界。 |
| 07 | [训练交接、策略版本与权重更新](chapters/07-training-handoff/README.md) | 4.2、5.1、7.8；7.9 与 SFT 作为第二遍 | 掌握生成与训练的工程合同、基本 RL/SFT 区别、checkpoint 与策略版本边界。 | 02、03、05、06；了解 Sample、结果传输与模型服务。 |

## 最终代码阅读清单

这是既有文件/函数索引，依附原有 00–07 单元；当前接续与学习状态只在[当前接续](#当前接续)维护。路径相对于 Slime 仓库根目录，源码链接保留 `22a89f96835969a47055a659c588f46151f8b07a` 的固定来源，不冒充当前 checkout。

**01–26 条目用于回查职责、输入输出、停止点与配套验证，接续位置以上方记录为准。** Trace 与契约测试从当前主线配合使用，配套测试先看 fixture/断言，不把源码阅读当作运行通过。

全局入口为 README 架构段与 `train.main`；4.1 连续导览提供单任务内部调用链，沿用 Claude/Anthropic 图文，Codex/OpenAI 保留为同一职责的实现对照。已经读过的调用链只按本轮问题回查，不作为必须重读的起步。

### 00 全局职责

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 01 · 样本数据合同 | [slime/utils/types.py · Sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/types.py#L107) | 只读主要字段到 SpecInfo 前：任务身份、prompt、tokens、reward、mask、logprob、状态和 Session。 | 先能说明一次任务、一次请求、一份训练样本的区别；完整序列化与所有方法后置。 | [tests/test_sample.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_sample.py#L1) |

### 01 完整任务与环境

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 02 · 一个任务的调用骨架 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | 读完 generate 的准备、Harness、diff、独立评分、训练/评测返回和 finally；boot 重试实现暂不展开。 | 解释 CLI 退出码与 reward 的区别；第二遍追超时、空轨迹和失败。 | [tests/test_agent/test_agent_rollout_cpu.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_agent_rollout_cpu.py#L1) |
| 03 · 可替换的 Agent 启动骨架 | [slime/agent/harness/common.py · BaseHarness.run](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L81)<br>[slime/agent/harness/common.py · run_agent](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L107) | 读 user/config/launch/wait 的交接；安装 Node/npm 的辅助函数先停住。 | 能指出新增 CLI 要实现的步骤；测试 fixture 和调用顺序断言随读。 | [tests/test_agent/test_harness.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_harness.py#L1) |
| 04 · 先选一种 CLI：Codex | [slime/agent/harness/codex.py · CodexHarness.write_config](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/codex.py#L56)<br>[slime/agent/harness/codex.py · CodexHarness.launch_and_wait](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/codex.py#L69) | 看配置模板、模型地址、session 与启动环境；到外部 CLI 边界停止。 | 能把 CLI 配置与 OpenAI Adapter 路由接起来；Claude 分支放在完整链读通后的实现对照。 | [tests/test_agent/test_harness.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_harness.py#L1) |
| 05 · 执行环境和长命令 | [slime/agent/sandbox.py · Sandbox](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L28)<br>[slime/agent/sandbox.py · exec_and_wait](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L82) | 读环境操作合同和等待函数；区分 detached spawn、退出标记、重复调用与等待预算。 | 第二遍展开 E2B RPC、超时和重放；Kubernetes 后端需另外实现与验证。 | [tests/test_agent/test_sandbox_exec_and_wait.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_sandbox_exec_and_wait.py#L1) |
| 06 · 任务产物与独立评分 | [examples/coding_agent_rl/swe.py · git_diff](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L230)<br>[examples/coding_agent_rl/swe.py · run_evaluation](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L239)<br>[examples/coding_agent_rl/swe.py · _grade_scaleswe](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L253) | 选 eval_cmd 评分分支，追 diff 如何在新的评估环境中应用；swepro/SWE-bench 的全部实现后置。 | 说明工作环境和评分环境分别由谁创建与清理；fake 测试不能证明真实 E2B/数据集评分。 | [tests/test_agent/test_agent_rollout_cpu.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_agent_rollout_cpu.py#L1) |

### 02 模型、上下文与轨迹

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 07 · 先选一种模型协议：OpenAI | [slime/agent/adapters/openai.py · OpenAIAdapter._register_routes](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/openai.py#L47)<br>[slime/agent/adapters/openai.py · OpenAIAdapter._translate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/openai.py#L53)<br>[slime/agent/adapters/openai.py · OpenAIAdapter._respond](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/openai.py#L69) | 用一份包含 tool_calls/tool 结果的请求，读路由、翻译和非流式响应；SSE 后置。 | 说明请求直接来自 CLI，协议名不是实际模型供应商；对照 Anthropic 时共享流程不用重读。 | [tests/test_agent/test_adapters.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_adapters.py#L1) |
| 08 · 一轮共享模型处理 | [slime/agent/adapters/common.py · BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L318)<br>[slime/agent/adapters/common.py · call_sglang_generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L442) | 读完两个函数，标出 sid/inflight/rid、模板 token、SGLang /generate、logprob、响应与记录。 | 当前实际顺序为 parse → respond → record_turn；第二遍再读取消与预算分支。 | [tests/test_agent/test_adapters.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_adapters.py#L1) |
| 09 · 输出和工具调用解析 | [slime/agent/parsing.py · parse_model_output](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L25)<br>[slime/agent/parsing.py · parse_tool_uses](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L59) | 读 reasoning/text/tool_uses/ill_formed 的返回形状；外部 parser 内部实现先停住。 | 分清解析工具调用与实际执行工具的责任；配套测试部分依赖 SGLang。 | [tests/test_agent/test_adapters.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_adapters.py#L1) |
| 10 · 上下文记录到训练 Sample | [slime/agent/trajectory.py · TurnRecord](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L29)<br>[slime/agent/trajectory.py · TrajectoryManager.record_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L283)<br>[slime/agent/trajectory.py · TrajectoryManager.get_trajectory](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L307)<br>[slime/agent/trajectory.py · _SampleBuilder.to_sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L234) | 只追一条正常工具多轮链，核对 tokens、mask、logprob 与 reward 的导出。 | 每个输出 Sample 当前赋完整 reward；第二遍选一种分叉/压缩/token drift，不通读全部消息树辅助实现。 | [tests/test_agent/test_trajectory_manager_branching.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_trajectory_manager_branching.py#L1) |
| 11 · 会话完成、导出与清理 | [slime/agent/adapters/common.py · BaseAdapter.finish_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L245)<br>[slime/agent/adapters/common.py · BaseAdapter.drop_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L278)<br>[slime/agent/adapters/common.py · BaseAdapter.shutdown_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L225) | 看在途请求等待、样本导出/解码与 cleanup-only；线程 drain 细节留到并发问题。 | 能区分本轮 HTTP 请求结束、Session 结束与任务结束。 | [tests/test_agent/test_agent_rollout_cpu.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_agent_rollout_cpu.py#L1) |

### 03 策略与评测接入

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 12 · 策略如何接回生成流水线 | [slime/rollout/sglang_rollout.py · generate_and_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L289)<br>[slime/rollout/sglang_rollout.py · generate_and_rm_group](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L384)<br>[slime/rollout/base_types.py · call_rollout_fn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/base_types.py#L28) | 定位 custom generate → hook → RM，组级并发/评分，以及整批 rollout 包装的不同返回合同。 | 说明单样本扩展和替换整批 rollout 的区别；queue identity 继承细节留到 22。 | [tests/plugin_contracts/test_plugin_generate_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_generate_contracts.py#L1)<br>[tests/plugin_contracts/test_plugin_rollout_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_rollout_contracts.py#L1) |
| 13 · 可替换评分器 | [slime/rollout/rm_hub/__init__.py · async_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/rm_hub/__init__.py#L55)<br>[slime/rollout/rm_hub/__init__.py · batched_async_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/rm_hub/__init__.py#L99) | 读分发顺序和单样本/批次函数签名；数学 grader 与远端重试后置。 | 能说明新增评分器与组级评分怎样接入。 | [tests/plugin_contracts/test_plugin_path_loading_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_path_loading_contracts.py#L1) |
| 14 · 样本处理与 hook | [slime/rollout/sample_hooks.py · apply_rollout_sample_hooks](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sample_hooks.py#L52)<br>[slime/rollout/sample_hooks.py · _apply_to_sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sample_hooks.py#L37) | 读 sync/async、Sample/None、嵌套形状和 rollout_id 上下文；批次过滤的确认过程后置。 | 能指出错误返回、样本扇出与身份保持需要哪些断言。 | [tests/test_rollout_sample_hooks.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_rollout_sample_hooks.py#L1) |
| 15 · 评测配置与实际消费 | [slime/utils/eval_config.py · EvalDatasetConfig](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/eval_config.py#L135)<br>[slime/utils/eval_config.py · build_eval_dataset_configs](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/eval_config.py#L265)<br>[slime/rollout/sglang_rollout.py · eval_rollout_single_dataset](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L616) | 配置后立即对照 runner：样本注入、sampling 和 rewards/truncated/samples 返回合同。 | 当前默认 runner 未消费 eval_task_timeout、early-stop、app_service 字段；配置合并测试不能证明运行时能力生效。 | [tests/test_eval_config.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_eval_config.py#L1) |
| 16 · 另一种策略：Multi-Agent | [examples/multi_agent/rollout_with_multi_agents.py · generate_with_multi_agents](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/multi_agent/rollout_with_multi_agents.py#L16)<br>[examples/multi_agent/agent_system.py · run_agent_system](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/multi_agent/agent_system.py#L198) | 画 solver → rewriter → selector 和早退，定位 _emit 如何统一兄弟样本 rollout_id。 | 对照 Coding Agent，确认通用接入合同；prompt、模型生成与奖励缩放细节第二遍再读。 | [tests/plugin_contracts/test_plugin_generate_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_generate_contracts.py#L1) |

### 04 Trace、验证与复现

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 17 · Trace 与真实埋点位置 | [slime/observability/trace_utils.py · bind_trace](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L238)<br>[slime/observability/trace_utils.py · trace_span](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L345)<br>[slime/observability/trace_utils.py · trace_function](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L451) | 先看身份、父子 span、耗时和错误，再回 sglang_rollout 的真实调用点；此步的思想也用于 02–16 的测试。 | 第二遍看 export/import 与重试关联；Coding Agent/CLI/环境/评分的端到端传播仍需补覆盖和验证。 | [tests/observability/test_trace_utils.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/observability/test_trace_utils.py#L1) |
| 18 · 结果分析与实验复现 | [tools/trace_timeline_viewer.py · _build_items_from_trace](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tools/trace_timeline_viewer.py#L245)<br>[tools/trace_timeline_viewer.py · _build_cache_data](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tools/trace_timeline_viewer.py#L572)<br>[tools/trace_timeline_viewer.py · main](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tools/trace_timeline_viewer.py#L2359)<br>[slime/observability/metric_utils.py · compute_pass_rate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/metric_utils.py#L14)<br>[docs/zh/advanced/reproducibility.md](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/docs/zh/advanced/reproducibility.md#L1) | 只读 Trace 到离线时间线的输入/缓存/入口，以及 pass@k 的分组假设；不通读 Viewer。 | 保存代码/模型/tokenizer/数据/采样/依赖/资源配置；固定 seed 不保证所有实现行为完全一致。 | [tests/observability/test_trace_utils.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/observability/test_trace_utils.py#L1) |

### 05 并发、队列与恢复

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 19 · 并发上限与请求节奏 | [slime/rollout/sglang_rollout.py · GenerateState.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L89)<br>[slime/utils/async_utils.py · AsyncPacer](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/async_utils.py#L8)<br>[slime/rollout/sglang_rollout.py · generate_rollout_async](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L476) | 先辨认 semaphore、pacer 和 FIRST_COMPLETED 收集/补任务；abort 与过滤分支第二遍追。 | 说明并发上限、启动节奏、线程事件循环和任务取消的不同职责。 | [tests/test_fully_async_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_fully_async_rollout.py#L1) |
| 20 · 持续生成：先看分支，再读本地池 | [slime/rollout/fully_async_rollout.py · _get_worker](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_rollout.py#L54)<br>[slime/rollout/fully_async_rollout.py · AsyncRolloutWorker._loop](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_rollout.py#L173)<br>[slime/rollout/fully_async_rollout.py · AsyncRolloutWorker.pause](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_rollout.py#L109) | 看本地 worker 的 active pool、完成队列、ABORTED 重入与暂停；reader_config 分支接下一步。 | 本地输出 queue 无界，背压由补任务条件承担；不能写成有界输出队列。 | [tests/test_fully_async_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_fully_async_rollout.py#L1) |
| 21 · 持久化模式：分布式生成池 | [slime/rollout/fully_async_distributed.py · DistributedRollout.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L474)<br>[slime/rollout/fully_async_distributed.py · RolloutScheduler._run](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L98)<br>[slime/rollout/fully_async_distributed.py · RolloutScheduler.generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L161)<br>[slime/rollout/fully_async_distributed.py · _GenerationActor._produce](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L319) | 从 _get_worker 的 reader_config 分支进入，辨认每节点 worker、局部 pool、输出队列与全局 demand/prefetch。 | 第二遍追 pause、worker 失败与结果恢复；只读本地 AsyncRolloutWorker 不覆盖这条主链。 | [tests/test_distributed_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_distributed_rollout.py#L1) |
| 22 · 任务租约、结果引用与确认 | [slime/data/queue_data_source.py · QueueReader.get_samples](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L1068)<br>[slime/data/queue_data_source.py · RolloutQueueController.take](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L488)<br>[slime/data/queue_data_source.py · RolloutQueueController.complete](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L563)<br>[slime/data/transport.py · pack_rollout_group](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/transport.py#L259)<br>[slime/data/transport.py · accept_raw_rollout](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/transport.py#L431) | 只追 task → lease → result_ref → receipt → accepted；QueueDataSource 主要是 reader/checkpoint 包装。 | 第二遍再读 heartbeat/add_samples、ready_batch/finish_batch 与 save/load；外部 straw/WAL 保证另行核对。 | [tests/test_distributed_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_distributed_rollout.py#L1)<br>[tests/test_straw_fully_async_recovery.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_straw_fully_async_recovery.py#L1) |

### 06 服务、资源与部署

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 23 · 服务和资源的真正拥有者 | [slime/ray/placement_group.py · create_placement_groups](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/placement_group.py#L123)<br>[slime/ray/serving.py · ServingCluster.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L38)<br>[slime/backends/sglang_utils/deployment.py · start_rollout_servers](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/deployment.py#L79)<br>[slime/backends/sglang_utils/external.py · discover_external_engines](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/external.py#L95) | 画 PG、router、Ray engine actor 和 HTTP 模型进程的运行位置，定位它们的创建者。 | 当前服务所有者在 ray/serving.py；第二遍读 engine_group/sglang_engine 与容器；Kubernetes 并行实践。 | [tests/test_placement_group.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_placement_group.py#L1)<br>[tests/test_external_sglang_engines.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_external_sglang_engines.py#L1) |
| 24 · 健康、恢复与退出策略 | [slime/ray/serving.py · ServingCluster.finish_rollout](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L280)<br>[slime/ray/serving.py · ServingCluster.recover_updatable_engines](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L256)<br>[slime/ray/serving.py · ServingCluster.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L294)<br>[slime/ray/rollout.py · RolloutManager.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L160)<br>[slime/utils/health_monitor.py · RolloutHealthMonitor.check_once](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/health_monitor.py#L126)<br>[slime/utils/cleanup.py · Cleanup](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/cleanup.py#L9) | 区分 rollout 结束、故障引擎退役、更新前恢复、训练失败保留 serving 和成功完整回收。 | RolloutManager 只清理自己拥有的资源；第二遍沿 health checks、engine recover/shutdown；部分测试启动 CPU Ray。 | [tests/test_rollout_manager_recovery.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_rollout_manager_recovery.py#L1) |

### 07 训练交接

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 25 · 生成数据怎样进入训练 | [train.py · main](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L103)<br>[train.py · train](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L13)<br>[slime/data/batch_builder.py · BatchBuilder.convert](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/batch_builder.py#L237)<br>[slime/backends/megatron_utils/actor.py · MegatronTrainRayActor._get_rollout_data](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L222)<br>[slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.train_actor](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L449) | 只追 tokens/mask/reward/rollout_log_probs 到 advantage 与 train；主循环第一遍可在全局地图中先扫角色。 | 第二遍选 compute_advantages_and_returns、policy_loss_function 或 sft_loss_function；不从 loss.py 开头逐行读。 | [tests/test_process_rollout_data.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_process_rollout_data.py#L1)<br>[tests/test_policy_loss.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_policy_loss.py#L1) |
| 26 · 数据完成、共同 checkpoint 与权重发布 | [slime/data/batch_builder.py · BatchBuilder.training_completed](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/batch_builder.py#L144)<br>[slime/data/checkpoint.py · save_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L39)<br>[slime/data/checkpoint.py · commit_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L77)<br>[slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.update_weights](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L628)<br>[slime/backends/megatron_utils/update_weight/__init__.py · create_weight_updater](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/update_weight/__init__.py#L10) | 接回 train 的 admission pause/update/resume，区分 accepted、training completed、checkpoint committed 与模型版本。 | 第二遍只按实际配置选一种权重 updater 与恢复路径；数值校正、全部传输后端和训练并行后置。 | [tests/test_rollout_straw_transport.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_rollout_straw_transport.py#L1)<br>[tests/test_megatron_checkpoint.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_megatron_checkpoint.py#L1)<br>[tests/test_update_weight_factory.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_update_weight_factory.py#L1) |

### 实现对照与后置范围

首条 CLI/协议链读通后，比较 ClaudeCodeHarness 的 write_config/launch_and_wait 与 AnthropicAdapter 的路由/_translate/_respond；共享处理与轨迹流程不用重读。

Search-R1、Tau-bench 和独立 Rollout Buffer 作为策略/环境/服务对照；模型结构、MLA、量化内核、NPU/GB10、全部 Megatron 并行实现和所有权重传输后端按实际需求后置。Kubernetes、外部 CLI 工具循环、端到端 Trace 和吞吐/恢复/训练实验需要独立实践，不能只靠阅读数量证明。

当前证据：文件、符号、行号与本地 Git blob 已静态核对；配套测试在本轮只作为阅读材料，未执行源码仓库的测试、模型服务、Ray、训练或 Kubernetes。

## 仓库覆盖与缺口

这里记录计划覆盖范围。源码入口经过静态核对，00 的职责地图与 01 的完整任务主线有展开讲解；01 也串联 02 的请求与轨迹职责，仍不表示所有分支或用户掌握状态已确认。

| 领域 | 主要代码/材料 | 对应单元 | 预期覆盖 | 后续或外部缺口 |
| --- | --- | --- | --- | --- |
| Agent 组件 | `slime/agent/`、`examples/coding_agent_rl/` | 01、02 | 启动、模型协议、环境、上下文、轨迹、任务与评分 | CLI 内部工具循环、任意外部模型客户端 |
| 策略与评测 | `slime/rollout/`、`utils/eval_config.py`、多轮示例 | 03 | custom generate、RM、hook、过滤、数据集、结果合同 | 其他环境/策略按问题选读；不是所有示例已审计 |
| Trace、测试与复现 | `slime/observability/`、`tools/`、`tests/`、CI 与复现文档 | 04 | Trace 合同、真实埋点覆盖检查、日志、指标、回放、契约与 fake 测试 | 端到端埋点、GPU/模型/集群实测与实验管理实践 |
| 数据、并发与恢复 | `slime/data/`、`fully_async_rollout.py`、`utils/cleanup.py` | 05、07 | 缓冲、队列、传输、取消、背压、恢复与共同 checkpoint | straw-queue、共享存储等外部实现和故障实验 |
| 模型服务与调度 | `backends/sglang_utils/`、`slime/ray/serving.py`、`slime/ray/rollout.py`、`utils/health_monitor.py` | 06、07 | 部署、发现、资源布局、健康、服务所有权与权重更新 | SGLang 服务内部、所有部署拓扑与容量调优 |
| 容器与 Kubernetes | `docker/`、`scripts/`、Sandbox 合同 | 06 + 独立实践 | 定位构建依赖，定义环境操作和集群适配边界 | 本版本未定位到原生 Kubernetes 沙箱后端或集群 controller；需实际集群经验 |
| 训练与算法 | `train.py`、`backends/megatron_utils/`、SFT/校正示例 | 07 | 数据消费、基本 SFT/RL、策略版本、checkpoint 与权重发布 | 并行训练细节、全部算法推导和数值实验 |
| 独立 Rollout Buffer 与其他插件 | `slime_plugins/rollout_buffer/`、模型插件 | 05 对照；其余后置 | 区分独立 HTTP buffer、TrajectoryManager、主链数据队列 | 模型结构/算子/平台插件的具体实现 |
| 项目维护与跨语言 | README、`docs/`、`.github/`、`scripts/`、`docker/` | 00 定位，04/06 按需 | 配置、测试入口、启动与发布材料职责 | TypeScript/Rust/Go 协作与 AI 工具经验需独立项目材料 |

这条路线支持理解需求到接口、数据、验证和运行边界的映射。实际部署、算法协作、性能治理和 owner 经验还需要任务实践与可观察结果，不能由阅读文件数量代替。

## 第 0 章 全局职责与三种运行粒度

**目录 ID：** `00-overview`
**产物状态：** ready
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 一次任务、一次模型请求和一次训练迭代，分别由哪些模块组织？

**前置：** 无；从这里开始。

**图文对照：** 1.1、4、7.1。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 训练与生成总入口 | [train.py · main](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L103) | locate | 只定位启动、资源准备和训练循环；训练算法留到 07。 |
| 任务数据合同 | [slime/utils/types.py · Sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/types.py#L107) | locate | 先辨认 prompt、reward、token、mask、状态和身份字段；字段转换在 02、03、07 展开。 |
| 分布式生成与评测入口 | [slime/ray/rollout.py · RolloutManager](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L36) | locate | 类的角色与 generate/eval 入口；资源治理留到 06。 |
| 一个代码任务的组装 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | locate | 只读调用骨架；执行和清理在 01 展开。 |

**章内顺序：**

1. 从本章 walkthrough 的基本工作流建立最小整体模型，先分清任务数据、生成评分、样本批次、训练和权重返回。
2. 以“谁启动并进入循环”为第一个展开问题，沿 train.main() 的真实交接定位服务准备与 train()；每步保留整体轮廓，第一遍不钻损失公式。
3. 到生成数据的交接再看 Sample 的主要字段；区分任务、请求和训练样本，具体字段按问题展开。
4. 主线进入具体 Agent 任务时，再定位 generate() 的 prepare → Harness → diff → evaluation → finish_session → finally；已读部分短提醒后返回调用方。

**验收问题：** 解释 agent/、rollout/、data/、ray/、backends/ 的职责，并指出工具循环、Kubernetes 和 tokenizer 实现的外部边界。

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 1 章 完整任务、Harness 与执行环境

**目录 ID：** `01-task-execution`
**产物状态：** ready
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 代码任务怎样启动 CLI、让 CLI 回连模型入口、收集补丁、独立评分并释放资源？

**前置：** 00；已知道任务、请求和训练的区别。

**图文对照：** 4.1 的动作 4、5、6、7；7.1。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 任务生命周期 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | trace | 分别追踪训练与 evaluation 分支；不是通用的独立任务平台。 |
| 调用方的模型入口准备 | [_AdapterService.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L138)（examples/coding_agent_rl/generate.py） | trace | 细读 tokenizer/解析配置、Adapter 内部状态、HTTP 线程、监听/回连地址和进程复用；返回调用方继续任务、Session、环境和题目准备。 |
| 启动骨架 | [slime/agent/harness/common.py · BaseHarness.run](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L81) | trace | 配置和 CLI 启动可替换；CLI 内部工具循环在外部软件包。 |
| 沙箱操作合同 | [slime/agent/sandbox.py · Sandbox](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L28) | trace | 当前实现为 E2B；Kubernetes 后端需独立实现和验证操作语义。 |
| 长命令等待 | [slime/agent/sandbox.py · exec_and_wait](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L82) | explain | 区分等待超时、进程退出和外层环境回收，不能假设返回超时就已杀死进程。 |
| 补丁的独立评估 | [examples/coding_agent_rl/swe.py · run_evaluation](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L239) | trace | 评分环境与 Agent 工作环境分开；继续定位 _grade_scaleswe/_grade_swebench。 |

**章内顺序：**

1. 先读 generate()，记录创建者、持有者、收集者和清理者。
2. 依次读 Harness.run、Sandbox 操作合同、exec_and_wait；再定位 Claude/Codex Harness 的模型地址和会话身份配置。
3. 补读 4.1 的动作 7 Make API Calls，接到 BaseAdapter._run_turn 的 HTTP 入口；模型处理留到 02。
4. 回到 swe.git_diff 和 run_evaluation，辨认工作环境退出后在新评估环境应用补丁并运行测试。
5. 沿超时、CLI 非零退出、空轨迹、评分失败和 finally 追踪结果与清理；用 tests/test_agent 中的 fake 测试理解可验证边界。

**验收问题：** 如果换 Agent CLI 或沙箱后端，分别修改哪层？CLI 的退出码为什么不等于任务 reward？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 2 章 模型协议、上下文与训练轨迹

**目录 ID：** `02-model-context`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** CLI 的模型请求如何进入共享流程，返回协议响应，并留下可用于训练的真实轨迹？

**前置：** 01；已连接 CLI 配置、HTTP 路由与任务会话。

**图文对照：** 4.1 的动作 2、3、3.5；补读会话结束。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 共享模型请求流程 | [slime/agent/adapters/common.py · BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L318) | trace | 协议转换、模板编码、模型生成、解析、响应与轨迹记录；具体协议见旁边 openai.py/anthropic.py。 |
| 实际模型调用 | [slime/agent/adapters/common.py · call_sglang_generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L442) | trace | 原生 SGLang /generate；协议兼容不表示已经支持任意云 API。 |
| 输出与工具解析 | [slime/agent/parsing.py · parse_model_output](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L25) | trace | 解析工具调用不等于执行工具；执行者是 CLI 或其他自定义 Agent。 |
| 会话轨迹与上下文分支 | [slime/agent/trajectory.py · TrajectoryManager](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L269) | trace | 第一遍看 record_turn/get_trajectory；token drift、分叉、mask 细节作为第二遍 explain 范围。 |
| 会话结束与训练样本导出 | [slime/agent/adapters/common.py · BaseAdapter.finish_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L245) | trace | 区分当前 HTTP 请求结束、会话关闭、Sample 导出和 cleanup-only drop_session。 |

**章内顺序：**

1. 取一份带工具的请求，沿 7 → 2 → 3 → 3.5 画输入输出。
2. 分别定位 OpenAI/Anthropic 路由、_translate、_respond；确认实际生成端是 SGLang。
3. 从 TurnRecord 到 record_turn，再到 finish_session/get_trajectory，核对 token、logprob、mask 与 reward 的来源。
4. 第二遍只选择一种上下文变化：追加工具结果、上下文压缩或分支；用 test_trajectory_manager_branching 理解行为。

**已确认的第二遍细分（2026-10-11）：** `generate()`／`_run_turn()` 主线之后，进入 [Trajectory Management 专题阅读入口](<../4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/Trajectory Management/README.md>)。每轮只展开一个机制：① `record_turn()` 的历史接续与分叉；② `_try_merge_assistant_rewrite()` 的改写合并；③ `get_trajectory()` 的 token 对齐、共享前缀去重和 Sample 导出。入口已建立，不表示用户已完成这些阅读单元。

**验收问题：** 一轮协议响应和一份训练 Sample 有什么关系？为什么仅保存最终文本无法还原生成时的全部训练信息？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 3 章 策略接入、数据生成与评测合同

**目录 ID：** `03-strategy-evaluation`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 新增 Agent 策略、评分器、数据集或样本处理逻辑时，应该接在哪个扩展点？

**前置：** 00–02；知道 Sample 与一次任务的返回边界。

**图文对照：** 4.5、3.4、3.3、3.2、3.1；7.5/7.6/7.10 作为对照。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 单样本生成与评分组合 | [slime/rollout/sglang_rollout.py · generate_and_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L289) | trace | custom generate、异步等待、样本 hook 和 group_rm 分支；自定义函数可能扇出多个 Sample。 |
| 整批 rollout 返回合同 | [slime/rollout/base_types.py · call_rollout_fn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/base_types.py#L28) | trace | 训练/评估输出不同；本版本支持数据引用，不能只记成 Python Sample 列表。 |
| 可替换评分器 | [slime/rollout/rm_hub/__init__.py · async_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/rm_hub/__init__.py#L55) | trace | 按样本、全局路径或远端评分分发；分组评分另看 batched_async_rm。 |
| 评测数据与参数 | [slime/utils/eval_config.py · EvalDatasetConfig](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/eval_config.py#L135) | trace | 先核对 eval_rollout_single_dataset 实际消费字段和结果合同；类中 timeout/early-stop/app_service 字段不能直接当作默认 runner 已实现的行为。 |
| 样本处理扩展点 | [slime/rollout/sample_hooks.py · apply_rollout_sample_hooks](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sample_hooks.py#L52) | trace | 同步/异步 hook 与样本身份传递；动态过滤和批次 hook 有不同位置。 |

**章内顺序：**

1. 标出 --custom-generate-function-path、--custom-rm-path、--data-source-path 和 --rollout-function-path 的不同作用范围。
2. 追踪 generate_and_rm 的生成、Sample 上下文继承、hook、奖励和返回；看 generate_and_rm_group 的组级处理。
3. 读 EvalDatasetConfig 与 eval_rollout_single_dataset，画一次固定数据集评测的结果合同。
4. 选 Search-R1 或 multi_agent 的入口，与 Coding Agent 对照如何替换单样本生成；Tau-bench 作为后续环境适配例子。
5. 读 tests/plugin_contracts 与 test_rollout_sample_hooks，列出新策略需要维持的输入、输出、身份和错误约定。

**验收问题：** 新增搜索工具策略和新增评分方法分别改哪里？什么时候需要替换整个 rollout？过滤样本后身份与完成确认由谁处理？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 4 章 Trace、结果分析、测试与复现

**目录 ID：** `04-trace-validation`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 怎样把模型、工具、环境和评分的失败或延迟关联起来，并用测试与配置验证修改？

**前置：** 01–03；已能指出执行与评测的关键交接。

**图文对照：** 9、8.2、3.5；源码 tests/ 和复现文档。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 事件与 span 的组织 | [slime/observability/trace_utils.py · trace_span](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L345) | trace | 自定义格式与跨边界 carrier；工具存在不表示所有示例已接好完整埋点。 |
| 实验日志与配置 | [slime/observability/logging_utils.py · configure_logger](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/logging_utils.py#L12) | locate | 继续读 init_tracking/finish_tracking；日志、指标与任务 Trace 分别定位。 |
| 正确率与结果统计 | [slime/observability/metric_utils.py · compute_pass_rate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/metric_utils.py#L14) | trace | 按题目分组和评分假设影响 pass@k 的解释。 |
| 轨迹时间线查看器 | [tools/trace_timeline_viewer.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tools/trace_timeline_viewer.py#L1) | locate | 输入适配、span 展示、离线分析；不当作现成的全链路在线监控。 |
| 扩展接口行为测试 | [tests/plugin_contracts/test_plugin_generate_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_generate_contracts.py#L1) | locate | 先读 fixture 与断言；测试未经本轮执行，不标为通过。 |

**章内顺序：**

1. 从 trace_span/trace_event 到 export_trace/import_trace，画父子 span 与跨进程关联。
2. 取一个评分失败或模型请求变慢的情景，决定应该记录的身份、阶段、尝试次数、耗时和错误。
3. 选 test_adapters、test_sandbox_exec_and_wait、test_eval_config 和 plugin_contracts，说明它们实际验证什么。
4. 读 docs/zh/advanced/reproducibility.md，记录代码 SHA、模型/tokenizer、数据集、采样、依赖和资源配置；固定随机种子不等于所有后端完全一致。
5. 第二遍再实践一项 fake 驱动的失败注入；需要模型或集群的验证另行准备环境。

**验收问题：** 一次任务失败，日志、Trace、样本状态和评分结果各回答什么？复现实验需要保存哪些配置与产物？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 5 章 并发、任务数据、背压与恢复

**目录 ID：** `05-concurrency-recovery`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 怎样持续处理慢任务、控制积压，并在取消、重启和部分失败后保持结果与任务身份一致？

**前置：** 03、04；知道组级输出合同与验证方式。

**图文对照：** 7.7、4.5、4.6；6.2 为独立服务对照。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 持续运行的生成工作者 | [slime/rollout/fully_async_rollout.py · AsyncRolloutWorker](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_rollout.py#L78) | explain | 本地池的任务、完成队列与暂停；先读 _get_worker 分支，持久化 reader_config 模式还需 DistributedRollout。 |
| 批次生成与取消 | [slime/rollout/sglang_rollout.py · generate_rollout_async](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L476) | trace | 区分线程中的事件循环、进程/Ray 调度和服务端生成请求的取消。 |
| 持久化分布式生成 | [slime/rollout/fully_async_distributed.py · DistributedRollout.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L474) | trace | 从 _get_worker 的 reader_config 分支进入；每节点 worker、局部池、全局 demand/prefetch 与 worker 恢复。 |
| 任务领取与确认 | [slime/data/queue_data_source.py · QueueReader.get_samples](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L1068)、[slime/data/queue_data_source.py · RolloutQueueController.take](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L488)、[slime/data/queue_data_source.py · RolloutQueueController.complete](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L563) | trace | task、lease、result_ref 与 receipt；结果 accepted、训练 completed、checkpoint committed 分开理解。 |
| 任务数据源 | [slime/data/queue_data_source.py · QueueDataSource](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L1292) | trace | 这是 job-level reader/checkpoint 包装；具体租约与确认在 QueueReader/RolloutQueueController，外部 straw 语义另行核对。 |
| 结果打包与共享存储 | [slime/data/transport.py · pack_rollout_payload](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/transport.py#L350) | trace | Ray object-store 与 straw 数据引用两种路径；完成确认、接受批次和持久化 checkpoint 不等价。 |
| 共同清理预算 | [slime/utils/cleanup.py · Cleanup](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/cleanup.py#L9) | explain | 每项清理使用剩余时间；清理工具不是通用强制中断器。 |
| 恢复计划 | [slime/data/checkpoint.py · resolve_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L237) | locate | 先辨认数据进度与模型/优化器状态的共同恢复边界，再看恢复实现。 |

**章内顺序：**

1. 先看 GenerateState.semaphore、generation_pacer 与 _get_worker；再比较本地 AsyncRolloutWorker 和持久化 DistributedRollout 两条任务池，解释并发上限、启动节奏和各自的队列背压。
2. 追一个正常组、一个 ABORTED 组和一个超时请求；记录排队、重入、结果接受和资源释放。
3. 对照 data_source.py、QueueReader、RolloutQueueController 与 transport.py；区分 prompt buffer、租约、持久化结果、批次接受和训练消费确认。
4. 读 tests/test_fully_async_rollout.py 和恢复测试，提出慢任务、满队列、取消、服务重启与重复结果的行为验证。
5. 第二遍对照 slime_plugins/rollout_buffer/README.md：它是独立 HTTP Rollout Buffer 服务，不能与 trajectory.py 或主链数据队列混为一谈。

**验收问题：** 暂停生成和取消请求有什么区别？任务完成、结果已收集、训练已消费和 checkpoint 已提交有哪些不同？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 6 章 模型服务、Ray 资源与容器边界

**目录 ID：** `06-serving-resources`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 谁部署模型、分配资源、发现服务、检查健康、处理故障，并回收任务与推理资源？

**前置：** 01、05；知道执行环境与并发预算的边界。

**图文对照：** 4.3、4.4、2.1；Kubernetes 为独立实践。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 分布式资源布局 | [slime/ray/placement_group.py · create_placement_groups](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/placement_group.py#L123) | trace | Ray placement group 与 GPU 布局；不是 Kubernetes Pod 或集群调度器。 |
| 推理部署组装 | [slime/backends/sglang_utils/deployment.py · start_rollout_servers](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/deployment.py#L79) | trace | 配置、router、engine group 和服务进程；模型内部算子后置。 |
| 外部模型服务发现 | [slime/backends/sglang_utils/external.py · discover_external_engines](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/external.py#L95) | trace | 外部 SGLang 引擎信息与控制接口，不等同于任意 Chat Completions API。 |
| 模型服务所有权 | [slime/ray/serving.py · ServingCluster.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L38)、[slime/ray/serving.py · ServingCluster.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L294) | trace | 服务与队列可以跨训练尝试保留；失败、detach、正常成功退出的政策不同。 |
| 生成服务管理与清理 | [slime/ray/rollout.py · RolloutManager.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L160) | trace | 借用 ray/serving.py 中 ServingCluster 的模型服务，dispose 只清理自有资源；服务完整回收另由所有者负责。 |
| 容器构建参考 | [docker/Dockerfile](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/docker/Dockerfile#L1) | locate | 镜像、依赖与补丁；集群控制器、沙箱后端和网络存储仍需独立实践。 |

**章内顺序：**

1. 画运行位置：训练 actor、rollout worker、模型 HTTP 服务、Adapter、Agent CLI 与沙箱。
2. 追 placement group → deployment → engine/router → health/recovery → dispose 的职责交接。
3. 选择一个模型服务不可达或 CLI 无法回连 Adapter 的情景，定位地址、端口、会话、日志与清理者。
4. 另做 Kubernetes 实践：Pod 创建/就绪、资源限制、命令与文件操作、网络回连、日志与结果保存、取消和清理；该任务只是建议，尚未执行。

**验收问题：** Ray、Kubernetes、Sandbox 和模型服务各管理什么？要换 Kubernetes 沙箱，需要满足哪些操作与失败语义？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 7 章 训练交接、策略版本与权重更新

**目录 ID：** `07-training-handoff`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 生成的轨迹怎样被训练消费，更新后的模型怎样继续服务下一轮任务，如何保留一致性？

**前置：** 02、03、05、06；了解 Sample、结果传输与模型服务。

**图文对照：** 4.2、5.1、7.8；7.9 与 SFT 作为第二遍。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 生成、训练、保存与更新主循环 | [train.py · train](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L13) | trace | 第一遍读职责与顺序；Megatron 张量并行和全部算法推导后置。 |
| 模型训练消费 | [slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.train_actor](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L449) | trace | 定位 reward、advantage、logprob、mask 的消费；不能假设所有字段在生成阶段已经算好。 |
| 权重发布 | [slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.update_weights](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L628) | trace | 暂停/版本/内存或磁盘更新；与 GPU/模型服务生命周期共同理解。 |
| 共同 checkpoint | [slime/data/checkpoint.py · save_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L39) | trace | 模型/优化器状态与数据进度共同恢复；仅完成一次训练不等于可恢复 checkpoint。 |
| SFT 样本生成 | [slime/rollout/sft_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sft_rollout.py#L1) | locate | 审核后的轨迹可重新编码用于 SFT；需要概率信息的 RL 不能只用最终文本补齐。 |

**章内顺序：**

1. 画 train() 的生成 → 训练 → 数据完成确认 → checkpoint → 暂停与权重更新 → 继续生成。
2. 从 Sample 跟到 actor 的数据读取与 train_actor，说明 tokens、loss_mask、reward、rollout_log_probs 与 advantage 的用途和产生位置。
3. 追一个策略版本跨越生成与训练的情景，分清异步旧策略数据和 SGLang/Megatron 数值不一致两类问题。
4. 第二遍按具体算法读 loss.py 与 examples/train_infer_mismatch_helper/；权重传输细节再读 update_weight/ 与 delta-weight-sync 文档。

**验收问题：** 更换 Agent 策略为什么可能影响训练数据合同？哪些数据必须在生成时保留？异步生成与训练更新如何协调？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。
