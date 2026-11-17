---
id: MH-007
title: 通过现有 Dressage 插件完成 MiniMax 单题 Harbor Trial 验收
status: Done
assignee:
  - '@codex'
created_date: '2026-11-17 11:44'
updated_date: '2026-11-17 12:56'
labels: []
dependencies:
  - MH-001
  - MH-006
references:
  - /home/hongshi/projects/agent-api-integration/USAGE.md
  - /home/hongshi/projects/agent-api-integration/configs/harbor-api.json
documentation:
  - backlog/docs/doc-004 - 消息-API-Adapter-接口约定与测试案例.md
  - backlog/decisions/decision-001 - 先完成无-GPU-API-评测链路，再接-Agent-Sandbox.md
priority: high
type: task
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
当前消息适配、协议交接与评测记录合同已有测试和有限真实 API 证据，但尚未运行真实 Harbor Agent、Gateway 网络、工具执行和 Verifier。本任务在替换为 Agent Sandbox 前建立可复现的单题执行基线。

### 短规格 v0.1：真实 Harbor Trial 桥接
状态：按已确认路线整理的规格草案；具体 Agent、任务、环境和运行配置待运行前核对。本轮仅记录规格，不表示 Trial 已开跑或验收完成。

#### 目标与边界
通过现有 harbor run --config <JobConfig> --plugin dressage 入口，运行一个 Agent、一个固定任务、一次 attempt，并发设为 1。Agent 实际执行工具，Harbor Verifier 产生评分，最终结果可关联到同一 Trial，正常与失败路径均可清理资源。
本轮独立运行 Harbor，不包含 Slime 发起、K8s/Agent Sandbox、预热池、并发性能或策略训练。MH-004 保持独立待办，不作为本任务前置。

#### 已有部分与本次桥接位置
已完成：MiniMaxAdapter、DressageBridge、中央 Proxy 消息后端及非训练结果合同（MH-005/MH-006）。
本次连接：Harbor Job/Trial 启动真实 Agent 与 Environment；DressageHarborPlugin 管理 Gateway 和 Trial 路由；Agent 的模型请求经 Gateway → RolloutLLMProxy → 中央 Proxy → DressageBridge → MiniMaxAdapter。工具命令由 Agent 通过 Environment 执行，评分由 Harbor Verifier 产生，插件收尾时提交轨迹与结果。
Gateway 在插件 Job 生命周期中管理，不新建平行 runner；中央 MiniMax Proxy 使用已有 serve:create_api_app 独立启动。

#### 方案与取舍
沿用用户已确认的 Dressage → Harbor 路线，优先配置接入；只有实际预检或失败测试证明接口缺口时，才做最小补丁。
直接让 Agent 请求供应商会绕开当前 Proxy 记录链，不作为本任务方案。
先适配 K8s 会同时引入新环境变量，不利于建立原有后端基线，保留到后续阶段。
不预先承诺原插件无需任何修改；必要 Dressage 补丁须先在 fork 单独提交并说明目的，再更新 pin。

#### 三层配置合同
1. Proxy 配置：使用现有 .env 加载方式，显式设置供应商地址、模型、供应商密钥与独立 Proxy 服务密钥；不把密钥写入任务或提交。
2. Dressage 集成配置：基于 configs/harbor-api.json，保持 execution_mode=rollout、require_trainable_tokens=false、default_temperature=null。配置 Gateway 的监听地址和 Agent 实际可达地址，以及中央 Proxy URL。Harbor 进程必须获得与 Proxy 一致的服务密钥；不能假设它自动读取 Proxy 的 .env。
3. Harbor Job 配置：固定任务来源/版本、Agent 名称/版本、执行环境、一次 attempt、并发 1、有限超时/重试与产物目录。native 表示使用 Harbor 原有环境提供者，不等于直接在宿主机运行；实际 provider 在 Job 中明确。

#### 运行前必须消除的未知
- MH-001 先确认 Python/Harbor/插件实际版本、依赖安装方式、插件发现和版本门禁；2026-11-17 已在独立 .venv-harbor 完成安装、插件发现及版本门禁验证，见 MH-001。
- 根据本机能力选择一个受支持的现有环境；先核对运行时状态，再锁定环境与镜像，不把存在 docker/bwrap 可执行文件视为环境可用。
- 锁定一个包含真实工具执行及可判定 Verifier 的小任务和兼容 Agent；Agent 自带的 temperature/top_p、强制工具选择等须核对，不能通过静默丢参数伪装兼容。
- 确认 Agent → Gateway → Proxy 的实际网络和凭据传递；容器内 localhost 不当作宿主机地址。
- 在实际调用前明确所用模型、调用规模/输出限制、任务超时与重试边界，并沿用用户实际授权范围；写规格或建卡不代表已经授权任意付费调用。

#### 验收原则
按下面五项 Acceptance Criteria 验收。ASGI 内存测试不能替代跨进程网络；HTTP 200 不能替代工具执行与评分；评分为 0 不自动代表基础设施失败。真实 API 输出不保证逐位复现，可复现性指版本、配置、命令和执行过程。
先收集正常路径证据，再验证一个可控失败或超时场景。记录退出状态、评分/失败原因、Trial/session/attempt 关联及环境/路由/会话清理结果。合成测试与真实运行证据分开记录。原始私有产物留在受控本地目录，任务仅保存脱敏摘要与定位信息。

#### 规格到实施的流程
本草案与已有验收标准先用于运行准备。完成 MH-001 后，把具体任务、Agent、环境、网络和运行限制补齐并确认；已经确认的路线不重复征求确认。领取 MH-007 时再基于当时源码写 Implementation Plan，不提前把未核实的安装或补丁步骤写成可执行结论。
实施阶段按预检、网络交接、单 Trial、失败清理逐层验证；涉及代码行为变更时先添加有意义的失败回归。最后检查代码与配置差异、记录验证边界，逐项勾选并更新 Final Summary。提交、推送及发布沿用相应授权，不由任务状态自动触发。

#### 依据
当前代码基线：agent-api-integration 5342362，Dressage fork 3820149。
已核对入口：third_party/dressage/dressage/integrations/harbor/plugin.py 的 on_job_start、config.py、compat.py，以及 examples/harbor/run_harbor_rollout_qwen3.5_4b.sh 的 Harbor CLI 入口。
模型适配合同沿用 doc-004；本任务不复制或重写该合同。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 记录固定源码、Python/Harbor/插件版本、一个任务及一个 Agent；提交不含凭据的 Job 与集成配置，以及可复现的准备、启动和停止命令。
- [x] #2 通过真实进程与网络验证 Agent 所在环境到 Gateway、Gateway 到 MiniMax Proxy 的可达性和鉴权；记录所选 Agent 的参数兼容性，不以 ASGI 内存传输替代。
- [x] #3 沿现有 Harbor 入口完成一个真实 Agent 的工具执行和 Verifier 运行；评分、轨迹、失败信息与结果文件可关联同一 Trial，模型答错不能冒充基础设施故障，也不能把任意 HTTP 200 当作任务完成。
- [x] #4 正常结束及至少一个可控失败或超时场景均有可核对的清理证据，涵盖任务环境、Gateway 路由和 Proxy 会话；失败如实保留。
- [x] #5 任务中记录实际命令、版本、脱敏结果摘要及限制；原始私有运行产物和密钥不入库，不将单 Trial 验收描述为 Slime、K8s 或训练验证完成。
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. 本轮已获授权先验证单个沙箱：从已知提交导出官方 hello-world 任务，先解析配置，再通过 Harbor 的 oracle 参考解答运行单个 Docker Trial，不调用模型。
2. 核对实际文件执行、Verifier reward、Trial 异常和容器/网络清理，保存脱敏证据与失败原因。oracle 测试只是环境基线，不勾选真实 Agent/MiniMax 全链路验收。
3. 环境基线通过后再锁定真实 Agent 的参数、Gateway 网络和单题 Job 配置；真实模型运行沿用相应配置与授权范围，完成后再验证失败清理。

2026-11-17 本轮执行：使用已固定的 hello-world 任务，Claude Code 2.1.293 harness，Docker native，现有 MiniMax 消息代理；harbor run --plugin dressage，单任务/单attempt/并发1/零重试，最多6轮，Agent超时180秒。先验证配置、Gateway容器可达地址和代理健康，再运行真实Trial，检查工具、verifier、轨迹、关联ID及资源清理；Slime不在本轮范围。

2026-11-17 用户确认检查剩余1和3：复用同一 hello-world / Claude Code / Docker / MiniMax 链路，只在独立测试任务副本的 verifier 中设置确定性超时；记录异常、manifest和bundle状态、Docker/Gateway/Proxy清理结果。限制单题单并发零重试，复用现有环境与凭据，不修改训练或沙箱后端。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-17 用户要求把下一步桥接与开发流程写入 tasks。本轮在 Description 中加入短规格 v0.1，明确三层配置、复用接口、未决项及分层验收。保持 To Do、AC 0/5，不把规格编写算成实际联调；Implementation Plan 在运行前提明确并正式领取任务时再写。

2026-11-17 运行前缺口复查：当前 .venv 的 pip show 确认 harbor、dressage、dressage-blackbox-server 未安装。配置目录仅有 harbor-api.json（集成配置），没有本项目单题 Harbor Job。只读检查：沙箱内 Docker socket 访问被拒绝，沙箱外 timeout 10 docker version --format '{{.Server.Version}}' 返回 29.9.3；bwrap --version 返回 0.9.0，claude --version 返回 2.1.293。没有启动容器、Agent 或任务，也没有验证镜像/容器网络。Docker 可作为后续本地环境候选，不据此标记环境已验收。下一具体工作先由 MH-001 核对固定依赖解析和隔离安装方案，通过 Harbor 0.18.0 版本门禁与 dressage 插件发现；随后本任务锁定一个 Agent/任务/环境，准备 Job 与 Gateway 可达配置，再做实际网络和 Trial 验证。保持 To Do 和 0/5。

2026-11-17 决策归属核对：长期路线沿用 accepted decision-001（先完成 API 评测基线，再接 Agent Sandbox），不为相同选择重复建 ADR。MH-007 独立运行 Harbor 是整体验证的阶段切分，不取消最终 Slime 发起目标；短规格、具体配置与验收留在本任务。只有新出现的长期架构选择才进入 decisions；工具检查、安装命令和执行进度留在 tasks。

2026-11-17 MH-001 已完成：独立 .venv-harbor 安装及插件/版本门禁验证通过，前置依赖解除。本任务仍为 To Do、0/5；下一步锁定一个 Agent、任务和执行环境，补齐实际网络及 Job 配置，再开始 Trial 验收。独立环境使用方式见集成仓库 USAGE.md。

2026-11-17 用户要求实际检查单个沙箱能否运行。本轮范围为官方 Hello World + oracle + Docker 的环境/Verifier基线；不调用模型、不提前转入 K8s、不把此结果当成 MH-007 全部完成。

2026-11-17 单 Docker 环境基线实际通过。任务取自本地 Harbor 阅读仓库固定提交 fdba28fc411e47e8765420a1a063b4918fce3def 的 examples/tasks/hello-world，经 git archive 原样导出到 /home/hongshi/projects/agent-api-integration/outputs/harbor-sandbox-check.D70JSr/examples/tasks/hello-world，未修改原任务；用已安装 Harbor 0.18.0 解析成功。实际命令：.venv-harbor/bin/harbor trials start --path /home/hongshi/projects/agent-api-integration/outputs/harbor-sandbox-check.D70JSr/examples/tasks/hello-world --agent oracle --env docker --trial-name hello-world-docker-smoke --trials-dir /home/hongshi/projects/agent-api-integration/outputs/harbor-sandbox-check.D70JSr/trials --delete。
结果：CLI 退出0；Trial ID de7f7708-0543-477d-ab19-135aa385e897；2026-11-17 12:03:54–12:04:50 UTC，约56秒；exception_info=null；verifier_result.rewards.reward=1.0。官方 verifier 的 test_hello_file_exists 与 test_hello_file_contents 均通过（2 passed），证明参考解答在容器中创建 /app/hello.txt 并写入预期内容。任务 checksum=000d03d9cafe8a0d1a7feffa4e5625a1303652b35e4e86f16d2a53eea034cdda；本次镜像ID sha256:10a4486df54aa49ea9566116ee0473d0da865eb43863b01151a9d04a9ff2de87。验证使用 Docker 29.9.3 / Compose 5.7.1；容器内官方脚本下载了 uv 0.9.7 与 Python 3.14.0 来运行 pytest，这不改变宿主 Harbor 环境的 Python 3.12.3。
清理证据：结束后 docker ps -a 按本次名称过滤、docker ps -a / docker network ls / docker volume ls 按 com.docker.compose.project=hello-world-docker-smoke__env 过滤均为空。只检查当前 Trial，不触碰其他容器。日志有预构建镜像OS检查因inspect返回1而跳过的提示，后续容器启动和评分均成功。首次运行时 apt 出现无交互终端的 debconf 回退提示，未导致失败。
证据保存在 /home/hongshi/projects/agent-api-integration/outputs/harbor-sandbox-check.D70JSr/trials/hello-world-docker-smoke/result.json、verifier/test-stdout.txt、agent/oracle.txt 和 trial.log；outputs 已被Git忽略，原始运行产物不提交。
边界：运行的是官方 Harbor oracle 环境/Verifier基线，无模型API调用，未使用 Dressage 插件/Gateway/Proxy，不证明真实Agent、MiniMax、失败清理或K8s兼容；MH-007保持In Progress，完整验收项仍未满足。可以基于该任务调查另一Environment后端，但在正式替换前，应让同一任务经过真实Agent→Dressage→MiniMax完成端到端基线，再对比切换后的行为。

2026-11-17 真实 Claude Code + MiniMax 单题链路通过。用户明确授权按真实 harness 路线验证；未启动 Slime/SGLang/本地模型。固定源码 Dressage 3820149ebfc0536b213ec120b43ec090f09b3fcd（子模块无修改），Python 3.12.3 / Harbor 0.18.0 / Dressage 0.1.0 / blackbox 1.1.0。任务沿用固定 Harbor fdba28fc411e47e8765420a1a063b4918fce3def 导出的 hello-world，Claude Code 安装及运行日志确认 2.1.293，模型 MiniMax-M3。
执行：独立 uvicorn agent_api_integration.serve:create_api_app --factory --host 127.0.0.1 --port 8800；Harbor 进程从本地 .env 取得独立服务密钥，设置 DRESSAGE_HARBOR_INTEGRATION_CONFIG 后，通过 .venv-harbor/bin/harbor run --config outputs/harbor-minimax-claude-smoke/job.json --plugin dressage --yes 运行。配置单题/单attempt/单并发/零重试、最多6轮、Agent180秒、安装300秒、输出4096；Gateway仅绑定本机Docker网桥172.17.0.1:39100，使用HTTP和configure_only，不宣称网络出口隔离。
结果：Job 74a85c64-85f7-472d-866e-e94e0ebfe652，Trial hello-world__dMem5H7，Trial/session ID 5299f631-def1-4fb9-9f4b-4b63578ee112，instance harbor-968c363097266fba15fe1edb96b6bff4；UTC 12:16:46.817969–12:18:53.251373，约126秒，CLI退出0。Claude Code 2轮交互，Write工具实际创建/app/hello.txt，工具结果成功；代理记录两次真实/v1/chat/completions HTTP200，verifier两个检查通过、reward=1.0、exception_info=null。未修改或静默删除模型采样参数；此结果仅证明该Agent/任务实际请求范围兼容。
Dressage manifest state=completed、committed=true；bundle与同一Trial关联，reward=1.0、failures=[]、warnings=[]、trainable=false、trainable_token_count=0、finalization_checkpoint=store_drained。结束后按Compose project hello-world__dmem5h7__env过滤的容器/网络/卷均为空，Gateway39100无监听；Proxy health active_sessions=0、store各计数0。随后SIGINT停止本次Proxy，进程退出0。
原始产物仅保存在已忽略的outputs/harbor-minimax-claude-smoke/，未上传或提交。新增无凭据configs/harbor-api-docker.json、configs/harbor-hello-world-claude.json及USAGE复跑说明，两个配置通过实际模型校验，并核对除产物/任务路径外与执行配置完全一致；git diff --check通过。AC2/3/5有证据，AC1尚未Git提交，AC4尚缺可控失败/超时清理验证；任务保持In Progress，不将本次成功扩展为Codex、Slime、K8s或训练验收。

2026-11-17 按用户 smart-commit 授权完成本地主题提交：b403847 文档: 固化 Backlog 任务接续规则；ae4a17e 文档: 记录隔离 Harbor 环境的安装方式；4333364 配置: 提供 Claude Code 与 MiniMax 的单题 Harbor 验证入口。各批从实际索引导出快照检查精确路径、文档结构/链接及shell语法；第三批两个配置通过Harbor/Dressage模型校验、执行参数对照及本地凭据排除检查。uv pip check 使用临时缓存后112个包兼容，git diff --cached --check通过。没有改动代码/测试或Dressage pin，没有重跑付费Trial，没有推送远端。已满足AC1的无凭据配置与复跑命令提交要求；当前4/5，剩余AC4可控失败/超时清理测试，保持In Progress。集成仓库工作区干净，原始产物及.env仍被忽略。

2026-11-17 范围接续澄清：用户要求保存 Slime/Dressage 自定义奖励扩展点的理解，并确认 Agent Sandbox 是否为下一目标。讲解记录位于 implementation/references/reward-hooks-and-interview-notes.md，不新增训练算法必读步骤。依据当前 AC，下一具体工作是本任务尚未完成的可控失败/超时与清理验证；之后接已确认的 Agent Sandbox 后端与有限验收。MH-004 的 Slime 无 GPU 发起仍保留为最终目标的独立未完事项。本轮只保存讨论和修正导航，未运行失败测试、安装集群或修改任务状态。

2026-11-17 用户确认检查第1项；真实 verifier 超时与清理验证通过，AC4补齐。

配置与注入：沿用已验证的 Harbor 0.18.0、Claude Code 2.1.293、MiniMax-M3、Dressage 3820149、集成仓库 4333364；单题/单attempt/并发1/max_turns6/零重试。仅在 outputs/harbor-verifier-timeout-fvukn4o8/hello-world 的任务副本 tests/test.sh 顶部加入输出标记 MH007_CONTROLLED_VERIFIER_TIMEOUT 和 sleep 30；Job verifier.override_timeout_sec=2。模型、工具、Gateway、Proxy和容器均为真实运行，不使用mock；没有修改原始任务、实现代码或子模块。

启动与复跑：在 /home/hongshi/projects/agent-api-integration 运行 .venv-harbor/bin/python outputs/harbor-verifier-timeout-fvukn4o8/reproduce-check.py。该脚本由本轮 /tmp/mh007_timeout_check.py 保存而来，读取本地.env，不含密钥，使用configs/harbor-hello-world-claude.json与configs/harbor-api-docker.json，生成独立输出目录。复跑会再次调用真实付费API，须保持显式授权。脚本启动 uvicorn agent_api_integration.serve:create_api_app --factory --host 127.0.0.1 --port 8800，随后 harbor run --config <本次目录>/job.json --plugin dressage --yes，结束后SIGINT停止其自己启动的Proxy。Gateway使用本地Docker网桥172.17.0.1:39100，仍为configure_only/public网络，不宣称强隔离。

结果：Job 114b0577-e0c3-4777-a0bf-395313e349c5；Trial hello-world__UXSLL6Q；Trial/session ID 1947d48c-dbd0-4cca-9501-33329f14a3d4；instance harbor-6452ebabe5902525abb6b707814706e3。Trial UTC12:53:55.761049–12:56:22.567970，约147秒含安装。Proxy记录2次真实chat/completions请求；Agent的Write工具执行成功。Verifier stdout保留注入标记，Trial exception_type=VerifierTimeoutError，message=Verifier execution timed out after 2.0 seconds，verifier_result=null；Job n_errored_trials=1、n_retries=0。CLI退出0只代表Job执行完毕，不能当作Trial成功。

结果提交：bundle与同一Trial/session对应，rewards={}、trainable=false、trainable_token_count=0、finalization_checkpoint=store_drained；failures包含HARBOR_TRIAL_EXCEPTION（details.exception_type=VerifierTimeoutError）与REWARD_MISSING。manifest state=completed、committed=true表示结果已提交，包括失败记录，不表示题目通过。

清理断言：按com.docker.compose.project=hello-world__uxsll6q__env分别查询docker ps -aq、docker network ls -q、docker volume ls -q，三者均空。Gateway39100无监听；Proxy停止前health.active_sessions=0，store total_items/total_instances/ready_instances均0；Proxy退出0，随后8800与39100均无监听。未清理或停止其他任务资源。

证据：本地忽略目录 outputs/harbor-verifier-timeout-fvukn4o8/，包括job.json、integration.json、reproduce-check.py、check-summary.json、Harbor的result.json/Verifier stdout/Agent原始日志、Dressage manifest/bundle、proxy.log与harbor.log。额外断言检查Trial异常、ID一致、失败码、零重试、非训练合同及资源清理均通过。未上传原始产物或密钥。

已发现的表示限制：固定Dressage artifacts.py:_exception_info_failure把Harbor异常统一标为stage=agent，因此本次verifier超时在bundle.stage中也显示agent；原始exception_type/message完整保留。排障应读取details.exception_type，不能仅凭stage归因。本轮记录该限制，不为修复分类标签扩展任务。

范围：正常路径证据见前文，结合本次单一verifier超时满足本任务AC4。没有覆盖SIGKILL、主机故障、网络分区或全种类取消；没有验证Slime发起、Agent Sandbox、集群并发或训练。实现仓库与Dressage工作区均保持干净；任务状态更新不包含Git提交或推送。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
已完成固定Claude Code/MiniMax/Dressage/Harbor的单题Docker基线与一次确定性verifier超时。正常任务reward=1；超时任务如实保留VerifierTimeoutError和缺失奖励，两种路径均有环境/Gateway/Proxy清理证据。无凭据配置与复跑说明已提交于4333364，本次失败证据保留在忽略目录。5/5验收通过；不包含Slime发起、Agent Sandbox或训练。固定Dressage将Harbor异常stage统一标agent，细分原因以exception_type为准。
<!-- SECTION:FINAL_SUMMARY:END -->
