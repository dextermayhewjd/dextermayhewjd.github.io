# 00 全景 Walkthrough：源码与材料边界

本次新增的启动和上层调用关系按 Slime 提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 静态核对。已有职责表与单任务阅读骨架保留其原先 `22a89f96835969a47055a659c588f46151f8b07a` 来源；未把旧链接批量换成当前提交，也未重新执行旧版本。正文、图和此记录都不表示实际运行过 Agent、沙箱、模型服务、训练或集群。

| 编号 | 核对事实 | 调用处与定义处 | 方式与结果 |
| --- | --- | --- | --- |
| C01 | 主入口先准备或接续 rollout 组件，再进入 train；启动和退出责任留在 main | [train.py:103](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/train.py#L103)、[create_rollout_manager:293](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/ray/placement_group.py#L293) | 阅读调用处与实现；不是所有组件都在每次运行重新创建 |
| C02 | train 请求本轮 rollout 数据，再把返回引用交给训练组，随后确认数据进度并更新权重 | [train.py:13](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/train.py#L13)、[RolloutManager.generate:303](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/ray/rollout.py#L303)、[BatchBuilder.convert:237](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/batch_builder.py#L237) | 阅读正常路径；未将一个任务、一个样本或一个优化器步当成同一粒度 |
| C03 | 默认 rollout 的单样本接入点选择并等待自定义生成函数；Coding Agent 返回评测结果或训练 Sample 列表 | [generate_and_rm:289](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L289)、[Coding Agent generate:182](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L182) | 阅读函数选择、参数、await 与两个结果分支；正文导航是职责摘要，不是可执行替代实现 |
| C04 | CLI 推进工具循环；Adapter 请求 SGLang 并记录模型采样，任务收尾再独立评分并导出 | [BaseAdapter._run_turn:318](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L318)、[finish_session:245](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L245)、[Sample:107](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/types.py#L107) | 与当前源码对照；仅聊天记录加评分不自动满足 token、mask、logprob 的训练合同 |

## 图与讲解的身份

- `framework-map.svg` 是本次按上述关系绘制的教学图。上层画数据交接，下层按 main 的执行推进定位调用；工厂返回后由主入口继续，不表示工厂直接调用后面的每个组件。
- “基础骨架 → 新需求 → 展开机制”表示阅读层次。没有 Git 历史证据，不将它写成 Slime 当初的开发过程。
- 2026-10-19 按用户纠正调整开头与图中文字：基本框架从整体工作建立，不以已读 `generate()` 为起点；回顾信息只在进入该局部时使用。通用方法和逐步模型记录移到仓库根目录 `00-repo-reading/`。
- 正文中的技术问题来自已经发生的讨论；当前解释可继续修订。没有把助手提供的解释代写成用户已经记住、接受或独立复述的事实。
- 已有单任务图文保持原来源；本次新增部分只把它接回框架入口，不重做全部历史摘录核验。

## 官方概念对照

- [整体实验流程](https://thudm.github.io/slime/get_started/experiment-guide.html#the-loop-you-are-building)：生成、评分、批次或队列、训练、权重同步。
- [Agent 工作流接入](https://thudm.github.io/slime/get_started/agent.html)：自定义生成、评分与协议 Adapter。

这些文档是概念和接口说明，实际函数、行号与本页证据以上述固定提交为准。
