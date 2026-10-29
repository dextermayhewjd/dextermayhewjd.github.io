# 04 · Step 017 理解形成过程

[本步入口](README.md) · [scope](01-scope.md) · [train 函数卡](02-short-term-memory/functions/train.py/train.md)

<a id="step-017-opened"></a>

## 2026-10-29 · 用户确认开启生成训练闭环步骤

前一步用户已明确表示，大概理解把样本、配套字段和安排交给 Ray。上一轮助手据既定路线提出 Step 017：以 train.py::train 为入口，先沿 use_critic=False 路径看 51 → 67 行，再依次看完成通知、生成侧权重更新，评估只定位。原范围建议见 [Step 016 记录](../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#training-loop-next-scope)。

用户本轮明确确认：

> 好的那么开启这一个step吧

本步归入此前已规划的主题 04“训练数据与更新”。从 Step 016 的 03 + 02 合并 83 份函数／类记录与 17 份配套文件，2 份历史空白占位原样保留。只修改继承内容的相对链接，不修改原话、认识时间、源码版本或未知。split_by_dp 完整调取到本步 02，用于输入结构回顾；其余历史记录继续保留在 03。

<a id="first-reference-handoff"></a>

## 2026-10-29 · 首个观察点：同一数据列表从生成交给训练

本轮核对本地 18868a79 的 train.py:13–99、RolloutManager.generate:317–333 与 RayTrainGroup.async_train:148–167。51 行先等待生成调用返回，取得的是上一阶段形成的数据引用列表；列表内仍以 Box 保存各 DP rank 数据的 ObjectRef。67 行把同一个 rollout_data_ref 交给 actor_model.async_train；该方法返回每个训练 worker 的远程任务引用，外层 ray.get 等待训练完成。

数据引用与任务完成引用用途不同；它们的列表长度也不要求相同。这里没有展开训练 worker 怎样读取所属 DP 数据。第一段按实际两行代码与接口返回值写入 train 父卡，后面的完成通知、权重更新和评估暂留在 scope 的定位中。

本轮没有运行 Ray、生成服务或训练；图中的数据引用只是结构说明，没有真实引用编号或训练结果。用户尚未对 train 的内部关系给出个人解释，不能把同意开启记为掌握。下一处按 scope 返回 71 行，但继续深度随用户问题确定。

<a id="jd-aligned-first-reading"></a>

## 2026-10-29 · 根据再次提供的 JD 明确首读位置

用户在已开启的 Step 017 中询问从哪里开始，并再次贴出完整 JD 要求对齐。其五条职责、六条要求、四条加分项与已保存岗位正文一致；本轮未更换目标岗位，也未重新核验招聘网站。

按既定范围，首读位置保持 train.py:51 → 67。观察重点是数据引用交给训练组的接口合同、远程训练工作的提交与完成等待；必要时进入 RayTrainGroup.async_train:148–167 的 external_data=None 分支，随后返回 67 行。无需在此前重读资源创建或进入 loss / 优化器内部。

这一选择主要对应职责 2 中的任务执行封装，职责 4 与要求 1、5 的执行边界及并发工程，以及职责 5、要求 4 的强化学习训练链路。之后再按 scope 接到 71 行完成通知和 88–93 行权重更新。Ray 的异步任务接口与原生 Asyncio 分开，不用本段阅读替代岗位中其他能力或实践要求。

本轮只补明起点及目标，父函数卡仍是本步核心记录；没有新建 async_train 方法卡、开启新 Step 或运行训练。用户对实际调用的理解等待后续表述。

<a id="jd-depth-boundary"></a>

## 2026-10-29 · 用户要求按 JD 限定深度

用户再次贴出相同岗位正文，并明确要求：

> 请按照这里的内容重点分析一下 不要超出这里的要求吧

助手以 Agent 框架的接入、维护、验证与排障作为主轴，将训练视角限定为满足至少一类流程的必要理解；当前沿 RL 路线，不同时铺开预训练、SFT 与 RLHF。Step 017 保持已确认的函数与主线，但明确停止条件为数据交接、等待完成、通知与权重更新，评估只定位，不默认深入 loss、优化器或并行通信。

同时保留 JD 中不能遗漏的部分：策略与评估接入验证、原生异步与错误回收、日志/Trace 和复跑、容器/Kubernetes 实践、围绕真实需求的工程迭代。Trace 的暂缓按已有指令保留，不自动恢复；加分项不扩展成额外完整课程。该分析是依据原文的投入取舍，不声称这些能力已完成验证。

边界写入岗位对照、既有阅读计划及本步 scope，不创建新课程、步骤或函数卡。本轮不新增源码阅读或运行。

<a id="combined-foundation-audit"></a>

## 2026-10-29 · 综合已有学习材料后确定剩余范围

用户明确要求把 Learn Claude Code、Python 异步与并发、当前 Slime 阅读痕迹和已有强化学习理解合起来判断缺口，并确定剩余 Slime 范围。

本轮核对 Agent S01–S17 的正文结构与 S15、S16 的实际边界，异步课 98 项 API 的独立路线及明确的暂缓/理解反馈，CS285 Lecture 2、5、6、9、10、14，以及 Slime 的 Step 015–017 和 Trace 记录。已有内容按基础计入，不以仍有局部未知为由重开完整课程；模拟、文档检查与真实系统运行分别判断。

审查发现 Step 015 明确尚未运行插件契约验证；Skills Lab 与 Workflow demo 有模拟边界。旧岗位记录同时明确用户已有 kubectl 和简单部署经验，因此 Kubernetes 不按零基础安排。对目录外是否已有更完整排障案例的补充问题只用于核实，不因未回答而判定用户没有经验。

剩余 Slime 范围收为 A 当前训练闭环、B 已读 worker 的中断结果与背压、C 一个已有接口的小改动及复跑验证；A/B 是核心阅读，C 以执行验证为主。Trace 仍暂缓，部署案例单列，不扩展为额外底层课程。详细证据与入口保存在综合审查文件，未开启后续 Step 或执行测试。

<a id="async-train-submission-walkthrough"></a>

## 2026-10-29 · 接续第一段：训练组提交任务，主循环等待结果

用户在剩余范围确认后要求：

> 好的那么继续看一下这里的几个steps吧

本轮沿已有 Step 017 继续，不开启 B/C 或新的步骤。当前观察点是 train.py:51 → 67：上一阶段交回的是按 DP rank 组织的数据引用列表，RayTrainGroup.async_train:148–166 则遍历训练 worker 的句柄，为每个 worker 提交一次 train.remote，并返回新产生的任务引用列表。外层 ray.get 在正常路径中等待这些任务全部完成后，才接到 71 行的完成通知。

父函数卡增加了直接提交分支的真实源码、教学上拆开的两句调用，以及输入数据引用 → 各 worker 任务 → 返回任务引用列表的局部图。图中不指定实际 worker 数，不把 worker 数与 DP 分片数混同。每个 worker 都收到数据引用列表参数；怎样读取所属 DP 数据继续留在下一层，不为此展开训练后端或 Ray 调度内部。

本地 HEAD 仍为 18868a79b0b083a093798a94ed0f8cb4f71b9c14，工作区干净；只读查询官方 main 仍为 540ea919e45b8b929198abce008a103be9cfc779。核对 Ray 官方 actor 调用文档用于确认 remote / get 的接口行为，没有拉取版本、运行 Ray、模型或训练。用户尚未对两类引用的区别给出个人解释；本轮新增的是助手讲解与静态源码证据。后续按用户反馈决定是否补本段，下一交接位置仍是 train.py:71。

<a id="sample-refs-to-megatron"></a>

## 2026-10-29 · 用户复述：生成的数据引用交给 Megatron

用户原话已保存在 [train 函数卡](02-short-term-memory/functions/train.py/train.md#async-train-submission)。用户把 RolloutManager 侧获得的 Sample、Ray 引用与 Megatron 训练联系起来，并确认接下来应看 actor_model.async_train。

助手核对后确认总体方向，补充两处精确关系：首先，经 Ray 引用交付的已是 convert 整理、split_by_dp 分配后的训练数据，而非未经转换的 Sample；其次，actor_model 为 RayTrainGroup，async_train 负责向它管理的 worker 提交 train 调用。当前默认 worker 类在 actor_group.py:105–108 选为 MegatronTrainRayActor，实际 train 入口位于 slime/backends/megatron_utils/actor.py:400。取数与训练计算只定位，不展开。

当前仍停在 async_train 的提交层，不因用户确认总体来路就跳到 71 行或深读训练后端。两类引用、worker 的选择数据过程及训练计算并未获得新的理解确认。本轮为固定源码核对与保存复述，没有运行 Ray 或训练。

<a id="current-reading-location"></a>

## 2026-10-29 · 明确当前是 Step 017 的第一步

用户问：

> 我们来看一下当前的这里的这个step 我目前需要看哪一个步呢？
> 我不是特别理解

本次针对阅读位置答复：当前仍是 Step 017 中第一步“数据引用进入训练”，直接读 actor_group.py:163–166 的普通分支，理解给各 worker 提交任务与返回引用，然后回到 train.py:67。第二步完成通知、第三步权重更新、第四步评估只作后续定位。scope 顶部加入“此刻读哪里”的明确入口，保留完整骨架；没有改变范围或将任何阶段记为已掌握。


<a id="async-train-independent-card"></a>

## 2026-10-29 · 精读函数独立成卡，并在 3.2 直接标出

用户问：

> 好的 那么我第一个需要看的函数是哪一个呢？
> 是这里的哪一个函数卡片呢？
> 是否应该在3.2的部分给出这里需要我精读的核心骨架呢？

此前指向 RayTrainGroup.async_train，却让用户打开 train 父卡中的一段，函数名与卡片名没有对齐。本轮将已经展开的 async_train 提交逻辑拆成同名独立函数卡；它成为当前第一个精读入口。train 父卡保留数据来路、外层等待与后续通知，原有完整版本归档到 references/history，原话和未知继续保留。

scope 3.2 保留完整一轮骨架，以①标出当前提交调用、②标出完成通知、③标出权重更新、④标出周期评估；紧接骨架给出①的普通分支、独立卡链接和返回 train.py:67 的位置。3.3、步骤 README 与短期索引使用同一入口。当前仍在 Step 017 第一步，不将导航修正记为用户已经理解，也不展开 Megatron 训练内部或新建后续 Step。

本轮是固定源码下的文档与导航修正，没有新运行 Ray、模型或训练。卡片内容依据已有提交带读和源码证据；没有新增个人理解结论。

<a id="external-data-pairing-and-list"></a>

## 2026-10-29 · 配对分支：数量检查、for 解包和列表返回

用户开始阅读 async_train，提出 external_data 数量应与 worker 一致，并识别传入 rollout_id、rollout_data_ref；对 for actor, ed 不清楚，又问返回的是否为 list generator 或远程调用列表。完整原话保存在 [函数卡的本轮表述](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.async_train.md#external-data-pairing)。

助手补充三点：if 首先判断 external_data 是否为列表，assert 才检查额外输入数与 worker 数相等；这不是检查训练样本数与 worker 数相等。zip 按位置组成 (worker, extra) 对，actor, ed 接收每对的两项；数量检查不验证顺序。方括号列表推导式在构造列表时已经调用 remote 提交工作，最终返回普通的任务结果引用列表；它不是生成器，也不是暂未调用的函数列表。主线仍为 external_data=None，本轮配对分支是用户问题触发的局部对照，不进一步展开 critic 训练。

为核对语法，使用 Fluent Python 第 2 版的 Generator Expressions 与 Unpacking Sequences and Iterables 对齐小节，英文、官方中文原句与行号放在函数卡的折叠来源。原书基于 Python 3.10，本机 Python 3.12.3；没有把 Slime/Ray 行为归为书中结论。

另外从固定源码提取未改写的 async_train 方法，使用只记录调用并返回字符串的 remote 替身，运行列表、None、长度不等三种情形。前两者返回 list，返回前已记录两次提交；长度不等触发 AssertionError 且没有提交。结果保存在 references/async-train-pairing-local-output.json；未创建真实 Ray ObjectRef、未运行模型或训练。用户对配对、列表推导及引用用途的理解仍待反馈，不以局部运行替代掌握确认。

<a id="paired-tuple-versus-returned-reference"></a>

## 2026-10-29 · zip 元组是否进入返回列表，以及两条分支各自返回什么

用户明确将术语改为列表推导式，继续询问 actor 与 ed 是否组成 tuple 后放进返回列表，以及两条路径的差异。完整原话保存在当前 async_train 卡。

助手沿原代码指出两个位置：for actor, ed 对 zip 提供的元组解包；for 前面的 actor.train.remote(...) 才决定结果列表中的元素。因此，zip 的元组用于本轮配对，最终列表收集每次提交返回的任务结果引用。

两分支对比以相同的两名 worker 为例：列表 `[extra0, extra1]` 将每项分别交给对应 worker；非列表 None 或字典 X 则给每个 worker 传入相同的额外输入值。两条分支都返回每个 worker 一项的任务结果引用列表，各次调用的引用对象属于其各自任务。卡片中加入并排对照表，继续保留数据引用与任务引用的区别。

本轮沿用先前原方法配 recording remote 替身的局部输出，没有重复执行或启动真实 Ray、模型、训练。用户对术语的确认已记录，元组与返回结果的进一步校准仍待反馈；当前不进入训练完成通知。

<a id="worker-handle-and-result-reference"></a>

## 2026-10-29 · 共同输入之外的 ed，以及本地句柄与结果引用

用户已将已有 handler、zip 配对、拆包、remote 调用和保存 ref 连成初步理解，但继续问共享 rollout_id、rollout_data_ref 时为何需要 zip，以及“任务列表”究竟是什么。最新完整表述保存在 async_train 卡，本轮未重复保存中断重发的同一问题。

助手指出，zip 配对的是 worker 句柄与第三项 external_data=ed；前两项公共输入相同不影响每个 worker 需要不同额外输入。使用两次完整的 train.remote 调用显示这一差异，避免只反复描述 zip 的形式。

进一步将“本地 actor”精确为本地持有的远程 worker 句柄：方法提交到对应 worker 执行，本地取得用于等待该次结果的 ObjectRef。列表保存的是这些结果引用，“任务列表”只是容易混淆的简称。当前 actor 的 train 正常返回 None，外层 ray.get 对两个结果引用取值时得到 [None, None]，但已经等到对应训练调用完成；具体训练仍发生在 worker 内部。

没有新增运行或改读后端计算，继续使用固定源码与先前局部替身记录。用户对最后两处精确关系的理解待反馈，未推进到完成通知或权重更新。


<a id="python-knowledge-gap"></a>

## 2026-10-29 · 判断当前需要补的 Python / Ray 概念

用户询问是否因为 Python 某些知识不清楚而卡住，并明确表示拆包与 list operator 已理解。原话保存在 async_train 卡。本轮沿前文语境将其记录为拆包和列表推导式已理解，不继续重复讲这两项，也不从一个框架调用的疑问推断整体 Python 基础不足。

助手结合当前追问，建议将前置问题拆为两个：一是工作、异步结果对象与最终结果值的区别；二是本地持有的远程句柄与 worker 实例、执行进程的区别。前者可用已有 20.3 / 20.4 的 Future 教学补清，后者是 Ray 的库接口与远程执行模型，不应混同为 Python 语法。ObjectRef 与 asyncio.Future 只类比共同用途，不视为同一种类型。

核对现有课程与已读 make_done_cb 的 Task/result 场景后，在函数卡中加入最小回查入口。此处仅提出局部学习建议，没有切换独立异步课进度、开启新 Step、运行例子或把建议写成已掌握。


<a id="future-object-versus-value"></a>

## 2026-10-29 · Future 代表结果，当前返回的是结果引用列表

用户尝试把 Future 理解为异步结果，并把它对应到 actor.train.remote 的返回内容；原话保存在 async_train 卡。助手沿该方向仅校准一个区别：Future / ObjectRef 是代表结果、用于等待与读取的对象，最终结果值另行取得。当前 remote 返回 ObjectRef，async_train 收集引用列表，ray.get 等待并取得远程调用的实际结果；正常 actor 路径中实际值为 None。

这里的 ObjectRef 与 asyncio.Future 仅在用途上类比，未将两种类型混为一谈。沿用已核对源码，没有新运行或切换阅读步骤；对象与实际值的精确区分待用户反馈。


<a id="training-completed-reading"></a>

## 2026-10-29 · async_train 有总体理解反馈，接续第二步完成通知

用户明确表示：

> 好的 我现在大概理解这里的async train了 让我们继续吧

据此将第一步记为已有总体理解反馈，不扩展为全部后端计算或失败分支已掌握。沿本步已确认的四段骨架继续到 train.py:71，建立 RolloutManager.training_completed 卡片；scope 3.2、3.3、步骤入口和短期索引同步标出②，保持完整骨架。

本轮核对：训练已在 67 行等待成功，71 行是后续完成通知；管理器将 rollout_id 转交给 BatchBuilder.training_completed。默认 object-store、无恢复的正常路径下 raw_ref=None，begin 将 batch_id 置为 None，完成通知直接结束。存在批次时才验证 rollout_id 并调用 controller.finish_batch。该入口允许需要批次生命周期管理的路径收尾；不等于再次训练、保存联合 checkpoint 或更新生成侧权重。

BatchBuilder 的直接短分支附在当前方法卡中，不继续下钻 controller 或持久化存储。读完返回 train.py:71，下一处为 88–93 的权重交接。当前完成通知的理解待用户反馈；本轮仅静态核对，没有新增运行。

<a id="completion-id-matching"></a>

## 2026-10-29 · 完成通知比较的是哪两个编号

用户已定位到 rollout_manager.training_completed.remote(rollout_id)，问是否按 rollout_id 判断和本地的是同一个。原话保存在当前方法卡。

本轮从参数来源补齐关系：主循环的 rollout_id 先传入 RolloutManager.generate；生成开始时，管理器在 319–320 行把该值保存在自身和 BatchBuilder 的 rollout_id 字段。训练结束后，同一轮编号作为参数传入 training_completed，再由 BatchBuilder 与其保存的 self.rollout_id 比较。这里 self 指 BatchBuilder；比较轮次一致性，不是机器位置或 GPU 编号。

检查只在 batch_id 不为 None 时执行。以第 7 轮为静态例子：通知 7、记录 7 时继续，通知 6、记录 7 时抛错；通过后实际交给 finish_batch 的是批次记录编号 batch_id。默认 object-store 正常路径下 batch_id=None，连编号比较也跳过，直接到函数末尾。

本轮没有运行新实验或进入 controller；解释与例子来自固定源码，理解待用户反馈。当前仍在第二步，不推进权重更新。


<a id="completion-minimal-model"></a>

## 2026-10-29 · 收敛完成通知的心智模型

用户表示目前只希望建立简单心智模型，继续问轮次判断之后做什么。原话保存在 training_completed 卡。助手将说明收敛为“训练侧已用完这批数据，通知数据管理侧收尾”；轮次检查防止确认错批次，有批次记录时登记完成并释放对应队列额度，无记录时直接结束。随后回到主循环，后续权重更新属于下一段。

保留前面的编号来源和分支代码作回查，不继续展开内部实现。此简化解释尚待用户反馈；没有新运行或新步骤。

<a id="implemented-but-not-triggered"></a>

## 2026-10-29 · 区分默认未调用与功能尚未实现

用户问当前应保留什么心智模型，并表示先前说明听起来像代码尚未实现，询问是否需要继续读 controller.finish_batch。原话已保存到 training_completed 卡。

为排除“占位实现”的误解，本轮只读核对 RolloutQueueController.finish_batch:814–827：检查已有就绪批次，推进消费位置，从未完成批次列表移除该批次并保存状态。没有继续追踪 _advance、状态存储或回收实现。由此把心智模型明确成两个路径：默认 batch_id=None，通知直接返回；队列路径已有批次时，核对轮次并调用已实现的完成登记。

此前讲解未充分区分功能的存在与当前配置的触发情况。当前按用户希望的简单模型，读到入口职责即可；后续应回 train.py 的权重交接，不自动增加队列内部专题。此处为阅读深度建议，未将用户记为已理解；没有新运行。


<a id="finish-batch-stop-at-responsibility"></a>

## 2026-10-29 · 用户停止下钻，保留更新批次管理状态的职责

用户尝试描述 training lock、ready、task、receipt 和 state，随后明确“算了还是不继续精读了吧”，希望只知道该方法得知批次已完成并修改管理状态。完整表述已保存在当前方法卡；这次停止决定优先于消息开头试图继续读的提议。

助手仅校准职责：训练方已经等待训练完成，再发出通知；finish_batch 据此更新管理记录，使该批次不再列为未完成。它不自行监测 GPU 训练进度。用户关于内部字段的猜测继续保留为疑问，没有标记为已理解，也不新增这些实现的函数卡或研究步骤。下一处仍可回主循环的权重交接，当前没有展开。


<a id="completion-evidence-and-next-entry"></a>

## 2026-10-29 · 补出状态变化的直接依据，推荐下一处权重交接

用户追问“从未完成批次列表移除、保存状态”的依据，同时表示先假设该更新完成，询问下一步。当前方法卡补出 queue_data_source.py:824–825 的真实语句：过滤掉当前 ready_ref 对应的记录，再调用 _save_training_state。815 行的 docstring 作为列表含义的旁证；这不等于已验证样本文件删除。

下一处推荐沿既有③：从 train.py:89 的 actor_model.update_weights 进入 RayTrainGroup.update_weights:178，先看训练侧新权重怎样交回生成侧，再回查外层 88、92–93 行的暂停接纳与按条件恢复。不展开通信、磁盘重载或 Megatron 内部，也不因推荐而创建新 Step 或填写理解完成记录。本轮没有新运行。


<a id="pause-before-weight-update"></a>

## 2026-10-29 · 第三段先暂停接纳，再以权重更新为精读重点

用户指出：

> 然后下一步不是这里的paused吗？
> 虽然应该也很好理解
> 就是原有的rollout部分不再接受新的请求应该是这个意思对吧
> actor model 更新权重我们先看这一步吗？

执行顺序确实先到 train.py:88 的 pause_rollout_admission，再到 89 行 update_weights。此前“先读 update_weights”是按核心动作选精读入口，不能误写成真实执行时跳过暂停。本轮把第三段连成 pause → update → 条件恢复，暂停的直接接口在父卡解释，更新方法独立成卡。

暂停针对注册的 fully_async producer 的新任务接纳，调用 pause(drain=False)，不在此直接取消全部在途生成。was_paused 保存调用前状态，后面只有原先未暂停且还存在下一轮时才恢复；不存在该 consumer 时返回 True。局部与分布式 producer 的接口只用于核对该含义，不重读完整 worker。

当前更新只选非全量磁盘分支：给每个训练 worker 提交 update_weights.remote，并在训练组方法内部用 ray.get 等待，然后返回 None。Megatron worker 取得生成引擎并委派给 weight_updater，后续通信、存储和在途生成收束未展开。用户尚无对更新方法的理解反馈，本轮没有新运行。


<a id="weight-sync-participants"></a>

## 2026-10-29 · “所有 actor 更新权重”的范围与方向

用户将 update_weights 概括为所有 actor 开始更新当前权重。助手依据 self._actor_handlers 的遍历限定范围为当前训练组的 worker；不推广到作业内所有 Ray actor。结合后端的生成引擎和 weight_updater 调用，说明这里发布训练后的权重到生成侧，参数的训练更新已经发生在此前训练阶段。

本方法通过 ray.get 等待每个 worker 的更新调用结束；用户对范围、同步方向与等待的精确理解待反馈。没有继续进入通信实现或新运行。


<a id="training-finished-before-weight-sync"></a>

## 2026-10-29 · 本轮训练计算先完成，再同步给生成侧

用户将此处理解为现有 rollout 引擎用上新参数，并询问两侧是否都停下来，还是训练侧已完成而只需同步。原话保存在 update_weights 卡。

本轮依据 train.py:67、88、89、92–93 的先后关系，说明训练计算先完成，新权重已在训练侧；之后暂停新 rollout 接纳，训练 worker 参与同步，主循环等待完成后再按条件恢复接纳和进入下一轮。训练进程并非在此被停止。

pause(drain=False) 不等于所有在途生成已结束；实际安装权重的引擎同步机制继续留白，没有为解释当前时序而展开权重更新器。没有新增运行或新的学习步骤，理解待反馈。

<a id="weight-sync-state-card-and-next"></a>

## 2026-10-29 · 保存两侧状态，确定下一观察点

用户要求“记得把这里的内容写清楚放在这个函数卡片里面吧，然后考虑下一步”。本轮在 RayTrainGroup.update_weights 卡片中整理两侧状态对照：训练侧计算已完成但 worker 仍参与同步，主循环等待；rollout 后台暂停新接纳，已有生成引擎接收权重，不能由此推断所有在途请求已结束。

按既有第三段范围，下一观察点推荐回到 train.py:92–93，再按需查看 RolloutManager.resume_rollout_admission:156–158，弄清“还有下一轮”与“原先是否暂停”这两个条件。保持父卡中的恢复入口，不新建调度主题或提前进入周期评估。

本轮核对现有函数卡整体格式、代码来源与链接；没有运行权重同步或创建新的完成记录。保存内容与用户已掌握的范围分开，恢复条件尚待带读。
