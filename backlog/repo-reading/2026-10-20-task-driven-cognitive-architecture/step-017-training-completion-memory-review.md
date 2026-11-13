# Step 017 · training_completed 短期记忆审阅

[讨论入口](README.md) · [原函数卡](../../../00-repo-reading/repositories/slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md) · [阅读版对照稿](../../../00-repo-reading/repositories/slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/references/training-completed-card-proposal.md)

## 1. 本轮问题与判断

用户既希望简单下潜到 RolloutQueueController，也质疑 RolloutManager.training_completed 的 short-term memory 是否足够清晰，要求从认知和资深工程人员的阅读方式评估。

判断：**有必要轻量查看 finish_batch 的状态变化，但不需要通读控制器；当前卡片需要重新组织，而不是继续在末尾追加解释。** 重点是用一个明确前提的场景，把通知与可见变化连接起来。

## 2. 当前卡片的具体问题

本轮检查时卡片共 239 行，个人原话从第 132 行开始。长度本身不决定好坏；问题在于读者在看到一组完整前后变化之前，需要反复切换以下信息。

| 现象 | 对这次阅读的影响 | 候选调整 |
| --- | --- | --- |
| 调用方等待、管理器转交、批次判断、控制器效果散在不同小节 | 容易记住方法名字，却记不住一条因果关系 | 先放前提和一个职责模型，再用三行责任表连接各层 |
| 默认无批次路径与有批次的机制说明多次交替 | 用户容易把“本次直接返回”理解成“这个功能没有实际作用” | 先用一张表分清两种前提，再明确只展开有批次的对照场景 |
| “释放”“停掉”“完成”等说法反复校准，但缺少稳定的状态对照 | 容易把登记状态、训练进程、未完成生成任务合为一类 | 展示 `state["batches"]` 的 ref_A/ref_B 前后变化，说明它是训练数据登记 |
| 澄清正文与历史问题都默认展开 | 每次回看要重复筛选当前结论与历史说法 | 保留全部原话和来源，默认折叠历史；阅读正文只保留一套解释 |
| 部分当前源码链接仍指向本机不存在的 /home/hongshi 路径 | 跳转失败会打断核对 | 候选稿使用固定版本链接和已核对的当前本机入口，不改写历史版本归属 |

## 3. 从认知与工程阅读目标看

这里采用的是设计推断，不是用公司名为某一种笔记格式背书，也不是声称已验证学习效果。

- **降低无关的来回查找**：让代码、它改变的状态及解释靠近，读者无需在几个分散段落中拼接。对应本库已保存的[邻近呈现与注意提示讨论](discussion.md#step011-code-markers-nearby-explanations)。
- **建立可恢复的整体单元**：以“训练已结束 → 通知数据侧 → 完成该批消费登记”作为一个单元，再挂上三个方法的位置。既有知识块取决于读者的经验，不能假设看到委派代码就自然懂其用途。
- **用具体对照约束抽象词**：用同一个 A 批次的前后状态解释“收尾”；保留 B 的登记和 C 的生成任务，以显示变化边界。对照用于理解，不冒充运行证据。
- **面向维护者的信息**：先说明调用前提、成功返回后改变什么、错误时不做什么，以及到哪里核对实现。这比要求逐个记住所有辅助函数更有助于定位一次实际需求或故障。

已有研究参考：Chandler 与 Sweller（1992）关于整合相互参照的信息与学习负担的研究，见[出版方摘要](https://bpspsychub.onlinelibrary.wiley.com/doi/abs/10.1111/j.2044-8279.1992.tb01017.x)；Mayer 与 Moreno（2003）关于相关信息邻近、提示与减少额外处理的讨论，见[既有资料](https://carpentries.github.io/instructor-training/files/papers/mayer-reduce-cognitive-load-2003.pdf)。工程写作参考为 [Google 代码示例指南](https://developers.google.com/style/code-samples)。本轮沿用已有记录中的参考，不声称重新核验了网页或这些研究直接验证了本函数卡片。

## 4. 下潜范围与记录单位

只看 RolloutQueueController.finish_batch，而不是整个类。用 `_training_state` 确认 state 是消费进度与未完成登记；集中观察 `_advance`、过滤 `state["batches"]`、`_save_training_state` 三项变化。锁、租约、codec、GC、存储协议不列为本轮必读。

这次三个方法共同说明一个完成通知的效果，因此先在同一父卡中放局部机制即可，不强制每层都新建卡。若后续真的独立研究控制器的消费进度、重放或回收，再拆出对应记录。此安排依据短期 memory skill 对“仅为当前入口服务的辅助函数”的规则，不改变函数记录整体结构。

## 5. 候选稿与状态

[对照稿](../../../00-repo-reading/repositories/slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/references/training-completed-card-proposal.md)保留原栏目、完整个人记录、未知与来源。第一版按场景和状态对照组织；用户指出缺少层级后，当前版改为编号调用层与局部处理阶段，见第 6 节。

本轮完成的是审阅和具体候选稿；正式卡片主体尚未被替换，旧记录不删除，不把用户要求改进格式当作已经理解技术机制。反馈重点是能否迅速找到“哪个状态变化、为何需要通知、哪些任务不受本方法处理”，而不是候选稿字数是否更少。

<a id="numbered-breadcrumb-revision"></a>

## 6. 用户要求编号层次和下潜面包屑后的修订

用户原话：

> 这个reference1不行 我觉得需要需要有层次
> 以及代码是怎么下潜的 需要面包屑 分论点以及通过数字的方式 给出类似于3.1 这种或者3.1.1 如果有必要的话

现已修改同一份对照稿：3.1 为 RolloutManager 转交，3.2 为 BatchBuilder 核对，3.3 为 RolloutQueueController 完成登记；3.3.1–3.3.3 对应控制器函数内部的查找验证、取得状态、更新保存；3.4 说明逐层返回。每层先标明当前面包屑与该层论点，再给源码和说明，最后连接下潜或返回位置。

编号用于表达阅读层次：3.1–3.3 跟随真实调用，3.3 的子编号只是同一个方法的内部阶段，不把每个阶段都说成一次新函数下钻。保留连续的完整 finish_batch 方法，并让子节与代码中的阶段标记一一对应。

这是对当前 reference 的明确格式修正，不改写用户技术理解。原正式卡片仍保留；第一版候选已归档至其 references/history，当前链接继续指向修订版。

## 7. 2026-10-31：用图逐层展开同一个职责框

用户进一步希望像阅读代码骨架一样，通过图的递进理解 training_completed。当前对照稿在 2.3 下增加三层图：先看已训练完的数据怎样交给数据侧登记，再打开三个对象的委派关系，最后展开 Controller 的消费与批次记录变化。三个层次保持同一件事的语义，不把表示层次当作新的执行步骤。

图中特别把“训练已完成”留在调用前，并区分无登记批次的直接返回，避免将已完成训练的事实误当成 training_completed 内部判断出的结果。图示与已有 3.1–3.4 的源码下潜导航互相补充；展示已落盘，效果仍待实际阅读反馈，不改写个人理解状态。

<a id="pseudocode-inline-comments-v2"></a>

## 8. 2026-10-31：第二版改用伪代码和同行注释

用户对图示反馈：

> 我觉得可以 但是有没有更加好一点的方法?
> 不可以用伪代码的方式来写吗? 这个图占比太大
> 不过内容和结构是清晰的
> 请给出第二版本方案

在第二版准备期间继续要求：

> 旁边能否直接放一下对应的注释呢?
> 直接看代码我还需要再读一遍

已单独建立[第二版：紧凑伪代码与同行注释](../../../00-repo-reading/repositories/slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/references/training-completed-mental-model-v2.md)，保留第一版“整体职责 → 对象分工 → 状态变化”的三层和 2.3.1–2.3.3 编号。第一层保留真实调用，第二层用缩进表示调用下潜，第三层用关键源码名称及明确标注的伪语句表达状态变化；每行作用直接写在旁边，长调用换行，删除代码后的重复解释。

第二版继续保留无批次早返回、轮次不符报错、等待 controller 完成，以及返回 None 的边界；自然语言伪语句不是新造的源码接口。第一版图示仍可对照，原话与历史在原记录中保留。用户认可的是内容和组织结构，不据此标记所有机制已掌握。

用户随后补充：逐行旁注之外，希望代码下方再简单说明整段逻辑。第二版现采用“同行注释解释局部语句，段后短段落说明整段完成什么”的组合；段后说明不重复逐行翻译，而是把动作连成目的与结果，重点补清 Controller 的消费登记职责。

<a id="final-v2-before-merge"></a>

## 9. 2026-10-31：选用第二版，先形成完整最终候选

用户要求：

> 好的那么使用这里的第二版吧 但是合并之前先出一个最终版本吧

已将第二版主体整理为[完整最终候选](../../../00-repo-reading/repositories/slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/references/training-completed-card-final-v2.md)：保留三层伪代码、同行注释和每层的整体说明；补齐定位、四项 LLM 说明、输入输出、全部个人记录、未知和来源。主读部分不再叠加第一版大图和重复的完整实现讲解，第一版与第二版原型继续作为历史对照。

原函数卡的锚点在候选中保留，历史链接按候选位置重新计算；合并时仍须按正式位置转换相对路径。当前只生成最终候选，没有修改正式卡片、长期记忆或技术掌握状态。

## 10. 2026-10-31：用户确认后采用第二版

用户已用自己的话概括分层转交与消费登记，并明确要求替换对应的正式 short-term memory。现已将第二版完整定稿采用到正式函数卡，合并前旧卡完整归档，原话、未知、来源与旧锚点保留，链接按正式目录重算。

本轮额外校准了“回收”的含义：移除未完成批次登记与实际文件回收是两个层次，后者受可选 GC 条件约束。这一说明不替代用户原话，也不扩展为已经掌握底层存储回收。采用过程见[技术阅读记录](../../../00-repo-reading/repositories/slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/04-flow.md#training-completed-v2-adopted-20261031)。

## 11. 2026-10-31：同一格式用于 pause_rollout_admission

用户明确要求参照已采用的 training_completed，完成暂停接纳的短期记忆构建。本轮将同一套分层伪代码、同行注释与段后整体说明应用到已有暂停卡，同时保留原话、未知、旧锚点与完整旧稿。针对该调用跨线程协作的特点，第三层按写请求、后台响应、等待返回组织，明确阅读顺序是因果关系而非连续调用 _loop。具体落地见[暂停卡片](../../../00-repo-reading/repositories/slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.pause_rollout_admission.md#mental-model)。

## 12. 2026-10-31：同一格式用于 update_weights

用户要求按此前函数格式整理 update_weights，现已应用三层伪代码、同行注释、段后整体说明和输入输出对照。主线保留普通分支的提交与内部等待，具体 backend 作为用途边界；此前磁盘分支放入折叠对照。原话、未知、固定源码和旧锚点保留，旧稿完整归档，不把形式统一变成扩大源码阅读范围。
