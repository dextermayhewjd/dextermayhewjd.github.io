# 父函数卡调整前快照：代码标记与紧邻说明

保留 2026-10-26 调整前的完整卡片；现行内容见[父函数卡](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md)。本页为历史快照。

---

# generate_and_rm_group

- 源码定位：[slime/rollout/sglang_rollout.py:388–439](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L388-L439)。
- 首次接触：Step 010 作为调用者定位；2026-10-26 在 Step 011 按用户指定独立展开。
- 最近认识更新：2026-10-26，用户已将 group、Sample、任务创建和结果收集联系起来，并提出 session_id 重复创建、参数副本、外层列表副本及评分责任的疑问；下述源码校准尚待反馈。

AsyncRolloutWorker._loop → **本函数：组织一组生成任务** → [generate_and_rm](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md) → 返回本函数汇总 → 调用者的完成回调接收结果。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：调度者拿到一组 Sample，要为其中待生成的成员分别启动生成，并取得完整的一组结果。本例继续 Coding Agent，evaluation=False、group_rm=False。
2. **具体内容**：取得共享状态，准备会话标识，为非列表成员创建任务；等待全部任务结果，按原组位置写回；开启组级评分时由本层负责评分，最后返回 group。已有分段列表先校验再保留。
3. **建议构建的心智模型**：

   > 组级组织者：把一组工作分给多个 generate_and_rm，再按原位置收齐结果。
   >
   > ```text
   > 输入 group
   > ├─ 待生成的 Sample → 创建任务 → generate_and_rm
   > └─ 已完成的分段列表 → 校验后保留
   >             ↓
   > 等本次创建的任务全部返回，结果放回各自 idx
   > ├─ group_rm=False → 交回整组（本例）
   > └─ group_rm=True 且未中止 → 组级评分后交回
   > ```
   >
   > 第一层按“是否需要重新生成”分类；第二层按“是否由本层评分”分类。外层组的位置保持，子任务返回的 Sample 或列表也保持原形状。

4. **调用代码**（AsyncRolloutWorker._loop:214–223，本步只定位调用者）：

   ```python
   task = asyncio.create_task(
       generate_and_rm_group(
           self.args, group,
           sampling_params=self.state.sampling_params.copy(),
           evaluation=False,
       )
   )
   task.add_done_callback(self._make_done_cb(gid, group))
   ```

## 本场景的输入与输出

**输入**：调用者已经提供 group。本函数不负责把一个提示复制成多个输入。本例用两个新 Sample 的 group=[s0, s1] 观察交接；sampling_params 是该组的公共采样配置，evaluation=False、group_rm=False。两个成员不含已有分段列表，也未开启确定性采样。对象标签和数量为教学构造，不代表真实运行数据。

**输出**：返回一份新的外层 group 列表。每个原位置被该任务的返回结果替换；Coding Agent 可使每个位置成为一个 Sample 列表，因此结果可以是 list[list[Sample]]。本函数没有把内层列表展开为一条平坦列表。输入 Sample 的 session_id 可在准备阶段被补充。

### 1. 准备成员（398–415）

- 取得 [GenerateState](../02-short-term-memory/classes/slime/rollout/sglang_rollout.py/GenerateState.md)；若已经中止，直接返回输入 group。
- 新 Sample 仅在 session_id is None 时补 UUID，已有编号保留；后面将同一个 Sample 交给 generate_and_rm。这一步只是准备标识，还没有在 Adapter 中登记会话。
- 进入 Coding Agent 的 _generate 后，[_session_id](../02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_session_id.md)优先返回已有的非空编号。因此通常沿用外层补好的 UUID；只有仍缺少有效编号，才走 cagent-题号-索引或随机后缀的兜底分支。随后 adapter.open_session 才登记会话。
- 这里的“每个 Sample”针对待生成的普通成员；旧分段列表走下述保留分支。
- 如果成员已是分段列表，只接受非空且各段已完成或截断的结果；非组评分时各段还需已有 reward。这是重试保留路径，本例暂不深入。

### 2. 创建任务、等待全部、按位置写回（417–430）

以下为真实代码的教学裁剪，保留组级评分分支以显示职责；省略前面的准备、确定性 seed 覆盖与 trace 包装：

```python
tasks = {}
for idx, sample in enumerate(group):
    if isinstance(sample, list):
        continue  # 已完成的分段结果在前面校验过，保留它
    current_sampling_params = sampling_params.copy()
    # 本例未开启确定性采样，省略 seed 覆盖
    tasks[idx] = asyncio.create_task(
        generate_and_rm(args, sample, current_sampling_params, evaluation=evaluation)
    )

results = await asyncio.gather(*tasks.values())
group = list(group)
for idx, result in zip(tasks, results, strict=True):
    group[idx] = result

if not state.aborted and args.group_rm:
    rewards = await batched_async_rm(args, group)
    for sample, reward in zip(group, rewards, strict=False):
        sample.reward = reward
return group
```

- tasks 的键是原组下标，值是 Task；每个非列表成员各有一个 generate_and_rm 调用。
- sampling_params 在调用前已经准备好，包含 temperature、top_p、max_new_tokens 等生成设置；本段不是重新计算一套采样策略，而是为每个任务复制一份字典，再传给 generate_and_rm。顶层键可分别修改；嵌套值仍共享引用。确定性采样分支会在该副本里写 sampling_seed；通用生成实现也会调整 max_new_tokens。
- results 是各 Task 的返回值。group = list(group) 新建外层列表，初始仍引用原来的成员；随后 group[idx] = result 才把相应槽位换成生成结果。原输入外层列表的槽位不因这几行被替换，但成员对象可已被前面的 session_id 赋值或子函数修改。见[浅拷贝参考](python-shallow-copy.md)。
- gather 成功时按传入任务的顺序返回结果，完成得快不代表被放到前面。zip(tasks, results) 再把每份结果写回对应 idx；已保留的列表成员不会丢失。
- 组内任务均已创建后才执行这一处 gather 等待。实际进入生成的名额与启动节奏仍由子函数中的 semaphore、pacer 控制；本函数没有另设组内并发上限。

教学示意：s1 对应的任务先完成，s0 后完成；只要都正常返回，输出仍是 [s0 的生成结果, s1 的生成结果]。若各任务返回列表，则输出是 [[s0 的各段], [s1 的各段]]。

### 3. 评分与交付（432–439）

这里要把子函数与本函数的同一个 group_rm 开关对照看：

| group_rm | generate_and_rm 的评分阶段 | generate_and_rm_group 收齐后的评分阶段 |
| --- | --- | --- |
| False（本例） | 对正常结果补缺失的 reward；自定义生成已给分时保留它 | 跳过组级评分，直接返回 group |
| True | 生成和 hook 后直接返回，跳过本层补分逻辑 | 未中止时将整个 group 交给 batched_async_rm，再写回 reward |

因此框架用开关选择补分发生在哪一层；不能仅凭看见两个评分入口，就认为它们会连续执行。组级入口让需要整组信息的自定义评分函数拿到完整 group；batched_async_rm 的默认分支仍逐项调用 async_rm，具体见[已有接口卡](../02-short-term-memory/functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md)。

另一个边界是自定义生成函数可以自行评分：Coding Agent 的 _generate 会先运行评测，再把 reward 交给 finish_session。当前 False 路径保留已有分数；若改为 True，开关只让 generate_and_rm 跳过补分，并不会禁止插件内部评测，而本层组级评分也不按 reward 是否为空过滤。因此不能概括成“任何配置下都绝不重复评分”。本层写回按成员为 Sample 使用，True 与 Coding Agent 嵌套结果的组合未在本轮验证。

返回本函数结果后，AsyncRolloutWorker 为它注册的完成回调处理整组结果；完成队列、继续取任务与背压属于后续调度问题。

## 我的直接表述（原话）

> 好的那么 我们现在看一下下一个generate and rm group的内容吧

这是最初的阅读范围确认。

2026-10-26，沿整体骨架的初步理解与疑问：

> 好的那么我们来看一下这里的几个部分吧
> 之前的generatestate还是和上一部一样
> 但是这里有一个这个group
> group里面都是sample
> 那么是给每一个sample先创建一个session id吗？
>
> 我记得coding agent rl 里面已经有对于如何创造session id的部分了？
> 为什么这里会有不一样的？
>
> 其次是这里task吧
> 首先是enumerate了这里的group
> 然后这里会创建sampling的aprams的内容
> 我不是特别理解
> 然后就通过上面说的generate and rm来处理之前的sample了
>
> 然后呢？
> 这里还有results
> 这里我理解
> 就是收集这里的结果
> 然后为什么还要在列一下这里的group
> 然后是在这里给这里的group rm里面为什么还需要一个batched async rm呢？
> 我很疑惑 之前在单独的generate and rm里面不是已经拿到过奖励了吗？
> 这里是再来一层给一下奖励？
> 我不是特别理解了

原话已能对应到若干处理阶段，但四处机制疑问仍需校准，不预填为已掌握。

## 尚不清楚

- session_id 的上层补齐与 Coding Agent 优先复用、编号与会话登记的区别，已给源码校准，尚待反馈。
- 已有采样设置与逐任务字典副本的区别、tasks/结果/外层列表三者的关系，已给解释，尚待反馈。
- group_rm 的两层互补分支，以及插件内部自行评分的边界，已给解释，尚待反馈。
- gather 的返回顺序、分段列表形状是否已理解，尚待反馈。
- 一个子任务异常或被取消时，本层与完成回调怎样协作处理；重试、确定性采样和组评分的具体组合，留待后续问题。
- 上游怎样构造 group、决定同时运行多少组，以及结果如何排队交付，不在本轮展开。

<details>
<summary>来源与验证边界</summary>

- 固定提交 18868a79b0b083a093798a94ed0f8cb4f71b9c14，已核对本地源码与干净工作区。
- [本函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L388-L439)、[实际示例路径的调用者](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L208-L223)。
- 本轮校准源码：[session 复用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L438-L443)、[登记与参数传递](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L269-L274)、[插件评测结果导出](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L325-L329)、[单任务评分开关](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L357-L378)。
- [本轮问题与解释](../04-flow.md#group-four-handoffs)；[本步过程](../04-flow.md#group-reading-start)；[本步继承来源](../03-long-term-memory/overview.md)。
- 已用真实函数 AST 去掉追踪装饰器，在最小 Sample/GenerateState 与可控生成函数替身下验证：后完成的第 0 项仍回到第 0 位、内层列表保留、每份采样参数独立、旧列表不重跑、预先中止原样返回。首轮实验缺少 Any 类型导入，补齐后上述检查通过。该实验不等于运行真实 Agent、模型、队列服务或训练。

</details>
