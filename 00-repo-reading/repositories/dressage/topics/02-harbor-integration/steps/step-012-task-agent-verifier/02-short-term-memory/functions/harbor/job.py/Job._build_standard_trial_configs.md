# Job._build_standard_trial_configs

- 源码：[src/harbor/job.py:459–462](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L459)，Harbor v0.25.0。
- 首次单独建卡：2026-11-12；此前已在普通分支的交接中查看，本次补成可独立跳转的短卡，不代表新增掌握。

[从 _init_trial_configs 的普通分支进入](Job._init_trial_configs.md#init-trial-configs-mainline) → **当前：_build_standard_trial_configs** → [下钻 JobPlan.build_trial_configs](../job_plan.py/JobPlan.build_trial_configs.md#trial-plan-mainline) · [scope](../../../../01-scope.md#reading-sequence)

进入时，self 是正在初始化的 Job，已经保存 config、任务列表和 Job ID；返回时，把下层生成的列表交回 _init_trial_configs，由它保存到 self._trial_configs。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_init_trial_configs 判断当前是普通 Job，调用本方法生成尝试配置。
2. **具体内容**：从当前 Job 取出三项已有数据，传给 JobPlan.build_trial_configs，把返回列表原样交回。
3. **建议构建的心智模型**：

   > 从 Job 取出组装所需的资料，交给 JobPlan 生成列表，再把列表返回上层。

4. **调用代码**：

   ```python
   # _init_trial_configs 中：右侧先执行完，左侧才接住返回的列表。
   self._trial_configs = self._build_standard_trial_configs()
   ```

## 本场景的输入与输出

<a id="standard-trial-configs-mainline"></a>

下面保留完整方法，只补注释：

```python
def _build_standard_trial_configs(self) -> list[TrialConfig]:
    return JobPlan.build_trial_configs(
        self.config,         # Job.__init__ 已保存的整份运行配置。
        self._task_configs,  # 已解析好的题目来源列表。
        job_id=self._id,     # 当前 Job 的身份。
    )                        # 直接把 list[TrialConfig] 返回给上层。
```

本方法不创建新的 Job，也不自己保存 self._trial_configs。具体组合在[下一张 JobPlan 卡](../job_plan.py/JobPlan.build_trial_configs.md#trial-plan-mainline)；读完先返回本方法的 return，再回到[_init_trial_configs 的赋值处](Job._init_trial_configs.md#init-trial-configs-mainline)。

## 我的直接表述（原话）

> 然后需要看这里的这个init trial configs
> 然后需要看这里的这个build standard trial configs

以上为用户指定阅读顺序的节选。尚无对本方法内部的独立复述。

## 尚不清楚

- 下层怎样组合题目、Agent 和次数，继续使用已有 JobPlan.build_trial_configs 卡与具体例子。

<details>
<summary>来源与验证</summary>

- 来源为本地 Harbor 发布标签 v0.25.0，提交 fdba28fc411e47e8765420a1a063b4918fce3def；没有联网或执行任务。
- 本方法的调用者在 job.py:457；返回类型为 list[TrialConfig]，保存动作属于调用者。
- [Step 012 本次导航修正](../../../../../step-012-task-agent-verifier/04-flow.md#complete-creation-chain-navigation)。

</details>
