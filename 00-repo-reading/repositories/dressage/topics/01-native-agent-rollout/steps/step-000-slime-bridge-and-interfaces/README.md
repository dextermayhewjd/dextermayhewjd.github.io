# Step 000 · 黑盒任务如何交回训练样本

[项目目标与当前接续](../../../../README.md) · [后续学习指南](../../../../references/design-on-slime.md#reading-guide) · [下一阅读单元：Step 001 身份与参数](../step-001-task-identity-and-parameters/01-scope.md)

本步从 blackbox_dispatch.generate 建立单条黑盒 rollout 的整体交接：环境准备、注册与执行、读取轨迹、转换样本、安排回收。详细函数卡保留作回查；本步的阅读边界是知道主要阶段怎样接起来，不要求深入所有子函数。

## 从这里开始

1. [scope 3.1](01-scope.md#whole-flow)保留系统全景，标注 Step 000 的整体范围。
2. [scope 3.2](01-scope.md#reading-navigation)按六段组织 generate 的内部阅读顺序。
3. 环境准备的具体问题在 [Step 004（原 001）](../step-004-paddock-environment-preparation/01-scope.md)接续，那里以本步展开的 generate 作为上层背景。

| 材料 | 用途 |
| --- | --- |
| [01 · scope](01-scope.md) | 整体阅读的问题、位置、顺序与停止条件 |
| [02 · 函数索引](02-short-term-memory/overview.md) | 仅保留 generate；init 早期版本已归档，当前记录在 Step 004 |
| [03 · 前序函数索引](03-long-term-memory/overview.md) | Step 000 暂无前序继承 |
| [04 · 实际讨论](04-flow.md) | 用户复述、范围调整及真实接触顺序 |

源码基准为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。用户已复述 generate 主线，具体对象区别与 init 实现仍需继续确认。此次分步保留原有学习事实，不标记全部机制已掌握；未运行真实 rollout 或训练。
