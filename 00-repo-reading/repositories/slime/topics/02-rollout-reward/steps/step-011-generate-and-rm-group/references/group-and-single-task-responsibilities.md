# 为什么分成组级组织与单次生成

[返回父函数卡](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md)。本页解释已读代码的职责分工，源码绑定 Slime 18868a79；下面的好处是从结构和数据交接作出的分析，不冒称作者的原始设计说明。

## 一组相关输入，每份各自生成

一个实际来源是 [RolloutDataSource.get_samples:124–134](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/data_source.py#L124-L134)：同一个 prompt 按 n_samples_per_prompt 复制多份 Sample，共享 group_index，各有 sample.index。组关系表达这些生成输入属于同一组；每个成员都需要完成自己的生成。

这说明普通数据源存在“一题多次尝试”的实际需求，不据此假定所有队列输入都由这个方法构造，也不保证多个尝试的输出必然不同。本轮只回查这条来路，没有开启数据源的完整阅读。

```text
同一道题的一组 Sample
    ├─ Sample A → Task A → generate_and_rm → A 的生成结果
    ├─ Sample B → Task B → generate_and_rm → B 的生成结果
    └─ Sample C → Task C → generate_and_rm → C 的生成结果
                    ↓
组级按原位置收齐 → 需要时组级评分 → 返回整组
```

这里的 group 进入函数时是 Sample 组成的列表，代码随后为待生成成员创建 Task。用户所说的 taskgroup 可以作为“一组工作”的口头模型，当前代码没有使用 asyncio.TaskGroup。

## 代码中怎样体现这种分工

组级 [417–430](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L417-L430) 中，跳过已完成分段结果后，关键交接是：

```python
current_sampling_params = sampling_params.copy()
tasks[idx] = asyncio.create_task(
    generate_and_rm(args, sample, current_sampling_params, evaluation=evaluation)
)
```

所有待生成成员的 Task 创建完毕，再通过 gather 等待并按 idx 放回 group。单个 Task 调用的是完整的单次生成控制流程；对于 Coding Agent，它可以包含多轮模型与工具交互，并返回多个分段 Sample。这不是把一份轨迹中的 token 拆成并行任务。

| 分工带来的效果 | 对应代码与实际意义 |
| --- | --- |
| 多份生成可以交错推进 | 先创建多个 Task，再 gather。某份工作等待模型服务或沙箱时，其他已获准的任务有机会继续；并发程度仍取决于资源与限流 |
| 按一次生成控制资源 | generate_and_rm 使用共享 semaphore、pacer、DP 上下文与 finally 释放名额；组内各成员分别携带会话和参数进入同一个控制流程 |
| 单次生成接口可以复用 | 组级只依赖 generate_and_rm 的输入输出；后者负责选择默认生成器或自定义生成器、后处理与按配置补分，更换生成实现时组级汇总逻辑通常可沿用 |
| 保留组内关系与统一交付 | idx 维持输入与结果对应，旧分段结果可保留；group_rm=True 时收齐后交给整组评分入口，False 时沿用单任务已处理的奖励 |

单任务的控制、生成选择与补分分支见 [sglang_rollout.py:326–378](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L326-L378)；组级评分见[433–439](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L433-L439)。

## 当前模型的边界

- 并发推进不保证吞吐一定提高，也不表示每个 Task 独占进程或 GPU；共享服务能力、并发名额与等待时间决定实际效果。
- 当前组级会在 gather 处等齐本次任务后整体返回，先完成的成员不会由这个返回值提前交付。
- 拆成多个 Task 本身不自动提供失败隔离或重试协议；这些行为按既有未知继续保留。
- 分成两个函数的可维护性收益，与创建多个 Task 带来的并发效果分别成立。写成一个大函数也能实现并发，但单次控制与组级组织会混在一起。

本轮仅做静态源码核对，没有新增生成、评分或吞吐实验。
