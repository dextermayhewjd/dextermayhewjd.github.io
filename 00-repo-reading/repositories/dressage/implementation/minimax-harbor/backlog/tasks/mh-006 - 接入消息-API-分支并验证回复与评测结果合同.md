---
id: MH-006
title: 接入消息 API 分支并验证回复与评测结果合同
status: Done
assignee:
  - '@codex'
created_date: '2026-11-17 10:53'
updated_date: '2026-11-17 11:34'
labels: []
dependencies:
  - MH-005
type: feature
ordinal: 6000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 真实 Dressage 校验对训练基线、缺字段与显式无 token 评测记录有可重复结果
- [x] #2 同一 create_app 中 API 分支支持 JSON/SSE、身份与 hooks，并跳过 tokenizer/SGLang 初始化
- [x] #3 ProxyClient→finalize/read→HarborArtifactStore 提交通过；训练模式拒绝无 token 记录
- [x] #4 失败、取消、资源关闭及既有 SGLang 路径回归通过；文档含启动配置与边界
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Spec: doc-004。1. tests/test_dressage_result_contract.py 验证真实 validate_attempt，先固定缺字段失败及空数组在评测模式的明确语义。2. src/agent_api_integration/dressage_bridge.py 映射请求及完整回复；third_party/dressage 的 fork 增加 create_app(message_backend=...)、消息 StepRecord/segment 与 JSON/SSE 分支，保留既有 SessionManager/TrajectoryStore/HarborArtifactStore。3. tests/test_dressage_bridge.py 用真实 create_app、ProxyClient、ArtifactStore 和 MockTransport 验证多轮、身份、最终保存、坏参数、缺失 usage、HTTP 错误、取消、训练拒绝及关闭。4. 增加可运行 CLI/配置说明；运行完整集成仓库测试与受影响 Dressage 测试；必要 fork 补丁单独提交，更新 submodule pin；不运行付费 API 或宣称真实 Harbor/Slime 训练可用。风险检查：消息附加字段丢失、usage 伪造、并发串话、取消后误记成功、误把评测结果声明可训练。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-17 实际验证与接入：
- B1：真实 validate_attempt 的 4 个测试，确认缺少 tokens/full_loss_mask/full_logprobs 仍被拒绝；明确的空数组 + 正确身份/完成标记 + require_trainable_tokens=False 接受为非训练评测记录，训练要求仍拒绝。
- B2/B3：新增 DressageBridge、固定 fork create_app(message_backend=...) 与 message_backend.py。分支在 tokenization 之前，复用 SessionManager/request_lock/hooks/finalize/TrajectoryStore；真实 ProxyClient 和 HarborArtifactStore 完成模拟 HTTP 两轮回复、finalize/read/commit、重复提交、磁盘保存与 manifest。reward 由最小 TrialResult fixture 提供，没有运行 Verifier。
- 自有测试 76 passed；固定上游 test_proxy_client.py + test_session_manager_cleanup.py 10 passed；原 token 路径另有最小生成/finalize/关闭回归（包含在 76 项中）。完整上游 test_proxy.py 因缺少 PyTorch 无法收集，不宣称全套 SGLang 回归完成。
- 实际启动 Uvicorn factory 并通过 localhost HTTP 读取 integration/capabilities，确认 messages 模式、trainable=false；随后正常停止。使用虚构凭据和 provider.invalid，未调用供应商。
- 新增 configs/harbor-api.json 并通过真实 HarborIntegrationConfig 校验；USAGE.md 给出安装、启动与配置交接。没有安装/运行 Harbor runtime、Agent CLI、真实 Gateway、Verifier、Agent Sandbox 或 Slime 发起端。
- 独立复核发现未映射生成控制参数静默丢失、hooks 审计丢失；新增 6 个失败测试后修复，完整套件通过。另修复 X-Dressage-Expected-Version 检查并测试。
- 决定：沿用明确空数组的现有评测校验语义，不伪造 IDs/logprobs/versions；保留 training guard，因此仍不能从 Slime 训练入口直接使用非训练 bundle。若误把本验证等同端到端训练，会跳过必要前置，文档已明确区分。
- 独立 fork 补丁提交 3820149ebfc0536b213ec120b43ec090f09b3fcd（feat/message-api-backend），上游基线 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。本轮不推送远端；适配仓库代码仍为本地改动。

2026-11-17 按用户可读性反馈整理 bridge：complete 保留请求合同→调用→回复映射三段，参数检查和 HTTP 异常转换移到文件下方辅助方法；行为不变，既有 76 项测试通过。说明保存在 doc-004 §8.4 和实施仓库 USAGE.md。

2026-11-17 用户要求本地明文配置且不上传 GitHub：启动 factory 使用 python-dotenv 读取当前工作目录 .env，已有环境变量优先，不向进程环境写入，不搜索父目录。创建无密钥 .env.example 和权限 600 的本地 .env；仅本机生成 Proxy 密钥，MiniMax 密钥留空待用户填入，未读取或输出真实密钥。git check-ignore 确认 .env 被忽略且未跟踪。新增两个配置测试先失败后通过，完整 78 项通过；测试隔离到临时目录，不读开发者 .env。未调用真实 API，未 push。

2026-11-17 真实 API 最小验证：用户填写本地 .env 后授权检查。配置字段齐全；.env 权限 600、被 Git 忽略且未跟踪。通过真实 create_api_app + ProxyClient（ASGI 内部 HTTP）→ DressageBridge → MiniMaxAdapter → api.minimax.cn 发出一次非流式请求，模型 MiniMax-M3，提示只回复 OK，输出上限 2048。真实返回 OK，finish_reason=stop，耗时 1.11s；供应商报告 prompt_tokens=204、completion_tokens=3、total_tokens=207。随后 finalize_session 成功（1 step），read_trajectory 读回 1 条 messages 记录，tokens/full_logprobs/full_loss_mask 均为空。没有输出或保存凭据；没有使用替身供应商。此验证覆盖真实 API 和 Proxy 消息记录，不包含外部监听端口、工具调用回合、Harbor Agent/Verifier、沙箱或 Slime 端到端训练。未修改产品代码，未 push。

2026-11-17 用户追问 bridge 是否用于单轮替换 Step 006 链路。对照 Step 006 pipeline 六阶段与 fork server.py:2009：bridge.complete 对应一次模型请求的格式接入，内部 body→GenerationRequest→adapter.generate→GenerationResult→回复 dict；它本身不决定整条链路切换，也不管理完整 Agent 轮次。启动时 create_app(message_backend=DressageBridge(...)) 注入，pipeline 的 API 分支绕过原 token 构建/SGLang 生成/输出解析，分支外层继续负责 session/turn 与锁，分支内负责 hooks、message StepRecord 和 JSON/SSE。一个 Agent 任务可多次调用 complete；真实验证仅覆盖一次文本请求及 finalize/read，未证实完整工具/Agent/Verifier 运行。此为助手澄清，尚不记录为用户已掌握。

2026-11-17 完整 Trial 前的边界澄清：Gateway 实现在 Dressage integrations/harbor/gateway.py，不是 Harbor 自身的模型服务；它鉴权/绑定 Trial 后在进程内委派 RolloutLLMProxy.app，后者进行 Agent 协议转换并经 HTTP 请求中央 Dressage Proxy。修改集中于中央 Proxy 的消息后端、初始化及消息记录，不只是换 SGLang URL；其余 Trial/Verifier/lifecycle 原则上复用但尚未联合验证。网关和 RolloutLLMProxy 会转发 Agent 的 temperature/top_p/stop_sequences→stop/tool_choice 等；首版 adapter/bridge 拒绝其中部分参数，必须用选定 Agent 的真实请求核对，不能承诺其他代码完全不用改。完整跑 Trial 前还需安装固定 Harbor/插件、准备单题 JobConfig 与实际环境、共享 Proxy 凭据并验证 Agent→Gateway 网络可达。沿 MH-001 做运行准备，不需要重读整仓或重写 Gateway。

2026-11-17 替换兼容性验证：新增 tests/test_rollout_proxy_api.py 的 9 个案例，使用真实 RolloutLLMProxy.app→真实中央 Proxy→adapter，仅供应商 HTTP 模拟。OpenAI/Anthropic × 普通/SSE 四条通过；Anthropic 工具调用→tool_result→第二次生成通过，身份、finalize/read 保留。temperature/top_p/stop_sequences（包括空列表）/tool_choice 四种显式参数仍得到400，未静默忽略。完整项目87项通过。
随后以本地.env发出一次真实请求：合成Anthropic /v1/messages→未改的RolloutLLMProxy→中央Proxy→MiniMax；HTTP200，返回OK，stop_reason=end_turn，1.50s，转换后的usage input_tokens=204/output_tokens=17，finalize1step/read1record。未输出密钥。此检查替换了HTTP传输为ASGI内存传输，未覆盖Gateway路由凭证分配、真实Agent CLI、Harbor Trial/Verifier/环境；不得冒称完整Trial通过。未改RolloutLLMProxy或其他生产逻辑。结论：支持范围内的模型后端替换已验证；任意Agent配置不能直接照搬，下一步按MH-001准备固定Harbor与单Trial配置。

2026-11-17 参数兼容性修订（用户已确认执行）：保留请求意图，将 stop 加入 GenerationRequest 并由 Bridge 映射；MiniMax 层按实际能力区分无约束/支持/不支持。空 stop 列表正常运行，tool_choice=auto 验证后转发；非空停止标记和强制工具选择不得静默降级。沿用现有 three-layer adapter 及 Dressage fork，不新建 runner。执行顺序：核对文档与真实接口 → 添加失败回归（协议入口、合同、供应商出站）→ 最小修改 → 全套测试及更新使用说明。范围仅 stop/tool_choice，temperature/top_p 保持现有规则。选择按能力适配，而非全部拒绝或未经验证全部透传。

2026-11-17 参数兼容性修订：用户指出替换后端应保留原 Agent 的控制意图，不能因尚未核对就将整个可选字段拒绝。新 GenerationRequest.stop 保存字符串或字符串列表；Bridge 将 stop/tool_choice 交给 Adapter 决定能力。None/[] 不设置停止约束；auto 原值转发。非空 stop 及非 auto 选择模式仍明确拒绝，不静默降级；UnsupportedControlError 映射为包含字段和限制的安全 400。非法空字符串、非字符串列表元素及其他类型也拒绝。未改动 Dressage 子模块，未改变 temperature/top_p 范围。

证据分层：MiniMax Anthropic 兼容文档列出 auto 支持、stop_sequences 忽略；不能直接视为 OpenAI 接口同样支持。另向实际 api.minimax.cn/v1/chat/completions、MiniMax-M3 发三次探测：auto→200/READY；stop=[CUT_HERE]→200但返回 READY CUT_HERE AFTER.，证明该次并未执行停止约束；指定工具→length/无工具，输出预算512，该结果不充分，不能宣称支持或普遍不支持强制调用。

先加回归出现21项预期失败，再实施修订，完整109项通过。包含真实转换器 OpenAI/Anthropic × JSON/SSE、含auto的两轮工具消息交接、空stop、错误类型、约束失败以及不泄露参数值。修改后再发一次真实请求：合成Anthropic请求含空stop_sequences与auto→原转换器→中央Proxy→新Adapter→MiniMax，HTTP200/OK/end_turn，1.15s，finalize1step/read1record。内部HTTP为ASGI；未运行Harbor Trial、真实Agent CLI/Verifier/沙箱。USAGE与测试说明同步；未commit/push。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
消息结果合同、Proxy 接入及评测记录提交已完成本地自动验证。76 + 10 项通过，启动 smoke 通过；完整上游训练测试受 PyTorch 缺失限制，真实 API/Harbor/Slime 运行未执行。
<!-- SECTION:FINAL_SUMMARY:END -->
