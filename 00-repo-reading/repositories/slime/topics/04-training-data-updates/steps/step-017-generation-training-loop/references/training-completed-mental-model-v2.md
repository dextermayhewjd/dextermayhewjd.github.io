# 方案二 · 用伪代码与同行注释逐层展开 training_completed

**本方案已于 2026-10-31 采用到[正式函数卡](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md#mental-model)。** 本页保留第二版原型，[最终定稿](training-completed-card-final-v2.md#mental-model)保留合并前版本。

> **位置**：[Step 017](../01-scope.md) → [原函数卡的心智模型](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md) → **第二版：紧凑伪代码** · [第一版：递进图示](training-completed-card-proposal.md#progressive-mental-model)。

本方案只替换第一版 **2.3 心智模型的展示方式**，沿用同样的三层内容；每项作用写在代码旁边。完整源码下潜、个人原话、未知与来源继续保存在[第一版正文](training-completed-card-proposal.md#layer-manager)；两版均为对照材料。

下文是阅读用伪代码，使用 `python` 代码块让 `#` 旁注按注释高亮。箭头和缩进表示“进入下一层调用”，不是 Python 的嵌套函数定义；自然语言语句用于概括动作，不是新增的源码接口，也不表示整段可以直接运行。

## 2.3 建议构建的心智模型：伪代码版

> 训练已结束，通知数据侧处理本轮完成登记；有登记批次时标记已消费并收尾，没有则直接返回。调用方等待这次处理完成，再继续主循环。

<a id="layer-purpose"></a>

### 2.3.1 第一层：先看整体职责

```python
# 前提：本轮训练已结束
ray.get(  # 等待这次完成登记处理结束
    rollout_manager.training_completed.remote(rollout_id)  # 发送本轮完成通知
)
```

**这一段完成什么**：训练主循环通知数据侧“这一轮训练已经结束”，并等整个完成登记调用处理完，再继续下面的流程。

<a id="layer-delegation"></a>

### 2.3.2 第二层：展开通知经过的对象

```python
RolloutManager.training_completed(rollout_id)  # 接收本轮训练完成的通知
  → BatchBuilder.training_completed(rollout_id)  # 转交；下面的 self 指 BatchBuilder
      if self.batch_id is None: return None  # 没有登记批次，直接结束
      if rollout_id != self.rollout_id: raise ValueError(...)  # 轮次不符，报错
      ray.get(  # 等 Controller 真正处理完
          self.controller.finish_batch.remote(self.batch_id)  # 交出要收尾的批次编号
      )
```

**这一段完成什么**：Manager 转交通知，BatchBuilder 确认当前有没有需要登记的批次、轮次是否匹配，然后把具体批次交给 Controller，并等待它处理完成。

[对应源码：第一版 3.1–3.2](training-completed-card-proposal.md#layer-manager)。

<a id="layer-state"></a>

### 2.3.3 第三层：只展开 Controller 的状态变化

```python
RolloutQueueController.finish_batch(batch_id)  # 只处理指定的这一批
    batch = self.batch(batch_id)  # 取得批次登记
    if not batch or not batch["ready"]: 报错  # 批次需存在且准备就绪
    receipt = 该批结果的回执  # 提供结果所在位置 receipt.position
    state = self._training_state()  # 读取消费进度和待完成登记
    self._advance(state, [receipt.position])  # 登记该结果位置已消费
    state["batches"] = 去掉当前 batch 对应的引用  # 例：[A, B] → [B]
    self._save_training_state(state)  # 保存更新后的进度与批次登记
    return None  # 本层处理结束，逐层返回到 train.py:71
```

<a id="controller-whole-logic"></a>

**这一段完成什么**：为这批已经训练完的数据做完成登记。找到该批次及其结果位置，把对应数据记为已消费，从未完成批次列表中移除它的引用，并保存新的状态。这样，数据管理侧就不再把这一批记作“还等训练完成确认”。返回表示本次登记处理结束。

[对应源码：第一版 3.3](training-completed-card-proposal.md#layer-controller)。A、B 是批次引用的示意名称。

**边界**：本次处理的是已训练数据的登记；暂停新任务是主循环第 88 行的另一条调用。

## 两版怎样选

第二版适合在阅读时快速定位层次与分支；需要建立对象之间的整体关系时，可回看第一版图示。两版保留相同的前提、分工与结果，本次没有把对展示形式的认可记为技术机制已掌握。

<details>
<summary>源码依据与范围</summary>

- 固定版本 `18868a79`：train.py:67–71；RolloutManager.training_completed:430–431；BatchBuilder.training_completed:144–148；RolloutQueueController.finish_batch:814–827。
- 第二层将 `batch_id=None` 的正常结束显式写为早返回，语义与源码外层 if 不成立时一致。第三层保留 `_advance`、`_save_training_state` 等真实名称，回执获取和过滤表达式用自然语言概括；`return None` 显式标明原方法的正常隐式返回。
- 锁、完整回执读取和可选 GC 已省略，A/B 状态变化来自源码推导；未执行真实队列或训练。
- 未展开暂停接纳、权重同步、消费游标算法、锁、租约或存储回收。完整历史来源见[第一版来源](training-completed-card-proposal.md#6-来源验证与完整例子)。

</details>
