# 04 · 本步问题与澄清

[本步入口](README.md) · [阅读范围](01-scope.md)

## 2026-10-23 · 从岗位目标确定 Step 0

以下原话来自本次会话，助手建议与个人理解分别记录。

用户明确目标：

> 为的是拿到混元强化学习框架这个岗位

用户随后追问具体入口：

> 那么我应该看一下哪一个文件呢？ 我的意思 我需要看哪一个文件呢？ 或者怎么开始这个问题

助手据此建议从 `blackbox_dispatch.py::generate()` 的正常路径建立单条黑盒任务骨架，把 Agent 回答与 Proxy 轨迹分别定位，再按具体问题有限下钻。官方文档作为资料索引，不把章节顺序直接当作源码阅读顺序。

用户要求按此前 skill 给出 Step 0 scope；助手提供阅读目标、指挥官函数、核心骨架三部分。用户确认落盘：

> 那么按照这样子写一下这里的steps里的这个 0吧

本步范围因此确定为任务骨架；尚未实际展开某个子函数或形成个人函数记忆。

## 源码核对与修正

静态核对源码提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`：

- 前置与后置命令分别位于 `paddock.call_agent()` 前后，不能合成 Agent 执行前的单一位置。
- 正常路径分别从 `call_payload` 提取回答文本、从 Proxy 读取轨迹分段，随后构建样本。
- `schedule_terminate_paddock()` 安排回收任务；不能写成函数返回前已完成远端资源回收。
- 返回的训练样本仍需下游奖励处理和训练消费；本函数没有完成一次参数更新。

以上为助手核对的代码行为，不代表用户已确认掌握。未运行真实 Agent、沙箱或训练。

## 学习材料先用 Markdown 预览

用户明确调整：

> 修改这个agents files吧 当前在学的内容不需要直接写到本地的blog里面现在md文件里面做预览

依此更新学习仓库的预览规则：先保存并预览 Markdown，不要求启动 Hugo 或同步博客；只有明确要求网站呈现时才进入博客流程。

落盘前发现原 steps 目录已不存在，故按本次确认的 scope 重建 Step 0。旧项目入口保存为[历史快照](references/project-entry-before-step0.md)，不凭该入口重建已缺失的学习历史。此文件仅记录当前会话实际发生的讨论。

## 2026-10-23 · 引入树形函数图优化 Scope 结构

用户指出需要看清指挥官函数所处的环境，并强调图示“越复杂越难懂”，最好使用简单、低认知负荷的函数树或面包屑：

> 这个图到底应该怎么画 最好是函数图 或者面包屑 构建框架和比较简单 图越复杂 越难 或者你给出几种 我都看一下吧
> 我也觉得 就用这里的风格2 吧 请现在修改一下这里的step 00部分的scope吧

据此，将 [01-scope.md](01-scope.md) 第二节中的抽象四步框图替换为**风格 2：源码树形函数图（Text Call Tree）**：
- 标注了 `blackbox_dispatch.py` 中 `get_paddock_from_env` (L221)、`paddock.init` (L223)、`register_agent` (L233)、`register_session_context` (L255)、`call_agent` (L260)、`read_trajectory` (L305) 到 `expand_segments_to_samples` (L324) 的精确行号。
- 明确了外部环境三大支柱（Paddock 沙箱、Dressage Proxy 代理、Inference Engine 推理引擎）与指挥官函数的交接关系。

## 保留的下一问

Agent 执行期间，Proxy 怎样获得生成记录？这只是候选问题，尚未据此创建 Step 1 或标记学习完成。


## 2026-11-05 · 核对 Dressage 是否内置 Kubernetes 单 Pod 启动配置

用户问：

> 那么看一下当前的dressage吧
> 我想要知道的是
> 当前的dressage 是否有类似的k8s相关的如何单个运行起来一个pod这样子的配置

本次核对当前本地 Dressage 自有代码、provider 工厂、YAML 与 Dockerfile，以及 Custom SandboxProvider 文档。当前内置 e2b 和 local_bwrap；没有找到自有的 Kubernetes provider 或单任务 Pod 创建清单。文档明确把自建 Kubernetes backend 作为实现 SandboxProvider 的扩展路径。源码提交仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，工作区干净，未初始化的 slime 子模块不纳入本次否定结论。

完整依据见 [Kubernetes 接入边界](../../../../../agent-sandbox/references/dressage-prewarm-comparison.md#dressage-kubernetes-provider-boundary)。这是按问题核对仓库能力，没有迁移阅读步骤、生成未读函数卡或执行部署。


## 2026-11-05 · 用户转向整体设计与 Slime 增量对照

用户要求：

> 我想要看一下dressage是怎么设计的
> 或者说dressage在slime的基础上把哪些内容做的更加扎实了
> 我希望能够看一下

本次按 Dressage 3e3142fe 与其锁定 Slime aaf5c209 做源码比较。虽然子模块目录未初始化，本机另一 Slime 仓库的 Git 对象库存在该提交，故用只读历史对象核对。Slime 已有 Adapter、Sandbox 协议、轨迹树、多 Sample 返回和异步/partial rollout；不能把 Dressage 所有模块都描述为从无到有。

重点整理 Paddock/provider/后端适配分工，Proxy 的 token 与 lineage 记录，多段奖励和 prompt-equal 训练字段，长任务预热/取消/版本治理，以及失败样本与评估约束。使用原始纯函数对分段奖励广播及归一化分母作了局部构造输入验证，没有运行完整训练。[完整分析](../../../../references/design-on-slime.md)作为本轮阅读材料；后续仍建议从既有 blackbox_dispatch.generate 主线进入，不预建子函数卡或改写学习完成状态。

## 2026-11-05 · 将五个方向保存为后续学习指南

用户回贴上一轮的设计分析，并明确要求：

> 好的
> 那么是否考虑一下
> 把当前的这些内容写下来放在dressage里面作为一个reference或者guild
> 用来指导接下来的dressage的学习呢?

本次沿用 references/design-on-slime.md，保留已有源码比较和验证边界，完善为学习指南：五个选题方向、每项的问题和停止标准、blackbox_dispatch.generate 的首轮正常路径、回答与轨迹两条结果通道，以及随后一次展开一个关系的阅读方式。

项目入口和本步 README 已提供指南链接，旧 cognitive-reading-guide 标明历史语境。未另起一套步骤、改写本步 scope 或创建未读函数卡。用户回贴和保存请求属于对学习参考的选择，不作为已经掌握其中技术内容的证据。

## 2026-11-05 · 借鉴 Agent Sandbox 的 scope 分工

用户指定 Agent Sandbox 的 topics/kubernetes-sandbox-control/steps/step-000-sandbox-reconcile/01-scope.md，要求考虑 Dressage 的第一份 scope 是否应借鉴其处理方式。

本次采用的是版式与职责分工：目标简短明确；入口说明选定场景与最少对象背景；3.1 保留完整任务及跨进程关系，标出当前函数；3.2 给出正常路径的关键调用、源码入口和返回位置，详细解释留给后续短期卡。

Dressage 的原目标与正常分支不变，仍从 blackbox_dispatch.generate 看单条任务怎样交回样本。新版特别区分 Agent 调用期间产生模型请求、Proxy 轨迹与回答文本两条结果通道、正常返回前安排清理与后台实际释放。旧稿中 Paddock 被称为沙箱调度器、代理被描述为固定在本地，以及 Agent 调用完成等同进程退出的表达一并按源码校准。

[修改前的 scope](references/history/2026-11-05-scope-before-global-local-navigation.md)完整归档。源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；Agent Sandbox 参考文件、两层 memory 和已有学习状态未改。没有将 Agent Sandbox 独有的主题编号和继承规则迁入 Dressage，也没有创建未读函数卡或运行 Agent。


<a id="generate-first-function-card"></a>

## 2026-11-05 · 第一处函数与 Slime 钩子接缝

用户问：

> 好的那么我第一个需要看的函数是哪一个呢?
> 先看一下这里的slime留出来的钩子也就是这里的generate
> 然后需要看一下这里的blackbox dispatch 对吗?
> 那么先生成一下
> 这里的这个blackbox_dispatch.py
> 的generate的short term memory吗

本轮按明确请求建立 [blackbox_dispatch.generate 函数卡](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)，不再沿用此前“本步只建骨架、不建卡”的限制。范围仍是同一个 Step 000 的编排入口，没有自动展开子函数。

助手核对 Dressage 的配置路径与其锁定 Slime aaf5c209 的 generate_and_rm：Slime 通过 custom_generate_func 直接调用 blackbox_dispatch.generate；Slime 自带 generate 位于未配置自定义函数时的 else 分支，并非必须先执行的一层。Dressage 子模块未初始化，调用者从本机另一 Slime 仓库的 Git 对象库只读核对，未改动源码。

函数卡沿认可样例保留六段连续源码与紧邻说明：任务信息、环境取得、注册准备、Agent 调用、轨迹与样本、退出回收。重点区分回答与训练轨迹两条结果通道；正常路径返回列表，普通失败可返回 ABORTED 单样本，取消继续抛出；finally 安排后台清理不等于等待资源释放完成。

scope 的 3.1 完整主线与 3.2 五个导航位置保留，仅将当前 generate 入口接到本卡；02 更新索引，03 保持初始为空。项目 README 维护唯一当前接续。用户原话是阅读问题与建卡请求，不记为已经理解上述机制；未运行真实 Agent、沙箱或训练。


<a id="paddock-init-reading"></a>

## 2026-11-05 · 保留 generate 原卡，从环境取得段进入 init

用户在试读候选后明确当前重点：

> 好的
> 其实我觉得原本的generate其实也还挺好的
> 重点式在这个generate 之后我具体应该读什么呢?
> 我不是特别明白了

助手据此前“sandbox 是否就是 paddock”的疑问，推荐 BlackboxAgentPaddock.init：只看环境需求怎样交给 provider、怎样取得服务地址、怎样返回 state，然后回到 generate 的 register_agent。用户确认：

> 好的那么我们来看一下这里的paddock的内容吧

本轮按该范围建立 [init 函数卡](references/history/2026-11-05-init-before-ownership-correction.md)，延续 Step 000，不通读整个类、不建立 __init__ 或 provider 子卡。generate 原有六段解释保留，只补双向入口、真实反馈和来源；参考中的改版未采用。此前完整主线复述保留在[原话参考](references/generate-memory-revision-proposal.md#user-feedback)，并与助手校准分开。

静态源码显示：__init__ 配置 Paddock 对象本身；本次 init 用传入 session_id 作为 traj_id，整理 SandboxSpec，委派 provider.create，取得 lease 与 blackbox endpoint，按开关检查健康，构造 SandboxState 并把 lease/state 登记到相应字典。健康检查的客户端是 BlackboxServerClient，区别于访问 Dressage Proxy 的 ProxyClient。

本轮解释按需求、环境与地址、记录与返回三段组织；实际沙箱由 provider 管理，state 是访问资料，init 正常返回后仍需注册和调用 Agent。取消/失败清理只标明边界。用户确认阅读不等于已理解这些细节；未运行环境、健康检查或 Agent。

scope 保留 3.1 全图和 3.2 原导航，只更新当前位置与 init 入口。唯一实时接续仍在项目 README；03 保持原样。


<a id="step001-split-adopted"></a>

## 2026-11-05 · 确认逐层承接，将环境准备接续到 Step 001

用户明确 3.1 标注 Step 的位置、3.2 描述本步内部阅读顺序，并进一步提出 Step 001 的 3.1 承接 Step 000 的 3.2。对 [reference1](references/reference1.md) 的最后确认是：

> 好的那么就按照这个方式来构建吧
> 我觉得这样子可行

本轮落实为 [Step 004（原 001）](../step-004-paddock-environment-preparation/01-scope.md)：3.1 沿用 generate 正常路径骨架，仅标注环境准备的 Step 范围；3.2 展开 init 的三段阅读。Step 000 scope 校准为系统全景与 generate 的六段交接，[调整前原稿](references/history/2026-11-05-scope-before-step001-split.md)归档保留。

两张函数原件未删除或改写。Step 001 的 03 完整继承 Step 000 的 03 + 02，02 调取 init 及直接调用方 generate；首次接触、认识时间、原话和未知保持。init 曾在 Step 000 展开这一事实继续保留，后续具体认识写入 Step 001 的 02。本次组织调整不是新增机制掌握，也未运行真实环境。


<a id="memory-ownership-corrected"></a>

## 2026-11-05 · 按正式步骤边界纠正 init 的记忆归属

用户指出：

> 这里的blackbox agent paddock的内容应该是step1的内容不应该是step00的short term memroy对吗?

本次确认：BlackboxAgentPaddock.init 属于 Step 001 的环境准备问题。此前把“保留早期讨论”处理成“继续占据 Step 000/02，并计入 Step 001/03”不符合已确认边界；以上早先关于两张卡继承的记录保留为实际经过，由本条纠正其现行归属。

修正后，Step 000/02 只有 generate，Step 001/03 只继承 generate；Step 001/02 保存主读 init 和回查用的 generate。旧 init 初稿与误继承副本完整移入 references/history，原话和源码说明保留；活动导航指向 Step 001 的 init，历史来源指向归档。

此次是记录归属纠正，不表示新增机制理解或实际运行；scope 的 3.1/3.2 阅读结构不变。
