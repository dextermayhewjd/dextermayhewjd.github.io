# generate 短期记忆改进方案：保留交接，按需展开

状态：2026-11-05 的候选方案，尚未采用。用户要求先保存到 references，不直接修改正式内容。

[完整候选稿](generate-memory-candidate.md) · [现行函数卡](../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md) · [本步 scope](../01-scope.md#reading-navigation)

## 1. 这次要解决什么

用户已经清楚 Slime 的 generate_and_rm，并开始用自己的话串联 Dressage 的环境取得、Agent 调用、轨迹读取和退出清理。现行函数卡把调用来路、六段源码、外部协作、边界和导航同时展开，第一次阅读需要来回比对的内容较多。

这次建议保留原有的函数卡栏目和执行顺序，让默认正文集中回答三个问题：

1. 当前这段手里有什么数据？
2. 调用哪个函数，接住什么？
3. 拿着结果回到哪里继续？

实际源码仍由 generate 组织这些调用。本次调整针对学习记录，不提出源码重构，也不将六个阶段自动变成六个新 step。

## 2. 两种可选方案

| 方案 | 怎样处理现行卡片 | 好处 | 代价 |
| --- | --- | --- | --- |
| A：保留全文，折叠六段详情 | 每段留一句摘要，原代码与解释放进 details | 改动小，全部旧内容仍在同一文件 | 展开后重复信息依然多；直接看 Markdown 源文件时，长度基本不变 |
| **B：主卡写交接，详细说明按需回查（推荐）** | 保留完整函数模型和六段关键源码；减少重复解释，将配置、完整分支及已有外部全图留在参考入口 | 默认正文与原始 Markdown 都更聚焦；从主卡能连续读到返回位置 | 细节需要一次跳转，必须保留明确的返回位置 |

推荐 B 的依据是本次具体反馈：用户已经能概括主要顺序，目前卡点集中在对象身份与交接方向。继续增加长段解释，容易让这些关键区别被埋住。这是本次版式建议，是否更适合仍以试读反馈为准。

## 3. 推荐方案怎样落到现有栏目

| 现行部分 | 候选处理 | 必须保留什么 |
| --- | --- | --- |
| 开头定位 | 保留源码、首次接触和认识时间 | 不能因改排版重置历史；本次已经有复述，应如实反映 |
| LLM 四项 | 保留顺序，缩短重复概括 | 函数的整体职责、当前场景、真实调用 |
| Slime 调用来路 | 主文只留加载与调用的必要两行 | 参数和返回位置；完整分派作为按需参考 |
| 输入与输出 | 用一张短表区分参数、返回值和副作用 | evaluation=False；正常返回列表；环境回收安排 |
| 第 1 段任务信息 | 保留身份与环境配置的来路 | session_id 与 instance_id 不是根据 image 创建的运行对象 |
| 第 2 段环境取得 | 保留预热判断及未命中的 init 交接 | Paddock、sandbox、state 的区别；命中仍回到同一后续位置 |
| 第 3 段注册准备 | 聚焦 register_agent 的实参及注册后接什么 | Proxy 地址在这里参与配置；前置命令与会话登记仍有位置 |
| 第 4 段执行 | 保留 call_agent 的真实输入与返回接收 | call_payload 是返回值；模型请求发生在等待期间 |
| 第 5 段结果 | 分清收尾、读取、转换三个动作 | ProxyClient 访问服务；轨迹与回答分开；转换结果交回 Slime |
| 第 6 段退出 | 保留 finally 的条件及调度调用 | 安排回收不等于等待远端资源已经释放 |
| 每段跳转 | 只保留该段必要的源码入口与返回动作 | 未读子函数不提前建卡，不显示成已经展开 |
| 原话与未知 | 加入本次真实复述和明确问题 | 原话保留不准确处；助手纠正单列，不冒充用户已经接受 |

主卡继续解释 generate 自己的赋值、分支和调用组合。只在未来实际展开子函数时，才把子函数内部机制集中到对应卡片；主卡仍保留实参来源、返回值和下一步。现行卡片多数内容本来就是父函数逻辑，不能简单地把整段搬到子函数名下。

## 4. 这次复述需要怎样体现在候选稿中

| 用户表达 | 静态源码校准 | 候选中的位置 |
| --- | --- | --- |
| 通过环境 image 构建 session、instance 信息 | 身份主要从 sample/metadata 取得或生成；环境需求另整理为 env_args | 第 1 段 |
| 获得 sandbox，也就是 paddock | sandbox 是实际环境；Paddock 协调操作；state 保存本次访问资料 | 第 2 段 |
| 拿到 proxy client，让 Agent 都发往它 | ProxyClient 是客户端；register_agent 传入 Proxy 地址配置模型请求路径 | 第 3 段 |
| 通过 call payload 执行 | call_agent 发起调用，call_payload 接收返回值 | 第 4 段 |
| 所有请求发到 Proxy，所以可以在那里读轨迹 | 模型请求经过 Proxy；read_trajectory 已封装为客户端方法，向服务读取记录；不把所有工具操作都说成经 Proxy 转发 | 第 5 段 |
| session id、instance id 用来获得轨迹 | 当前调用传 trajectory_id=session_id、instance_id；按本次身份读取 | 第 5 段 |
| 结束后不再使用环境，所以终结 | 当前生命周期退出时安排清理，成功和失败都需要考虑；后台释放可能晚于函数返回 | 第 6 段 |

上述是助手核对结果。用户已经表达主线理解，但尚未对这些精确区别逐项反馈；不能把它们全部登记为已掌握。

## 5. 如果以后采用，怎样改才不会丢内容

1. 先试读[候选稿](generate-memory-candidate.md)，重点看六段能否直接回答“输入、返回、下一步”。此时正式卡、scope、索引及进度保持现状。
2. 用户选择采用后，将当前完整卡片保存为带日期的历史参考，并重算其中的相对链接。当前候选链接到正式旧卡只是为了对照；采用时必须改指该历史参考，避免新卡自指或丢失详细解释。
3. 用确认的候选替换 generate 卡的正文。保留认可样例的栏目、用户原话、源码版本、首次接触和明确未知。
4. 将本次复述与校准写回对应形成过程，更新项目唯一进度中的事实描述。仅记录“已复述主线、这些区别待反馈”，不标记整步完成。
5. scope 的 3.1 与 3.2 继续负责全局和导航，不用本次卡片详解替换它们。03 也不因排版调整而变化。
6. 下一处可以建议 BlackboxAgentPaddock.init，只回答“环境需求怎样变成 state”；用户确认开始后才建子卡。子卡从 generate 的第 2 段进入，返回后继续第 3 段注册。

## 6. 试读时怎样判断是否改善

1. 不重新读 Slime 分派，仍能知道本函数接到什么、交回什么。
2. 沿六段能找出 state、call_payload、trajectory_payload、result 的来路与去向。
3. 能分别定位 Paddock 与 sandbox、ProxyClient 与 Proxy 服务；无需先学完它们的实现。
4. 进入一个源码入口后，知道带着什么结果回到主卡。
5. 旧解释和原话仍可回查，默认正文不用展示所有旁支。

这五项是材料的可用性检查，不是要求用户先通过复述考试才允许继续。

<a id="user-feedback"></a>

## 7. 本次原话与讨论来源

以下保留本次真实反馈；引用中的笔误和不准确表述不改写。技术核对见上面的对照表。正式记录尚未修改。

<details>
<summary>用户对现行卡片的反馈与首次主线复述（全文）</summary>

> 我清楚slime的generate and rm
> 但是这里的全都放在一个generate里面是否还是太多了?
> 虽然好像每一个部分还是比较全面的
> 但是有没有更好的办法呢?
>
> 先不要修改先给一下方法吧
>
> 我先说一下我对于blackbox dispatch的理解吧
> 1.
> 首先这里应该是通过环境image来构建一下这里的session
> 还有instance id什么的
> 也就是任务的一系列信息
>
> 2.第二部应该是先拿到这里的proxy client 也就是slime中有的adapter service中的proxy 相关的部分
> 让agent都发往这个proxy
>
> 然后才是这里的看一下是否能够获得这里的prewarm的sandbox
> 如果不恩能够够就获取一个这样子的sandbox也就是这里的paddock?
>
>  如果不是提前配置好的
> 那爱么就需要构建一下这里的这个state啊 instance啊 或者session id之类的一系列内容
> 让这个sandbox 能够清楚这里的是需要生成和发往什么id的是我的理解
>
> 3. 并且吧这个agent需要执行的内容也写在了这里
>
> 4. 最后吧这个agent要执行的部分通过call payload的方式执行
> 最后得到对应的结果是我的理解
>
> 5. 这样子这里说明了blackbox server llm proxy会发往这里的dressage proxy
> 然后这里的dressage proxy会有收集轨迹的部分
>
> 然后首位会话读取轨迹
> 然后再转换完了之后交给sample的部分
> 我在想的问题是这里的其实proxy client read trajectory如果都放在了proxy client好像也没问题?
>
> 因为所有的请求都发到那里去了?
>
> 这里通过session id还有instance id能够获得到这里的轨迹结果是我的理解
>
> 最后在推出的时候再考虑推出这里的环境部分的内容
> 因为创建的sandbox的内容就不再需要被使用了?
> 所以需要终结是我的理解

</details>

用户随后授权本次候选材料：

> 那么请给出这里 你打算修正 改进的方式吧
> 然后看一下应该怎么做?
> 则呢吗修正改进一下这个short memory 先给出可能的方案放在reference里面吧
> 不要直接修改目前的内容

<details>
<summary>方法样例、源码与本次修改边界</summary>

- 沿用[短期函数 skill](../../../../../../../../.agents/skills/repo-reading-short-term-memory/SKILL.md)、[BaseAdapter._translate](../../../../../../../../.agents/skills/repo-reading-memory/references/base-adapter-translate.md)的栏目。
- 编排段落依据 [BaseAdapter._run_turn](../../../../../../../../.agents/skills/repo-reading-short-term-memory/references/base-adapter-run-turn.md)；进入与返回依据[面包屑样例](../../../../../../../../.agents/skills/repo-reading-short-term-memory/references/breadcrumb-navigation-and-shared-infra.md)。本方案是当前卡片的试读提案，不改通用 skill。
- Dressage 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。主函数 blackbox_dispatch.py:116–412；Paddock.init/register_agent/call_agent 位于 paddock/blackbox/paddock.py:64/153/184；ProxyClient.read_trajectory 位于 proxy/proxy_client.py:115。
- 本轮仅新增本方案和完整候选稿。正式函数卡、scope、项目入口、索引、flow、03 与源码均不修改；也不预建其他函数卡。
- 静态核对调用与字段；没有运行真实环境、Agent 或训练。

</details>
