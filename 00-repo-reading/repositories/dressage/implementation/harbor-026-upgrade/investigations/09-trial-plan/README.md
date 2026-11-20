# 09 · JobPlan 生成的 Trial 还能正确对应 Dressage 的题目和尝试吗？

**当前判断**　保留 Dressage 的 Trial 配对逻辑，把已经观察到的真实 Job 行为固化为回归用例。

**对应的三版用法表**　[U15 Job._task_configs 提供已经解析的任务对象](../../usage/Job%20与%20Agent%20路由/U15-Job._task_configs%20提供已经解析的任务对象.md#u15) · [U16 Job._remaining_trial_configs 提供待执行配置](../../usage/Job%20与%20Agent%20路由/U16-Job._remaining_trial_configs%20提供待执行配置.md#u16) · [U17 build_trial_plan 配对原对象并写回 trial_name](../../usage/Job%20与%20Agent%20路由/U17-build_trial_plan%20配对原对象并写回%20trial_name.md#u17) · [原套件在本问题测到了哪里](../original-test-audit.md#i09)

一个题目可以有多个 Agent 和多次尝试。归错位置会把生成结果交回错误的训练模板。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　按位置同时校验 task 与 agent 的对象身份。[compat.py 第 158–165 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L158-L165)

```python
if config.task is not tasks[task_index]:
    raise HarborCompatibilityError(
        f"TrialConfig position {position} violates Harbor v0.18 task-major ordering"
    )
if config.agent is not agents[agent_index]:
    raise HarborCompatibilityError(
        f"TrialConfig position {position} violates Harbor v0.18 agent-minor ordering"
    )
```

**Harbor 0.26.0**　TrialConfig 的生成顺序由三重遍历确定。[job_plan.py 第 169–171 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job_plan.py#L169-L171)

```python
for _ in range(config.n_attempts)
for task_config in task_configs
for agent_config in config.agents
```

**据此判断**　Dressage 按 attempt、task、agent 推算位置，还要求 Trial 引用原来的对象。一次真实 Job 能同时验证顺序和对象身份这两个假设。

<a id="evidence"></a>

## 证据与验证范围

**单题输出**　0.26.0 的一次尝试、一道题、一个 Agent。[trial-plan-output.txt 第 21 行](trial-plan-output.txt#L21)

```text
plan (attempt, task, agent): [(0, 0, 0)]
```

**扩展输入输出**　同版改为两次尝试、两道题、两个 Agent。[trial-plan-output.txt 第 24 行](trial-plan-output.txt#L24)

```text
plan (attempt, task, agent): [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)]
```

三个 Harbor 版本都通过这一探测。0.25.0 和 0.26.0 的修前探测只在当前进程临时放行原版本门槛，探测终点是 Job 计划。

## 处理与验收

**下一步**　在现有手工 Job 合同旁加入上述真实 `Job.create()` 输入，断言位置三元组及其对应的原始模板。[test_contracts.py:108](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_contracts.py#L108)

**通过条件**　所有预期位置完整出现且顺序正确，Dressage 的对象身份检查通过，分配的 Trial 名唯一，能够回到同一题目和 Agent。

<a id="history"></a>

## 判断记录

- 2026-11-11　看到 Harbor 引入 JobPlan，先把对象身份与排列列为待验证。
- 2026-11-18　此前的真实 Job 探测临时放行版本检查，0.25 和 0.26 的顺序、对象身份和 Trial 数量均符合预期。可在独立 Dressage 分支固化该用例。Job 的私有成员集中在 `compat.py`，另一个已知的私有依赖 `_mounts` 属于环境后端。

### 复查入口

- 复现与对照　[计划探测](probe.py) · [逐版输出](trial-plan-output.txt) · [本地题目](tasks)
- 完整调用与配置　[compat.py:121](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L121-L165) · [job_plan.py:143](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/job_plan.py#L143) · [三层循环](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/job_plan.py#L164-L173)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#job) · [返回问题索引](../../README.md#investigations)
