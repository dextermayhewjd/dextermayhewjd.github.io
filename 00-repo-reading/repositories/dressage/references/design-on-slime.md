# Dressage 学习指南：从 Agent 运行到 Slime 训练数据

[项目入口与唯一进度](../README.md) · [五个学习方向](#learning-directions) · [从哪里开始与怎样推进](#reading-guide) · [既有 Step 000 scope](../topics/01-native-agent-rollout/steps/step-000-slime-bridge-and-interfaces/01-scope.md) · [沙箱预热对照](../../agent-sandbox/references/dressage-prewarm-comparison.md)

2026-11-05，用户回贴并确认将这份设计分析保存为后续 Dressage 学习的 reference / guide。后续围绕本页的五个方向选题；实际阅读位置仍只在项目 README 维护。保存指南不表示这些内容已经读懂，也不自动开始新的函数或步骤。

**学习目标：理解 Dressage 怎样把复杂 Agent 的运行过程，稳定地转换成 Slime 能训练的数据。** 重点观察接口分工、数据是否一致、失败后如何处理；用源码与具体调用判断设计作用，不把新增模块直接等同于全面优于 Slime。

## 1. 比较口径与总览

用户希望理解 Dressage 的设计，以及它在 Slime 基础上把哪些内容做得更扎实。这里比较 Dressage 本地提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c 与它锁定的 Slime aaf5c2092b01219fa0d5c2d323741d409086ca32，不把结论扩展成 Dressage 全面优于最新 Slime。

Dressage 主要强化的是 **复杂 Agent 运行 → 可验证的轨迹 → 可供 Slime 消费的训练数据** 这条桥梁。Megatron 训练、SGLang 推理与 Slime 的核心调度/数据协议继续复用；Dressage 提供自己的 rollout 入口、代理、环境交互组件和训练接入 hook，也有特定训练路径的包装与扩展。

黑盒主线可分为：

1. Slime 通过配置的生成/rollout hook 交入 sample。
2. Dressage 的 generate 取得环境，配置并运行外部 Agent。
3. Agent 的模型请求经过 Dressage Proxy 到推理服务；Proxy 记录 token 级数据及分段关系。
4. 运行结束后，Dressage 取回轨迹，构造 Sample 列表，处理奖励与训练字段，再交回 Slime。

这不是把所有功能放在一个 generate 函数中，而是由它串联下列职责：

| 层 | 主要责任 |
| --- | --- |
| Slime / Megatron / SGLang | 训练与推理底座、组级生成调用及相关训练协议 |
| Dressage rollout | 组织任务、异步组、预热、失败处理、轨迹到 Sample 的交接 |
| Paddock | Agent/工具如何交互，管理这次交互的生命周期 |
| SandboxProvider | 创建或取得运行环境、执行命令、读写文件、释放环境 |
| BlackboxServer 与后端适配器 | 对外提供统一会话/turn 协议，连接 Claude Code、Codex 等实际 Agent |
| Dressage Proxy 与训练 hooks | 模型请求转发、token/轨迹记录、分段、奖励与训练权重语义 |

## 2. Slime 原本已经有的能力

不能把“Dressage 有某模块”直接写成“Slime 没有”：

1. 基线 Slime 的 [BaseAdapter](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/agent/adapters/common.py#L127)已有协议适配、会话、在途请求及单轮模型调用流程。
2. [TrajectoryManager](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/agent/trajectory.py#L269)已有轨迹树、分支和将一条执行导出为多个 Sample 的能力。
3. [Sandbox 协议](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/agent/sandbox.py#L28)和 Harness 已将部分运行环境、Agent 启动行为抽象出来。
4. [generate_and_rm_group](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/rollout/sglang_rollout.py#L294)已有并发与多 Sample 返回支持，Slime 也已有 partial rollout 和 fully_async 示例。
5. Slime 的 [RolloutManager](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/ray/rollout.py#L449)提供奖励后处理、训练数据转换等扩展点。Dressage 的连接方式可以从[配置示例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/rollout.md#L373)核对。

所以应把下面内容理解为具体场景上的扩展、分层与约束加强，而不是重新发明所有基础能力。

<a id="learning-directions"></a>

## 3. 后续学习的五个方向

先完成第 4 节的单任务主线，再按下表逐步深入。五项是选题方向，不是五个预先生成的 Step；每次围绕一个具体交接或疑问确定当轮范围。

| 顺序 | 要回答的问题 | 主要材料 | 这一方向读到什么程度 |
| --- | --- | --- | --- |
| 1 | 换 Agent、换沙箱时，哪些接口保持不变？ | Paddock、SandboxProvider、BlackboxServer | 能沿一次 init → 注册/调用 → terminate 说明各层职责，以及结果交给谁 |
| 2 | 多轮调用、压缩和分支后的数据怎样对应实际生成？ | Proxy、TITO、Session/Lineage | 能追踪一次请求的 token、logprob、mask，并解释什么时候能够续接、什么时候需要分段 |
| 3 | 切成多个 segment 后，奖励和训练权重怎样保持正确含义？ | multi_segment、reward_post_process、convert_samples | 能区分题目、原始轨迹与 segment；用一个小例子解释奖励广播和归一化单位 |
| 4 | 长任务和训练更新并行时，怎样管理环境、取消和过旧数据？ | 异步 worker、prewarm、lifecycle、staleness、暂停/恢复 | 能说明环境和任务由谁持有、何时交接、取消后谁清理，以及按什么单位过滤过旧数据 |
| 5 | 环境失败、半份轨迹或异常输出如何避免污染训练？ | 失败样本标记、轨迹校验、评估与运行日志 | 能跟踪一种失败从发生到记录、重试/过滤、清理的路径，并与正常低奖励区分 |

第 5 项的必要失败边界会随前四项一起观察，不要求等所有正常路径读完后才处理。每个方向的具体源码与比较依据如下。

### 1. 把 Agent 接入与环境后端分开

问题：更换 Agent CLI 或环境时，不能把任务执行、模型记录和训练交接一起重写。

Dressage 用 [Paddock 接口](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/interface.py)表达交互方式，用 [SandboxProvider 协议](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/provider.py)表达环境能力；BlackboxAgentPaddock 将二者组合。BlackboxServer 的 [适配器工厂](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/factory.py)当前明确注册 opencode、openclaw、claude_code、codex。

一次实际交接见 [BlackboxAgentPaddock.init](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L64)：构造 SandboxSpec，取得 lease，解析服务端点并检查健康，最后保存 SandboxState。之后 register_agent/call_agent 操作的是交互层，而不是重新创建环境。

当前公开 provider 仍只有 e2b 与 local_bwrap；抽象可扩展不代表已有全部后端，更不代表已经实现 Kubernetes Pod controller。

### 2. 将多轮模型请求作为明确的训练数据来源

问题：Agent 会修改消息历史、压缩上下文、调用工具或创建子 Agent。仅拿到最后一句回答，无法说明训练用了哪些 token、对应哪些 logprob。

基线 Slime 的 [_run_turn](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/agent/adapters/common.py#L318)经 _render_token_ids 对消息调用 chat template，并记录 TurnRecord；Dressage 将相应职责组织成独立 Proxy、Session/Step/Lineage 与轨迹存储。

重点看 [Qwen35TITOTokenizer.merge_tokens](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/tito/tito_tokenizer.py#L192)：复用已记录 token 前缀，并编码新增的非 assistant 内容；配合 [SessionManager](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/session_manager.py)和 [Proxy server](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py)对历史续接、分支与分段的判断。不能把任意被改写的历史直接当作原轨迹的 append-only 延续。

这强化了 token、mask、logprob 与历史关系的可检查性，但 TITO 实现与模型/模板有关；不能从 Qwen 适配推出任意模型都已正确支持。这里也不把基线每轮模板编码简单定性为所有场景中的错误。

### 3. 明确分段后的奖励和梯度权重语义

问题：同一道题可能产生多条 rollout，每条 rollout 又可能切成不同数量的 segment。若把所有段直接当独立样本归一化，会改变原本的统计单位。

1. [expand_segments_to_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/multi_segment.py#L118)明确 parent_traj_id、segment_index 与 rollout_id，拒绝重复段编号；各段保持与原始轨迹的联系。
2. [reward_post_process](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/training/reward_post_process.py#L79)在分段场景按原始轨迹选 anchor，在轨迹层计算归一化奖励，再广播到各段；raw reward 保持只在 anchor 上非零的稀疏形式。
3. [convert_samples_to_train_data](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/convert_samples.py#L89)在相应 GRPO / Reinforce++ baseline 配置下计算 prompt-equal 的 mask 分母，避免分段方式无意改变题目的训练权重。

Slime 基线已经支持多段/多 Sample，并有 rollout_mask_sums。这里的增量是分组单位与归一化语义的明确调整，不是“Slime 只能返回一个 Sample”。转换文件本身注明其大部分逻辑接近复制 Slime，并要求随上游变动校准，这也是维护成本。

### 4. 围绕长任务处理前瞻、取消和版本过旧问题

问题：长 Agent 任务与权重更新、环境创建、异步数据收集交织，光能启动并发任务不够。

1. [PrewarmScheduler](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/scheduler.py#L35)提前取得具体任务组；[PrewarmStore](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L66)以 session_id 保存并转交初始化结果。
2. [Paddock 的创建路径](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L64)与 [lifecycle](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py)处理取消后可能晚到的创建结果及回收，不假定取消 await 就一定取消远端资源。
3. [StalenessTracker](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/staleness.py#L88)和组过滤器依据可确认的版本信息处理过旧组；过滤单位保留 GRPO 组关系。
4. [_safe_update_weights](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/training/train_async_with_rollout_pause.py#L95)将本代理的暂停/恢复与权重更新连接，相关 proxy 逻辑记录版本并处理分段生成。

Slime 已有异步与 partial rollout；Dressage 的 fully_async 模块也明确说沿用其示例形态。应重点比较长黑盒任务的交接协议和失败路径，而不是把“有异步循环”本身当成新增创新。当前预热调度仍为 FIFO，自动预热只对 E2B 启用，不能说这些机制解决了所有调度问题。

### 5. 把失败、结果完整性和评估约束纳入闭环

问题：环境或代理失败不能悄悄变成一条正常的低奖励样本，训练也不应消费半份轨迹。

1. [mark_aborted_no_grad](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/multi_segment.py#L72)保留失败轨迹身份，将样本标为 remove_sample，并为重试清理会话身份；转换时清零无效样本的 loss mask。
2. [TrajectoryStore.write_many](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/trajectory_store.py#L289)先验证整批分段，再发布到内存索引，失败时恢复原索引。这里是进程内发布的一致性，不是分布式持久事务。
3. [黑盒调用客户端](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py)用稳定 turn_id 连接重试与异步查询，降低重复提交同一次 Agent turn 的风险。
4. [SWE-Gym evaluator](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/recipes/swegym/evaluator.py#L48)在新的环境中应用补丁和评估，并有禁止修改测试路径等约束。基线 Slime 已有独立评估环境，新增重点在该具体配方的完整接入和校验，不能说 fresh sandbox 评估是 Dressage 首创。

<a id="reading-guide"></a>

## 4. 从哪里开始与怎样推进

### 4.1 第一轮：先读懂一次黑盒任务的交接

沿用现有 Step 000 的 [blackbox_dispatch.generate](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L116)。第一次选择未取得预热环境、Agent 正常结束的路径；已有预热、取消和失败分支保留位置，后续带着问题回查。

1. **取得环境**：从输入 sample 和 metadata 出发，找到 paddock.init 接收什么、交回什么 state。
2. **注册并调用 Agent**：看 state、会话标识和代理地址怎样交给 register_agent，任务消息怎样交给 call_agent；先按接口理解实际 Agent 的内部执行。
3. **取回轨迹**：找到 finalize_session 和 read_trajectory，分清 Agent 回答与代理保存的轨迹并非同一份结果。
4. **构造训练样本**：看 segments 怎样交给 expand_segments_to_samples，并把 list[Sample] 返回调用方。奖励后处理与 train_data 转换属于后续 hook，先定位消费者。
5. **保留退出位置**：看 finally 中怎样安排资源回收；安排后台回收不等于返回前远端资源已经释放完成。

这一轮始终跟踪两条结果通道：

| 来源 | 得到什么 | 后续用途 |
| --- | --- | --- |
| paddock.call_agent | call_payload，经提取得到 agent_response | Agent 的回答文本，可参与日志及样本构造 |
| proxy_client.read_trajectory | trajectory_payload 中的 segments | 带有训练所需字段的轨迹分段，参与 Sample 构造 |

**停止标准**：能借助代码指出输入从哪里进入、Agent 在哪里被调用、回答与轨迹分别从哪里来、样本在哪里形成，以及退出时谁安排清理。此时不要求解释 TITO 算法、所有 provider、每种 Agent 协议或全部训练 hook。

### 4.2 主线之后：每次只展开一个需要解释的关系

1. 从上面的真实调用点进入相应组件，按第 3 节的方向选择当前问题。
2. 先说清调用时已有的数据、当前函数负责什么、产生什么结果或状态变化、读完回到哪一行。
3. 首轮从选定入口向下最多追两层；复杂依赖先保留输入输出，不能因出现一个名字就自动将整条依赖链加入必读范围。
4. scope 保留完整主线与可持续回查的面包屑，前面读过的入口不因当前函数变化而消失；具体函数解释进入各自短期卡。
5. 已有的 Slime、预热和沙箱知识按需唤起，不从头重读，也不因为以前接触过就假定当前已经掌握。原话、明确未知、静态证据与运行证据分别记录。

本页维持方向与边界，项目 README 保存唯一进度，步骤 scope 限定当轮范围，02/03 保存本轮与继承的记录。旧的认知阅读指南和岗位对照仍作历史参考，其中的旧 Step 号不覆盖本页与项目接续。

预热已做过对照，可作为既有背景；Kubernetes 资源控制继续放在 Agent Sandbox 的独立目标下。其他特定训练配方、存储与负载均衡优化，只有当前问题需要时再补，不扩成额外必读清单。

<a id="six-stage-reading-order"></a>

### 4.3 六段 generate 骨架的阅读顺序复核（2026-11-05 建议）

> 后续落实：用户选择将 init 前的补读拆成三个短 scope，并要求原步骤按位置顺延。现行目录为 001 身份与参数、002 客户端与预热、003 未命中对象准备、004 原 init、005 原注册准备；见[编号对照](../step-numbering-2026-11-05.md)。新增范围尚未记为已读，以下保留六段主线的深度建议。

用户重新要求按“理解框架，并对齐腾讯混元岗位”审视阅读顺序。以下沿用本页五个学习方向，把投入落到既有六段代码上，不新增另一套必读专题。它是本轮提出的顺序与深度建议，不代表这些函数已读完，也不自动改动 Step 编号或启动新步骤。

**建议固定：先按实际执行顺序走通单任务正常路径；每个交接说明对象来路和去向；随后把深读重点放在 Agent 交互、训练轨迹与样本正确性，以及相关并发和失败语义。**

此前进入 init 是为回答环境对象和 state 的问题，本身有依据；不足在于前置只按接口看时没有足够醒目的边界说明，之后又在 local_bwrap 具体实现上停留较多。已有阅读不清零，后续补来路即可。不能用“先核心”作为省略读者必需输入的理由，也不把完整线性阅读等同于逐个通读所有辅助函数。

#### 第一轮：六段顺序不变，阅读深度有区别

| 骨架中的段落 | 按实际交接要看清什么 | 本轮深度与停止位置 | 对应学习价值 |
| --- | --- | --- | --- |
| 1. 任务身份与参数 | sample 怎样提供 session_id、instance_id、env_args；blackbox_type、backend_options、命令计划从哪里来 | 短读字段来路及消费者。ID 生成、配置合并、日志不单独扩成专题；字段后续发生变化要继续追踪 | 请求归属、任务/环境分离与后续一致性 |
| 2. 客户端与环境取得 | get_proxy_client；claim_prewarm 的有/无结果；未命中后的会话 ID 更新；get_paddock_from_env；paddock.init | 必须能说明两条分支最终怎样得到同一次任务的 paddock/state。两个获取函数短读缓存和创建何种对象；预热先读交接，不展开预测和调度器。init/Provider/Lease/State 复用已有记录 | 可替换环境接口、对象生命周期和资源交接 |
| 3. 注册准备 | register_agent 把环境、身份和模型代理地址交给谁；before_agent 的执行位置；Proxy 会话上下文登记 | 沿 Paddock → 客户端 → 服务接口走一条正常注册路径。分清两个服务上的登记；命令配置和重试细节按需。停止在 call_agent 之前 | Agent 接入、组件分工、协议与配置连接 |
| 4. Agent 执行 | call_agent 怎样提交任务并等待结果；模型/工具交互发生在哪里；call_payload 怎样得到 agent_response | 重点读。先跟随一个 Agent 路径，知道长调用怎样结束、结果如何返回，并定位执行期间的模型请求和轨迹记录；不并行通读所有适配器 | 模型/工具调用、多轮任务、异步交互与结果协议 |
| 5. 收尾、轨迹与样本 | after_agent；finalize_session；read_trajectory；segments；expand_segments_to_samples | 重点读。分清回答文本与训练轨迹，核对 Sample 中关键字段和原始轨迹归属；明确 reward 尚有哪些后续步骤 | 结果收集、训练数据与评估交接 |
| 6. 退出与回收 | finally 如何处理未完成上下文、安排环境释放；取消或异常如何影响样本与资源 | 第一轮看正常交付与退出时机，且在遇到错误时保留责任归属。随后选一个取消/失败路径深入；不要求穷尽所有恢复代码 | 并发、资源所有权、失败一致性 |

第 2 段的 get_proxy_client 不创建 Proxy 服务；get_paddock_from_env 获取/创建操作对象，不能与 init 获取实际环境混为一谈。claim_prewarm 命中时还可能等待此前的初始化完成，不能把“命中”概括成一定立即返回。

#### 两个贯穿全流程的观察点

1. **执行期间产生轨迹。** 模型请求经过代理、记录 token 等信息，发生在等待 call_agent 的期间。先在第 4 段定位这条关系，第 5 段再解释怎样收尾、读取和交付；不能把第 5 段读取轨迹理解成此时才开始记录。
2. **返回数据与释放资源是不同交接。** Python 在真正交回 result 前执行 finally；其中安排的后台清理可以更晚完成。源码的异常处理还会形成 ABORTED 等结果或继续抛出取消，正常路径的列表返回不能概括所有分支。

#### 第二轮：沿已走通的链路深入，不再另造课程顺序

1. **先从训练消费反查轨迹正确性。** 已知 Sample 的用途后，沿第 4/5 段进入 Proxy、Session/Lineage、TITO，核对生成的 token、logprob、mask 与上下文改写/分段的关系。重点是实际生成的数据能否被正确用于训练，不要求同时读所有模型适配。
2. **接上这份函数外的训练与评估接口。** expand_segments_to_samples 之后，继续看 reward_post_process、convert_samples_to_train_data，并沿一个任务评估样例定位原始 reward 的来源。需要能解释同一条 rollout 的多段不能被误当多条独立答题，以及不同任务/轨迹权重怎样处理。这属于原学习方向 3 和 5。
3. **再选一条长任务失败路径，连接并发治理。** 例如取消时远端工作还在运行，怎样终止/回收、怎样标记无效样本，重试怎样关联同一次 turn。随后再读批量异步调度、前瞻预热、staleness；它们的理解依赖单任务与样本归属已经清楚。

失败和清理的基本边界不必等第二轮才说明；第二轮深入的是完整机制。吞吐、性能和 Kubernetes 能力仍需要实际验证，源码阅读本身不能代替部署或实验。

#### 与岗位原文的对齐

依据已保存的[腾讯岗位原始响应](../../../../slime_photo/code-reading/job-evidence/2026-10-26-tencent-2061654749727600640.raw.json)，职责 2/3 强调模型、工具、任务、上下文、Trace、结果与评估的组件化和接入，职责 4 强调并发、资源和行为一致性，职责 1/5 要求连接强化学习、数据生成、评估与训练视角；要求 3 单独提出 Kubernetes/容器的集群经验。

因此，当前不应把主要投入停留在工厂、字段容器或某个非 Kubernetes 沙箱后端，也不应只认识 Protocol 的方法名。适合岗位的深读对象是具体的交互和数据一致性机制，并用一个可复现的小场景核对它们。Kubernetes 的资源创建、状态和回收继续使用 Agent Sandbox 已有阅读，不把 local_bwrap 或 E2B 客户端当作 Kubernetes 实现；两边通过 Provider 接口建立联系。

上述是基于 JD 的投入建议，不是对面试内容的保证，也不推断腾讯内部使用这些仓库。旧岗位对照中的固定比例、“明确不考某实现”等措辞不作为本轮取舍依据。

<a id="rollout-worker-reading-time"></a>

#### Rollout worker 什么时候读（2026-11-06 阅读建议）

用户追问：何时系统补充 rollout worker，而不只在领取预热时发现上游缺口？

1. **当前 Step 002：只补最小上游关系。** 知道异步 worker 提前取组、要求调度器启动预热，再派发同一组 sample；明白为何 generate 能用同一 session_id 找回记录。整体位置已补在 Step 000 的 3.1，不据此认定 worker 已读完。
2. **系统阅读时点：单条 rollout 正常闭环走通之后，进入批量/异步运行治理时。** 前提是能说明环境取得、Agent 注册与执行、轨迹转 Sample、退出清理；不要求此前穷尽各 Agent、TITO 或全部异常分支。这是原学习方向 4 的展开位置，不另增一套课程。
3. **届时的候选入口：AsyncRolloutWorker.continuous_worker_loop。** 以 fully_async_rollout.py 为一个代表路径，观察任务组来路、预热与派发、活跃组并发上限、完成结果交付和未使用环境清理；再按具体问题回查 PrewarmScheduler。partial/fully 两种实现不必同时通读。

当前不提前编号或创建 worker 步骤、函数卡；正式进入该阶段时再确认本轮范围。参考源码：[continuous_worker_loop](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/fully_async_rollout.py#L334)。

#### 当前从哪里接续：只补入口来路，再继续注册

1. 先作一小段前置回查：get_proxy_client → claim_prewarm 的有/无结果 → 未命中的 session_id 更新 → get_paddock_from_env。ID 和环境参数的来路如果仍不清楚，同处短补；不新建四个独立 Step。
2. 到达 init 后复用原 Step 001（现 Step 004）已读内容，指出这一步已经覆盖正常初始化与接口交接，不要求重读全部方法和类卡。
3. 然后继续已经建立的原 Step 002（现 Step 005），从 register_agent 进入注册准备。
4. 后续顺序维持执行 → 轨迹/样本 → 回收闭环；未来 Step 围绕这些业务交接确定，不因遇到一个新类就临时新增一条学习路线。

Step 000 的六段可以作为后续步骤的归属索引，但不机械对应六个新 Step：短字段准备可以只作前置回查；执行和轨迹等复杂部分可以分成多个明确问题。每步开头写清“来自哪一段、覆盖哪一分支、输入是什么、输出交给谁”，关闭本步时保留未展开的接口，避免把“图上出现过”写成“已读懂”。

源码定位：[客户端获取](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L43)、[Paddock 获取](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L165)、[预热领取](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L217)、[Agent 调用客户端](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L97)。其余固定版本入口见上方五个方向。

<a id="job-reading-stop"></a>

### 4.4 为腾讯混元岗位读到哪里（2026-11-07 建议）

用户问：“看一下如果要用dressage来找这个腾讯混元的岗位，那么我需要看这个dressage到哪里呢？”

**建议的系统阅读终点：能沿一条真实 Agent 任务说明执行、训练数据和资源交接，能追踪一种失败，并能对一个小改动或场景做验证。** 不以读完全部文件或积累多少函数卡为终点。这是基于已保存 JD 的投入建议，不代表招聘结果或面试范围保证；当前仍在 Step 005，以下不是完成记录。

沿用第 3 节五个方向，把它们收拢为三个验收层次，不新增课程或预编号步骤：

| 层次 | 读到哪里 | 停止标准 | 对应原方向 |
| --- | --- | --- | --- |
| 1. 单任务闭环 | 以 blackbox_dispatch.generate 为主线，完成注册、call_agent、一个 Adapter 的实际进程调用、模型/工具交互定位、结果与轨迹读取、Sample 形成和 finally 清理；接上一种任务的评测来源 | 能从题目跟到返回的 Sample；分清 Agent 回答、Proxy 轨迹和评测结果；知道新增 Agent、环境后端、评测各改哪里 | 1，及 5 的基本边界 |
| 2. 训练数据正确性 | 从 Proxy 的请求与会话记录进入一个 TITO/上下文变化案例，再到 multi_segment、reward_post_process、convert_samples_to_train_data | 用一次工具交互和一次上下文压缩说明 token/logprob/mask 的对应；用“一条 rollout 两段、另一条一段”解释原始轨迹归属、奖励和归一化单位；能区分运行故障与正常低分 | 2、3、5 |
| 3. 并发与运行治理 | 选 fully_async 的 worker 为代表，连接 prewarm、环境所有权、取消/超时、无效样本处理与 staleness/权重更新边界 | 能回答谁限制并发、谁持有任务和环境、创建中取消后谁回收、半份结果怎样处理、过旧数据按什么单位判断；能用会话/任务标识定位日志证据 | 4、5 |

第二、三层仍沿第一层已走通的真实调用回查。TITO 先读一个模型/模板和一个具体上下文变化，异步先读一种模式，失败先完整追一种场景；不要求先枚举所有实现。

**投入边界：**

1. Claude Code 作为完整黑盒样例；Codex 只比较命令、配置与输出协议的不同。白盒看一个入口如何共用 Proxy/训练交接即可，不要求把所有 Agent 和 provider 同等精读。
2. 当前安装与多 harness 讨论收束在“程序在哪里提供、任务何时选择、运行时谁启动、哪些组合尚需适配”。制作全套镜像、让所有代码题遍历所有 harness 是可选实践，不成为当前主线的新前置。
3. 多教师蒸馏、TransferQueue、复杂负载均衡、所有 partial/fully async 变体及训练引擎内核暂作按需材料。这是当前预算取舍，不表示岗位不会涉及这些问题。
4. JD 单独要求 Kubernetes/容器集群经验。当前 Dressage 的内置 provider 是 e2b/local_bwrap，不能用它们替代 K8s 部署排障；K8s 继续沿 Agent Sandbox 与共享专题进行，不在 Dressage 中补造另一条控制器课程。

**把阅读变成求职证据：** 建议用一小组固定任务和一个现成 harness，保留一次成功及一次失败/取消的日志、结果和清理观察；选一个有限改动（如任务配置或评测接入）说明改动位置和验证结果；再用小样本检查轨迹/分段到训练字段的关系。没有真实运行的部分只报告源码分析或测试结果。完整多卡训练不是上述每项验证的前置，但若报告训练收益或吞吐改善，必须有对应实验。达到这些标准后可停止系统通读，主要投入转向实践及具体问题回查。

**当前位置后的顺序：** 当前 Step 005 先返回 BlackboxServer.register 收束初始化结果，再完成 before_agent 与 Proxy 会话登记；下一正式范围候选是 call_agent 的执行链。之后完成轨迹、评测与回收，再进入上述第二、三层。新增步骤仍待按实际问题确认，不因本节列出材料就提前建卡或改写阅读进度。

岗位依据为已保存的 [2026-10-26 官方响应](../../../../slime_photo/code-reading/job-evidence/2026-10-26-tencent-2061654749727600640.raw.json)：职责 2/3 对应组件封装与接入，职责 1/5 对应训练/评测交接，职责 4 与要求 1/5 对应并发、资源、稳定性和验证。源码入口复用第 3 节与 4.3 节的固定版本链接。

<a id="readability-and-observability"></a>

### 4.5 是否比 Slime 更清楚、更容易观测（2026-11-07 校准）

用户追问：“所以我是想要知道这个真的比slime要清楚或者容易观测很多吗？”

**不能把组件拆分更多、诊断字段更多，直接概括为更容易读懂或排障明显更快。** 本轮仍比较 Dressage 3e3142fe 与其锁定的 Slime aaf5c209；通过本地 Git 对象读取后者，没有把 Slime 当前 HEAD 或最新主线混入结论。

1. **源码阅读：** Slime 的 coding_agent_rl 示例直接组织 prepare_workspace、harness.run、git_diff、run_evaluation、finish_session，并已有 Sandbox/Harness/Adapter 拆分。Dressage 增加 Paddock、Provider、BlackboxServer、两级代理等交接，接口职责更独立，但初次追踪一次执行通常需要跨越更多文件和服务。当前 Lease/State、安装/选择/注册之间的困惑不能简单归因于读者基础不足。
2. **运行观测：** Dressage 的 [请求中间件](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/app.py#L47)记录 request_id、路径、状态、耗时与正文；[状态接口](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/api/health.py#L17)提供服务状态查询；[RolloutArtifactWriter](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/artifacts/writer.py#L75)把任务/会话、Agent 类型、环境、异常及 HTTP 请求响应整理为 error.json。这些是针对黑盒 Agent 的具体诊断入口，不自动构成已验证的端到端故障定位体验。
3. **Slime 也有观测能力：** 锁定版本的 [BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/agent/adapters/common.py#L318)已有 session 归属、日志、在途请求和可选 debug_callback，TrajectoryManager 记录真实生成数据；[trace_utils.py](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/utils/trace_utils.py)已有 TraceHandle、父子 span 与 SGLang 耗时等元信息工具。工具存在不代表所有业务路径都已覆盖，但不能描述成 Slime 只有最终结果可看。
4. **学习取舍：** Dressage 的参考价值是对照具体实现——多 Agent 接入、上下文与训练数据对应、分段后的训练语义、长任务治理。已在 Slime 理解的通用主线可复用背景，不要求为了“更生产级”再完整学习一遍。4.4 的三个验收层次用于检查能力缺口，不是要求重新读完已掌握的所有组件。

本轮没有对同一故障进行双仓库运行和定位时间对比，因此不声称 Dressage 的可观测性全面领先或“容易很多”。也不因本次比较开启 Slime 的 Trace 深读或改变其暂缓状态。

<a id="reuse-integration-boundaries"></a>

### 4.6 以复用为目标，先读接入边界（2026-11-07）

> 随后用户要求完整 deep research，以避免反复在原生 worker 与 Harbor 插件之间切换入口。当前接入建议以[独立研究](agent-sandbox-harbor-integration-research.md)为准：若完整使用 Harbor 的任务/Agent/Verifier，沿 Dressage 已有 Harbor 路线，从官方入口与 Trial.run 建立全景，再展开环境、任务、预热、模型和结果接缝。下文保留本次研究前的边界讨论，不能将其中原生 worker 候选继续当作唯一入口。

用户进一步明确：能够复用 Dressage、Agent Sandbox、Harbor 的部分就复用，但接入前需要知道究竟接在哪里。这把当前问题收敛到已有项目 slime_api_data_collecting 的组件组合；4.4 的完整框架能力目标不再被当作本次接入前必须读完的清单。

需要先区分两条真实路径：blackbox_dispatch.generate → Paddock → BlackboxServer，是此前学习的独立黑盒路径；Harbor 集成则由 Harbor Job/Trial 管 Agent、Environment 和 Verifier，Dressage 通过插件接入生命周期、模型路由与产物。后者不要求同一条 Trial 再走一遍前者。此前学习保留为背景，不能因为已经读到 Step 005 就要求把独立黑盒路径全部完成后才接 Harbor。

| 接入边界 | 先定位哪里 | 需要弄清的最小合同 |
| --- | --- | --- |
| 项目入口 → Harbor | Harbor JobConfig/Trial；Dressage 的 pyproject.toml 中 harbor.plugins 注册，以及 DressageHarborPlugin.on_job_start | 谁组织题目、Agent 与尝试；插件何时收到 Job、怎样挂生命周期回调 |
| Harbor → Kubernetes 环境 | Harbor BaseEnvironment 的 start/stop/exec/upload/download 合同；现有 agentlab.sandboxes.k8s.adapter.UpstreamK8sSandbox | 哪些请求能委派给现有 K8s 适配；目录传输、镜像/资源映射、执行参数和取消语义缺什么；不是照搬同名 SandboxProvider 即兼容 |
| Harbor Agent → 模型与采集 | 插件注入的 Agent 路由、GatewayRuntime、ProxyClient | 请求协议和会话身份怎样传递；下游有哪些控制/轨迹接口；现有 API 后端如何满足这些合同 |
| Trial 结束 → 项目结果 | HarborArtifactStore.commit_attempt、插件结束/取消回调 | 评分、执行错误、轨迹和尝试身份怎样合并，失败后由谁完成记录与清理 |

特别需要提前验证模型侧的兼容性：默认 Harbor 插件连接 Dressage Proxy；ProxyClient 除 chat_completions，还会调用 finalize_session、read_trajectory 等项目专有接口。slime_api_data_collecting 当前 make_call_api_generate 是替换 Slime 模块函数的 API 后端，不是天然兼容该 HTTP 服务的实现。普通模型 API 的 URL 不能直接替代 dressage_proxy_url；是否直接复用默认 Proxy，或适配 API 后端与所需合同，需要以最小试验确认。仅关闭“要求可训练 token”也不等于免除这些接口合同。

Dressage 当前把 Harbor 锁定为 0.18.0，compat 还依赖该版本的任务解析/Trial 顺序；本机未发现 Harbor checkout 或上述项目内的已安装包，Harbor 原生接口细节尚需按锁定版本核对。现有 DressageEnvironment 是 bwrap 实现，不是已有的 Agent Sandbox 后端。

用户随后强调，优先考虑复用 Dressage 原生 rollout 的预热和调度，以减少自维护编排代码。因此**当前下一候选入口调整为 [AsyncRolloutWorker.continuous_worker_loop](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/fully_async_rollout.py#L334)**：先连接取组、do_prefetch、派发、结果队列及清理，再按需回查 PrewarmScheduler、PrewarmStore 和 generate 的领取处。这里只评估复用边界，不要求先完成所有单任务内部函数，也不启动新步骤或生成卡片。

本轮需要验证的边界有三项：任务输入能否适配 Slime 的 Sample/group；现有 K8s 环境能否兑现 Paddock.init 与预热结果合同；当前 API 模型及结果采集如何接到执行调用方。当前 prewarm_enabled 明确仅允许 e2b，原生预热调用 paddock.init，不等于已完成任务专属 setup、CLI 安装或注册。agentlab 自己已有 PrewarmStore，调用 sandbox_factory、recipe.setup、prepare_fn，并按 ready 队列交给 worker；切换 Dressage 是选择主实现和迁移行为，不是补一项原来没有的预热功能，也不能预设替换后行为相同或性能更好。

Harbor 的 Job/Trial 编排与 Dressage 原生 AsyncRolloutWorker 是不同入口。当前 Harbor 集成不能自动继承原生 PrewarmScheduler；如果之后选 Harbor 管任务，需单独核对其环境准备与 Agent Sandbox 池的组合。此前的 [DressageHarborPlugin.on_job_start](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L261) 保留为该路线的候选入口，不作为当前必须抢先阅读的函数。

## 5. 证据与运行边界

- Dressage 当前 checkout 工作区干净。其 slime 子模块目录尚未初始化，但锁定提交可在 /home/fredkeira/projects/slime 的 Git 对象库读取；本次通过 git show / git grep 读取该提交，没有切换或修改任何 checkout。
- 本机 Slime 工作区 HEAD 为 540ea919e45b8b929198abce008a103be9cfc779，并有原先的未跟踪笔记；比较未使用这个新 HEAD 代替锁定基线，也未修改它们。
- 代码、文档与已有测试作为静态证据，未运行完整项目测试、真实 Agent、E2B 或 GPU 训练。
- 额外以原始纯函数和构造样本验证两项局部语义：一条轨迹两段、另一条一段时，先按轨迹归一化得到 [0.5, 0.5, -0.5]，raw reward 保持 [0, 1, 0]；两个 prompt 各有 5 个有效 token、global_batch_size=2 时，三段的分母均为 5。脚本为本会话 /tmp/dressage_training_contract_probe.py。这不证明完整训练质量或性能优势。
- README 的吞吐/准确率结果属于项目特定实验，未作为本次“全面更好”的依据。
