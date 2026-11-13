# Job._init_trial_configs

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../step-012-task-agent-verifier/02-short-term-memory/functions/harbor/job.py/Job._init_trial_configs.md) 完整继承；复制不改变原认识时间或已掌握状态。

- 源码：[src/harbor/job.py:448–457](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L448)，Harbor v0.25.0。
- 首次单独建卡：Step 012，2026-11-12。此前只作为 JobPlan 的转交位置；用户现明确本轮先看这个函数。

[从 Job.__init__ 的 self._init_trial_configs() 进入](Job.__init__.md#job-init-mainline) → **当前：_init_trial_configs** → [普通分支进入 _build_standard_trial_configs](Job._build_standard_trial_configs.md#standard-trial-configs-mainline) · [scope](../../../../../step-012-task-agent-verifier/01-scope.md#reading-sequence)

进入时 Job 已保存运行配置和题目来源；本轮选普通分支。下层列表返回后，本方法将它写入 self._trial_configs，再回到 Job.__init__。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Job.__init__ 已保存配置和任务材料，现在要初始化 self._trial_configs。
2. **具体内容**：根据 Job 类型选择配置生成方法，将返回的列表保存到当前 Job。
3. **建议构建的心智模型**：

   > 选择本次 Job 的尝试配置生成方式，再把生成结果保存下来。

4. **调用代码**（Job.__init__:116）：

   ```python
   self._init_trial_configs()  # 当前进入这里；self 是正在初始化的 Job。
   ```

## 本场景的输入与输出

不额外传入参数，使用 self.config 和对象已有材料；正常返回 None，生成的列表保存在 self._trial_configs。它不运行 Trial，也不是直接返回列表给 __init__。

<a id="init-trial-configs-mainline"></a>

### 完整函数：先看普通路径怎样保存配置

```python
def _init_trial_configs(self):
    if self.config.is_regrade:  # 重评类型走自己的配置生成方式；本轮略过。
        self._trial_configs = self._build_regrade_trial_configs()
        return

    if self.config.is_diff:     # 差异任务走另一种生成方式；本轮略过。
        self._trial_configs = self._build_diff_trial_configs()
        return

    # 本轮普通任务走这里：调用生成方法，接住列表，保存到当前 Job。
    self._trial_configs = self._build_standard_trial_configs()
```

**当前先看最后一行的调用与赋值。** 具体怎样组合题目、Agent 和次数，是下游做的事；不能把两个函数当成同一个函数。

下一层进入 [_build_standard_trial_configs 函数卡](Job._build_standard_trial_configs.md#standard-trial-configs-mainline)，再由它进入 JobPlan。列表返回到当前函数后，才完成 self._trial_configs 的赋值；随后本方法正常返回 None，回到 [Job.__init__](Job.__init__.md#job-init-mainline) 继续初始化。

## 我的直接表述（原话）

> 不是这里的这个init trial config吗?
> 为什么是这个函数呢?

用户指出当前目标是 Job._init_trial_configs。助手此前把下游组装函数直接作为当前入口，现修正；不将这次导航纠正记作已经理解函数内部。

## 尚不清楚

- 当前普通分支下，具体怎样组成 TrialConfig，读完本函数再按需要进入下游。
- regrade、diff 的具体规则，本轮不展开。

<details>
<summary>来源与验证</summary>

- Harbor 发布提交 fdba28fc411e47e8765420a1a063b4918fce3def，job.py:116、448–462，按本地 git show 核对。
- 本文仅增加注释，主函数执行语句完整保留；未运行初始化或创建任务。
- [本步纠正记录](../../../../../step-012-task-agent-verifier/04-flow.md#correct-init-trial-configs-entry)。

</details>
