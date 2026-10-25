# TrajectoryManager

## 1. 对象职责

按 `sid` 管理多棵消息树，接收逐轮记录，并在导出时把消息路径交给组装逻辑，汇总为 `Sample` 列表。

它由 [BaseAdapter](../adapters/common.py/BaseAdapter.md) 持有；树中的节点是 [MessageNode](MessageNode.md)。

## 2. 字段总览

三个实例字段。“—”表示本卡尚未归纳具体用法。

| 字段 | 含义 | 已展开的用法 |
| --- | --- | --- |
| `_trees` | `sid → MessageNode` 根节点；初始 `{}` | [record_turn](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L398-L403)取得或建立根节点；[get_trajectory](../../../../functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)取树，正常导出后移除 |
| `_turn_count` | `sid → 已记录的生成轮次`；初始 `{}` | [get_trajectory](../../../../functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)正常导出后移除该 sid 的计数 |
| `_fork_threshold` | 改写合并与样本组装使用的阈值；未指定时为 `1024` | — |

## 3. 读 get_trajectory 前接清什么

```text
adapter.manager -> TrajectoryManager instance
manager._trees[sid] -> root (MessageNode) -> message tree
```

- `_trees[sid]` 是整棵树的根节点，不是现成的样本列表。已有轨迹来自此前的 `record_turn`。
- 从根节点枚举叶子，再从叶子取得一条消息路径；节点和路径的形态见 [MessageNode 的小例子](MessageNode.md#tree-example)。
- 回到 [get_trajectory](../../../../functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)：取树 → 取路径 → 委托组装 → 汇总与赋奖励 → 移除记录并返回。`_chain_to_samples` 先按“节点路径 → 样本列表”的接口理解。

## 4. 我的直接表述（原话）

本轮关于阅读入口的提问节选：

> 是否应该考虑考虑先理清楚trajectory manager呢?
> 是否需要单独看一下呢?

尚无对本类职责的独立复述；完整问题见[本次前置讨论](../../../../../../step-004-trajectory-to-samples/04-flow.md#trajectory-manager-prerequisites)。

随后用户给出整体认识：

> 好的我大概理解了 也就是这里的trajecotry的内容更多的就是这里的sessionid
> 还有这里的turn count
> 还有for threshold

已辨认出按会话组织、轮次计数与阈值这几部分；其中 `_trees` 保存的是 `sid → 根节点`，这一对应由助手据源码明确，保留后续核对。完整表述见[本轮反馈](../../../../../../step-004-trajectory-to-samples/04-flow.md#get-trajectory-reorder-feedback)。

## 5. 尚不清楚

- 消息树、节点路径与最终样本列表之间的区别，待结合 `get_trajectory` 继续说明。
- `_fork_threshold` 的具体判定规则、压缩与改写如何影响组装，留待对应算法展开。

## 6. 来源

<details>
<summary>源码、记录范围与验证</summary>

- 固定版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本机 `/home/fredkeira/projects/slime`。
- [初始化与公开方法](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L367-L446)、[改写判定与组装入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L510-L600)。
- 首次接触：此前经 `record_turn`、`get_trajectory` 接触；2026-10-24 在 Step 004 首次独立建立类卡。
- 最近认识更新：2026-10-24，用户表示大概理解，并列出会话标识、轮次计数与阈值；完整数据结构与各字段的使用仍按后续表述核对。
- 本页只建立字段与交接概要；实际方法过程仍以对应方法卡为主。

</details>
