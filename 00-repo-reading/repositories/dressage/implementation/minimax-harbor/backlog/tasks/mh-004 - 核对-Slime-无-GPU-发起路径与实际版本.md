---
id: MH-004
title: 核对 Slime 无 GPU 发起路径与实际版本
status: Done
assignee:
  - '@codex'
created_date: '2026-11-17 06:51'
updated_date: '2026-11-17 12:54'
labels:
  - phase-1
  - migrated
dependencies: []
documentation:
  - backlog/docs/doc-003 - 接口调查与待确认事项.md
  - backlog/docs/doc-002 - 总体路线与验收边界.md
  - backlog/docs/doc-001 - 迁移前原文快照.md
  - backlog/decisions/decision-001 - 先完成无-GPU-API-评测链路，再接-Agent-Sandbox.md
type: spike
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
原 Q03。此前独立 Slime 18868a79 的 train.py 在 eval-only 判断前涉及训练模型与权重同步；Dressage gitlink 实际是 aaf5c209 且当时尚未初始化。因此旧观察不能直接外推。需要核对实际选用版本与无 GPU 发起路径，不能随意下载模型凑齐初始化。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 明确采用的 Slime 路径和提交，以及它与 Dressage 固定子模块和旧阅读版本的关系。
- [x] #2 在实际版本定位启动至 rollout 发起/接回的路径，列清训练模型、SGLang 与 GPU 的初始化触发条件。
- [x] #3 给出无 GPU 的最小发起方案和验证命令；若现有配置不能满足，指出最小适配边界及阻碍，不把方案记成已跑通。
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. 取得 Dressage 固定 gitlink aaf5c209 的 Slime 源码，和旧阅读版本分开。2. 沿入口定位模型/GPU 初始化、rollout 委派及训练结果校验，核对现有 eval/debug 配置能否无 GPU 运行。3. 给出已验证的最小发起办法或明确最小适配边界，并记录可执行检查与未实跑部分。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-17 任务审计：git -C third_party/dressage submodule status 显示 -aaf5c2092b01219fa0d5c2d323741d409086ca32 slime，当前固定 Slime 尚未初始化。没有完成该版本启动路径调查或无 GPU 发起验证，继续保持 To Do，不因 MiniMax adapter 测试通过而勾选验收项。MH-007 的独立 Harbor Trial 不依赖本任务；本任务仍是最终从 Slime 发起目标的独立待办。

2026-11-17 用户指定检查第3项：固定 Slime 无 GPU 发起路径，调查完成，尚未实现 Slime API-only 启动。

版本：集成仓库 HEAD=43333649561c19acdd3c6cc85a8d33fefe708895；Dressage=3820149ebfc0536b213ec120b43ec090f09b3fcd；其 gitlink slime=aaf5c2092b01219fa0d5c2d323741d409086ca32。嵌套子模块未初始化，但独立 /home/hongshi/projects/slime 已含这个 commit 对象。用 git archive 导出至 /tmp/slime-aaf5c209-04e_mn9u，未变更任何 checkout/pin。独立阅读仓库 HEAD 仍为 18868a79b0b083a093798a94ed0f8cb4f71b9c14，本次结论均据 aaf5c209。

实际调用与边界：
1. train.py:9 的 train → create_placement_groups(:14) → create_rollout_manager(:19) → create_training_models(:21) → update_weights(:27)，之后才到 eval-only 判断(:36)。因此 num_rollout=0 不等于绕开训练/推理初始化。正常 generate 返回后仍进入训练循环。
2. slime/ray/placement_group.py:100 的 _get_placement_group_layout 确有 rollout_external + debug_rollout_only → (0,0) 分支；不能声称所有模式必需本地 GPU。仅 debug_rollout_only 则保留 rollout GPU。CPU 隔离执行这个真实函数的三组结果：普通(48,16)、仅debug(32,0)、external+debug(0,0)，数值为该测试输入下的资源布局，不是端到端成功。
3. slime/utils/arguments.py:1548 parse_args 仍解析 SGLang/导入 Megatron 参数模块；:1851 外部引擎探测经 slime/backends/sglang_utils/external.py:58 请求 /server_info 或 /get_server_info。这个地址参数指 SGLang 引擎，不能直接替换成 MiniMax /v1 地址。RolloutManager.__init__ 在 slime/ray/rollout.py:426 起调用 start_rollout_servers(:1091)，并加载 data_source/rollout/eval 函数；不是只换 rollout_function_path 就能跳过服务器初始化。debug_train_only 跳过推理但 eval(:567)直接返回；它与debug_rollout_only还互斥。
4. 训练侧 RayTrainGroup.create → _allocate_gpus_for_actor 仍引用 Megatron actor；create_training_models 要求 start_rollout_ids 集合长度为1。把actor数量硬设0不能直接当作支持的纯评测方案。依赖装齐也不自动解决运行合同。
5. Dressage integrations/harbor/rollout.py:1026 _run_harbor_rollout 在 evaluation 分支之前要求 execution_mode=training，再校验奖励/转换hook(:252)、Proxy能力(:197)。_bundle_samples(:623)拒绝非trainable bundle；:1177还拒绝无trainable group。这与 MiniMax 消息路线明确 trainable=false、不伪造 token/logprob 的合同不符。隔离执行该函数真实前两条语句，evaluation=True + execution_mode=rollout 实际得到 requires HarborDataSource in training mode。此探针只验证入口guard，不表示执行完整Harbor函数。

运行证据：.venv-harbor 当前 torch/megatron/sglang/slime 均未安装；实际执行 .venv-harbor/bin/python /tmp/slime-aaf5c209-04e_mn9u/train.py --help，在 slime/ray/utils.py:5 导入 torch 时失败 ModuleNotFoundError。未为了通过预检安装训练栈、下载模型或伪造GPU/训练数据。该报错是本机依赖边界；上述源码条件是独立的逻辑边界。

最小适配方向（尚未实施）：
- 启动侧：若坚持“Slime发起”，需要显式 API-only evaluation 入口/模式，在GPU placement、训练actor、SGLang启动之前分流；尽量复用 Slime 的 rollout调用/评测结果接口，而不是模拟SGLang服务器。
- 执行侧：复用已验证 Harbor Job + DressageHarborPlugin 的任务/工具/Verifier/清理生命周期，不新造任务runner。纯评测的结果映射应从 JobResult/bundle 的实际reward、失败及轨迹引用形成评测结果，不经过必须trainable的 _bundle_samples，不生成虚假token/logprob/weight version。现有严格训练入口不放宽。
- 验收：无GPU/本地模型/训练栈时，从新增明确入口完成同一小任务；证明调用现有Harbor生命周期、结果可关联、失败清理有效；同时防止API-only结果进入训练。当前可执行方案仍是 USAGE.md 的独立 harbor run --plugin dressage，不能称为Slime已经接入。

源码复核命令：git -C /home/hongshi/projects/slime show aaf5c209:train.py；git -C /home/hongshi/projects/slime show aaf5c209:slime/ray/placement_group.py；git -C /home/hongshi/projects/slime show aaf5c209:slime/backends/sglang_utils/external.py。完整启动验证尚未通过；本 spike 的完成仅代表版本、启动条件与最小改动边界已核对。实际实现属于后续工作，未自动新建/开启任务。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
已核对 Dressage 固定 Slime aaf5c209，确认外部SGLang+debug存在零GPU资源分支，但现有训练启动与Harbor训练结果合同不能直接承接MiniMax非训练结果。记录真实依赖报错、源码条件与最小API-only评测适配边界；三个调查验收项完成。Slime实际发起尚未实现或验收，独立Harbor基线不等于Slime接通。
<!-- SECTION:FINAL_SUMMARY:END -->
