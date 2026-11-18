# Trajectory Management：源码核对记录

## 固定依据

- 源码仓库：`/home/fredkeira/projects/slime`，核心包 `slime/`。
- 固定提交：`22a89f96835969a47055a659c588f46151f8b07a`。
- 核对日期：2026-10-11。
- 核对方式：静态读取调用处、定义与现有测试断言；核对相关文件与该提交的 Git blob。
- 未更新源码，也未重新判断官方 main 的最新版本；本专题沿用已确认的固定阅读快照。
- 主工作区已有未跟踪阅读文件，保留原样；本专题写入网站仓库的 `slime_photo`。

## C01 · 一次请求如何进入轨迹管理

| 角色 | 固定源码入口 | 核对事实 |
| --- | --- | --- |
| 调用处 | [adapters/common.py:384](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L384) | `_run_turn()` 传入 sid、TurnRecord、转换后的历史、助手消息和 metadata |
| 实现处 | [trajectory.py:283](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L283) | `record_turn()` 匹配、尝试合并、挂载消息并保存本轮生成 |

## C02 · 历史匹配与分支

| 入口 | 核对事实 |
| --- | --- |
| [_find_mount_point:352](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L352) | role 和消息字典相等时沿已有子节点继续；返回节点与匹配深度 |
| [_mount_prompt_messages:428](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L428) | 把未匹配的输入消息挂成节点 |
| [_attach_assistant_leaf:437](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L437) | 保存 TurnRecord 和会话内 turn_index；不是 task 依赖图 |
| [分支测试:402](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_trajectory_manager_branching.py#L402) | 正常多轮与用户消息分支测试分别位于 402、441 行 |

## C03 · assistant 改写合并

| 入口 | 核对事实 |
| --- | --- |
| [_try_merge_assistant_rewrite:370](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L370) | 只在特定结构及原回应长度条件下合并；清除 turn/turn_index，记录 merged_rewrite |
| [短改写测试:888](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_trajectory_manager_branching.py#L888) | 原输出不再训练，后续输出继续训练 |
| [歧义测试:955](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_trajectory_manager_branching.py#L955) | 多候选时不猜测目标，保留分叉 |

## C04 · token 对齐与训练导出

| 入口 | 核对事实 |
| --- | --- |
| [classify_token_drift:169](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L169) | CLEAN / REALIGN / FORK；REALIGN 的长度门槛比较本次 output_ids 长度 |
| [_split_chain_into_builders:456](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L456) | 用 response_trained 避免共享生成节点重复训练 |
| [_SampleBuilder.to_sample:234](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L234) | 继承 rollout_id；返回对齐的 tokens、response_length、mask 与 logprob |
| [get_trajectory:307](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L307) | 每个 Sample 获得完整 outcome reward，随后消费会话树 |
| [finish_session:245](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L245) | 先关闭并等待在途请求，再导出与填充文本 response |

## 验证与边界

- README 的树和字母消息是人工构造的说明案例，不冒充真实模型输出。
- 现有测试在本文中作为阅读材料引用；本次没有重新运行整个 Slime 测试集。
- 不根据消息分叉自动标注压缩／子 agent／teams，不把调用记录顺序当作任务依赖。
- 这份笔记没有给现有章节标记“已学完”；不改动原有 4.1 讲解、图或源码快照。
- 网站阅读页位于 `content/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/trajectory-management/index.md`；通过 shortcode 直接渲染本目录 README，发布相同内容的 Markdown 和源码核对记录下载，不维护第二份正文。
