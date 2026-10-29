# RolloutManager._generate

- 源码定位：[slime/ray/rollout.py:335](/home/hongshi/projects/slime/slime/ray/rollout.py:335)，固定版本 `18868a79`，由助手核对。
- 首次接触：Step 016，2026-10-28；此前仅在整体图定位，本轮回看调用方主干。
- 最近认识更新：尚无用户对实现的直接表述；本页保存入口解释与静态交接。
- 导航：[本步 scope](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/01-scope.md#manager-handoff) · [转换函数卡](../../data/batch_builder.py/BatchBuilder.convert.md)。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据固定源码整理，作为理解参考。

1. **使用场合**：外层 `RolloutManager.generate` 开始一轮 rollout，登记本轮编号后调用 `_generate`。这一层承接整个批次，具体 Agent 的 generate 由配置的 rollout 路径在内部调用。

2. **具体内容**：正常路径取得 Sample 列表，经过构建器的准备／复用判断，转换为训练字段，再分配给训练侧；恢复已有结果和只生成调试模式有提前返回分支。本轮选择无恢复、object-store、debug_rollout_only=False、raw_ref=None，先接通正常数据流。

3. **建议构建的心智模型**：

   > `_generate` 串起一轮结果交付：拿到生成结果 → 准备转换 → 转换数据 → 分配并返回。真正逐个字段整理的工作在 `BatchBuilder.convert` 中。

4. **调用代码**（外层 [317–333 行](/home/hongshi/projects/slime/slime/ray/rollout.py:317)的裁剪；省略计时、上下文编号、健康监控与服务收尾）：

   ```python
   self.rollout_id = rollout_id
   self.batch_builder.rollout_id = rollout_id
   result = self._generate(rollout_id, start_time)
   return result
   ```

## 本场景的输入与输出

构造阅读场景：调用方传入本轮 `rollout_id=0` 及已经取得的 `start_time`，Manager 已有数据源和构建器。选择无恢复、object-store、非 debug_rollout_only；`batch_builder.raw_ref=None`。这里静态跟踪接口，没有运行整个 Manager。

```text
输入：本轮编号、起始时间，以及 Manager 已有的运行组件
  │
  ├─ _get_rollout_data → (data, metrics)
  │                      data 是已展开的 list[Sample]
  ├─ begin(data, ...) → None
  ├─ convert(data) → train_data 字典
  └─ split_by_dp(train_data) → 每个 DP 分片对应一个包装后的 Ray 引用

返回：split_by_dp 的结果列表；由外层 generate 接住并返回
```

中间 Sample → 字段字典的具体数值沿用 [convert 卡片的小例子](../../data/batch_builder.py/BatchBuilder.convert.md#field-assembly)。最终返回形式在 split_by_dp:497–530 定位为列表，object-store 路径向其中追加 `Box(ray.put(value))`；本轮没有生成真实 Ray 引用，也不展开分片算法。

### ① 先看正常路径怎样把三种数据接起来

以下裁剪自 [355、380–390 行](/home/hongshi/projects/slime/slime/ray/rollout.py:355)，省略恢复、日志、调试退出与 straw 发布，保留真实的 begin 返回判断：

```python
data, metrics = self._get_rollout_data(rollout_id=rollout_id)

cached = self.batch_builder.begin(
    data, replay=self.recovery is not None and rollout_id in self.recovery.batches
)
if cached is not None:
    return cached

data = self.batch_builder.convert(data)
return self.batch_builder.split_by_dp(data)
```

- 第一行的 `data` 是 Sample 列表；它来自此前已读生成、评分、收集链的返回结果。
- `begin` 返回非 None 时，调用方直接返回该结果；当前选择的分支返回 None，继续执行 `convert`。
- 385 行把同名变量 `data` 重新赋值成训练字段字典。390 行再分配数据并返回，所以 `_generate` 的最终返回值与 `convert` 的中间字典要分开看。

### ② begin 先看当前短分支

[BatchBuilder.begin:48–53](/home/hongshi/projects/slime/slime/data/batch_builder.py:48)的当前分支：

```python
if self.raw_ref is None:
    self.batch_id = None
    self._plan = None
    return None
```

当前没有持久化原始批次引用，清空相关计划状态后返回 None。回到 `_generate` 的 383 行，提前返回条件不成立，于是执行 385 行的 `convert`。这足以解释当前交接。

`begin` 完整职责还包括：有 raw_ref 时保存／核对选择与转换计划，已存在 ready 结果时调用 split_by_dp 返回可用结果。因此它不只是检查普通内存缓存，也不是启动生成任务。相关持久化分支先保留用途，后续需要恢复或复用语义时再展开。

### ③ 回到 convert，再接后续分配

| 在哪里继续 | 本轮需要的关系 | 返回位置 |
| --- | --- | --- |
| [BatchBuilder.convert](../../data/batch_builder.py/BatchBuilder.convert.md#field-assembly) | 同一份 Sample 怎样变成训练字段 | 回到 `_generate:385`，data 接住字典 |
| [split_by_dp:445](/home/hongshi/projects/slime/slime/data/batch_builder.py:445) | 当前只定位分配和返回封装 | `_generate:390` 直接返回其结果，外层 generate:328 接住 |

## 我的直接表述（原话）

> 好的 那么我们来看一下这里的rolloutmanager generate吧
> 是否需要看begin 还是你觉得这里有你觉得最好的链接和讲述方式？

用户提出回看上层入口并比较 begin 的阅读深度，尚未表达对 Manager 实现的理解。

## 尚不清楚

- 对 `generate` 外层入口、`_generate` 编排和具体 Agent generate 的职责区分，尚待反馈。
- begin 的持久化计划、ready 复用与恢复分支尚未展开。
- split_by_dp 的具体划分、张量整理和 Ray 交付细节只定位用途。
- 健康监控、服务收尾和异常清理不在本轮展开。

<details>
<summary>来源、验证与完整例子</summary>

- [Step 016 形成过程](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#manager-generate-handoff)。
- 源码：rollout.py:317–390；batch_builder.py:48–120、445–530，固定版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。
- 本卡是静态调用和返回关系核对，没有执行 Manager、begin 的持久化分支、Ray 或训练。前一轮的隔离执行只覆盖 convert 的构造例子，不作为本卡运行证据。
- `BatchBuilder.__init__` 在 batch_builder.py:35–38 初始化 rollout_id、raw_ref、batch_id 和 _plan；本轮不另开完整类卡。

</details>
