# Step 016 · Sample 怎样成为训练数据

[主题入口](../../README.md) · [前一步](../step-015-custom-generate-contract/README.md) · [唯一进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

用户在确认这是下一 Step 后要求：“好的 那么继续吧 看一下这些结果到底是怎么整理成训练需要的数据的？”本步以 `BatchBuilder.convert` 为核心，跟随生成、评分和收集之后的 Sample，观察它如何成为训练侧使用的数据。

**本步问题：一组带有 token 和评分的 Sample，如何整理成 `train_data`；哪些字段直接汇总，哪些需要补充或处理？**

## 从哪里读

1. [01 · scope](01-scope.md#reading-order)：整体位置、默认转换骨架和固定阅读编号。
2. [02 · 短期记忆](02-short-term-memory/overview.md)：转换、奖励后处理、DP 交接方法卡，以及调取的完整 Sample 类卡；其中 [build_dp_schedule 独立函数卡：源码骨架与输入输出](02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md#schedule-flow)保存调度输入、约束、主干和输出。Manager 交接卡保留为背景。
3. [03 · 前序记录](03-long-term-memory/overview.md)：完整继承 Step 015 的 03 + 02，共 78 份函数／类记录、17 份配套文件，保留 2 份历史空白占位。
4. [04 · 理解形成过程](04-flow.md)：范围确认、首个观察点及证据边界。

本步首个观察点是 [278–288 行的字段组装](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md#field-assembly)：输入按 Sample 组织，输出按字段组织。先看清这次结构变化，再读 mask 和奖励后处理。此前的 [Manager 回查](01-scope.md#manager-handoff)保留为折叠背景，本轮直接从 data 目录中的 convert 继续。

## 本步证据与边界

- 源码固定为本地 Slime `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[版本与源码片段](references/source-evidence.json)。
- [小例子的完整输出](references/convert-example-output.json)来自固定源码方法的隔离执行，使用真实 Sample 类与构造数据；没有运行模型、Ray actor 或训练，没有执行前一步的契约测试。
- [DP 调度例子的输出](references/dp-schedule-example-output.json)来自两个原始函数体的隔离执行：两份样本、两个 rank、固定小批次、关闭负载均衡；[函数卡](02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md#two-sample-example)解释四项安排如何接回 split_by_dp。该运行不包含 split_by_dp 或训练。
- 例子关闭奖励归一化、使用默认转换，不将该配置当作所有作业的默认配置。
- [继承清单](references/inheritance-manifest.json)保留来源与哈希；[调取清单](references/active-retrieval.json)记录 Sample 卡的使用。
- 首轮读到 `convert` 返回字典；后续按用户确认简读 `split_by_dp` 的字段分配与返回引用，并用 `build_dp_schedule` 的固定配置补清索引来源。动态装箱、负载均衡、训练算法、张量打包、持久化和 Trace 内部继续留在边界外；不处理 Hugo。

源码核对与材料建立不代表用户已理解整个转换。本步暂不生成完成总结。

后续已按用户确认开启 [Step 017 · 生成训练闭环](../../../04-training-data-updates/steps/step-017-generation-training-loop/README.md)，承接本步的数据引用；本步原有源码与理解记录保留。
