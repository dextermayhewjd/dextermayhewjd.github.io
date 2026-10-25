# MessageNode

## 1. 对象职责

消息树中的一个节点，保存一条消息、父子关系，以及可能存在的模型生成记录。它由 [TrajectoryManager](TrajectoryManager.md) 组织成每个 `sid` 的树。

本轮重点是节点怎样连成路径，读完返回 `get_trajectory`。

## 2. 字段总览

八个实例字段。“—”表示本卡尚未归纳具体用法。

| 字段 | 含义 | 已展开的用法 |
| --- | --- | --- |
| `role` | 消息角色，如 user、assistant；默认 `None` | 下方例子用于区分节点角色 |
| `message` | 消息字典；默认 `None` | 下方例子保存各节点的消息内容 |
| `metadata` | 节点附加信息字典；默认 `{}` | — |
| `parent` | 父节点；根节点为 `None` | `is_root` 判断根；`path_from_root()` 沿它向上回溯 |
| `children` | 子节点列表；初始 `[]` | `add_child()` 连接节点；`leaves()` 沿子节点寻找叶子 |
| `turn` | `TurnRecord` 生成记录，包含 token、logprob、结束原因等；初始 `None` | [组装入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L577-L600)读取带生成记录的节点；本轮先定位其职责 |
| `turn_index` | 生成轮次序号；尚未赋值时为 `None` | — |
| `response_trained` | 是否已为该节点分配过训练信号的组装标记；初始 `False` | — |

`role="assistant"` 不自动意味着 `turn` 已有生成记录。`response_trained` 是组装时的标记，不表示模型参数已经训练更新。

## 3. 根、叶子与路径

<a id="tree-example"></a>

下面仅构造节点关系，没有调用模型，也没有填入 `TurnRecord`：

```python
root = MessageNode()
user = root.add_child(MessageNode(role="user", message={"role": "user", "content": "fix"}))
a = user.add_child(MessageNode(role="assistant", message={"role": "assistant", "content": "A"}))
b = user.add_child(MessageNode(role="assistant", message={"role": "assistant", "content": "B"}))
```

```text
root
└─ user
   ├─ a
   └─ b
```

| 方法或属性 | 在这个例子中的结果 | 源码 |
| --- | --- | --- |
| `root.is_root` | `True`，因为 `parent is None` | [100–102](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L100-L102) |
| `root.leaves()` | 迭代得到节点 `a`、`b` | [119–124](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L119-L124) |
| `a.path_from_root()` | 返回节点列表 `[user, a]`，不含占位根 | [109–117](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L109-L117) |

树只有根节点时，`leaves()` 会给出根本身；`get_trajectory` 用 `is_root` 跳过它。这里得到的路径仍是一组节点，之后才交给组装函数生成样本。

读完返回 [get_trajectory 的路径遍历](../../../../functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md#trajectory-path-iteration)。

## 4. 我的直接表述（原话）

本轮问题节选：

> 更多的是一个messageNode?
> 那么需要看明白什么部分才能够理解这里的trajecotymanager的get trajectory这个function呢?

这是对所需前置对象的提问，尚无本轮独立复述；完整上下文见[前置讨论](../../../../../04-flow.md#trajectory-manager-prerequisites)。

阅读类卡后的整体反馈：

> 以及这里比较重要的是messagenode
>
> 这个message中包含了比较多的比较合理的抽象
> 等一系列内容我大概理解了

这是对节点模型的整体反馈，未据此补写逐字段的理解；完整表述见[本轮记录](../../../../../04-flow.md#get-trajectory-reorder-feedback)。

## 5. 尚不清楚

- 节点树、叶子路径和样本的对应关系，继续在 `get_trajectory` 中连接。
- 真实运行中怎样挂接、改写节点，以及共享节点怎样避免重复分配训练信号，留到相应方法再读。

## 6. 来源

<details>
<summary>源码、记录范围与验证</summary>

- 固定版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。
- [字段与节点方法](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L62-L124)、[记录生成结果时赋值](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L535-L552)、[组装时读取节点](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L554-L600)。
- 首次接触：此前在消息树与路径讨论中接触；2026-10-24 在 Step 004 首次独立建立类卡。
- 最近认识更新：2026-10-24，用户表示对 MessageNode 的整体抽象大概理解；具体字段和路径关系的认识继续按实际表述记录。
- 局部验证：从固定源码提取原始 MessageNode 类，构造上面的分叉树，核对父子关系、两片叶子、排除占位根的路径，以及未填入生成记录时 `turn is None`。没有运行轨迹组装、模型或训练。

</details>
