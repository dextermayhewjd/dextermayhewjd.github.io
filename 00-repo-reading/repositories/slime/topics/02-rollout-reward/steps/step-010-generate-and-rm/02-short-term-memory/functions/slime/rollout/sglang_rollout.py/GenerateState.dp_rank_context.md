# GenerateState.dp_rank_context

- 源码定位：[sglang_rollout.py:123–133](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L123-L133)。
- 首次接触：Step 010 的控制骨架；2026-10-25 随生成前控制段展开。
- 最近认识更新：尚无对本方法机制的独立复述；以下为助手静态核对。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：当前任务已取得生成名额、通过 pacer，且没有中止，随后调用这个方法取得上下文管理器，在 `with` 的范围内执行生成。
2. **具体内容**：从在途计数最少的 DP rank 中随机选一个，增加其计数并记录编号；交给 with 主体使用，退出时减少该 rank 的计数。
3. **建议构建的心智模型**：

   > 为本次生成片段临时登记一个 rank 的占用：进入加一，退出减一。先看清这段计数的生命周期。

4. **调用代码**：

   ```python
   with state.dp_rank_context() as _:
       ...  # 选择生成实现并创建 generate_call
       sample = await _run_server_abort_generate(state, generate_call)
   ```

## 本场景的输入与输出

本方法用 `@contextmanager` 包装，调用时得到上下文管理器；进入时 `yield` 交出 rank 编号。调用方用 `_` 接住它，本方法本身不生成 Sample。

### 与 HarnessContext 的区别

| 名称 | 是什么 | 怎么使用 |
| --- | --- | --- |
| [HarnessContext](../../../../classes/slime/agent/harness/common.py/HarnessContext.md) | 保存工作目录、会话编号、Adapter 地址等信息的数据类 | 创建 `ctx`，传给其他方法读取字段 |
| `GenerateState.dp_rank_context` | 定义在 GenerateState 上的方法；调用后得到上下文管理器 | `with` 进入时登记计数，离开时归还计数 |

这里的 `context` 指“一段代码执行期间的上下文管理”，与保存运行参数的 `HarnessContext` 用途不同。类卡保存 `dp_counts` 等字段的含义，本方法卡保存对这些字段的一次操作；父函数 [generate_and_rm](generate_and_rm.md#generation-admission)保留四处控制语句之间的顺序。

`with state.dp_rank_context() as _:` 中，右侧调用产生上下文管理器，`_` 收到的是进入时 `yield` 交出的整数 rank，而非一个 HarnessContext 式的参数对象。

### 进入与退出怎样改变计数

教学构造：假定 `state.dp_counts = [2, 0, 1]`，期间没有其他任务修改计数。

| 时机 | 本例中的变化 |
| --- | --- |
| 进入 | rank 1 的计数最少，选中它；`dp_counts` 变为 `[2, 1, 1]`，`dp_rank = 1` |
| 使用期 | `yield 1`，随后运行 with 主体中的生成代码 |
| 退出 | `finally` 将 rank 1 的计数减一，回到 `[2, 0, 1]`；`dp_rank` 没有恢复为旧值 |

真实方法：

```python
@contextmanager
def dp_rank_context(self):
    candidates = [i for i, count in enumerate(self.dp_counts) if count == min(self.dp_counts)]
    dp_rank = int(np.random.choice(candidates))
    self.dp_counts[dp_rank] += 1
    self.dp_rank = dp_rank
    try:
        yield dp_rank
    finally:
        self.dp_counts[dp_rank] -= 1
        assert self.dp_counts[dp_rank] >= 0
```

最小计数并列时随机选一个。这里确认的是 rank 的选择与计数管理；当前调用处没有直接把这个编号传给模型服务，不能仅据此断定实际请求已路由到对应实例。

## 我的直接表述（原话）

> 然后最后的这里state dp rank context的部分是不是应该好好看一下了呢?

这是进入本方法的阅读问题，尚无机制复述。

随后比较已有概念并询问记录分工：

> 但是这里的state的dp rank context是什么
> 有点类似于之前看的harnesscontext的东西吗?
>
> 考虑一下之前都是按照function切分的
> 目前应该怎么分呢?

## 尚不清楚

- DP rank 与模型请求实际路由的关系尚未展开。
- 并发调用时的计数交错可在后续实例中继续观察。
- 数据参数对象与上下文管理器的区别已由助手补充，尚待用户反馈。

<details>
<summary>来源、验证与返回位置</summary>

- 固定版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；调用处为 [337–349 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L337-L349)。
- 读完回到 [generate_and_rm](generate_and_rm.md#generation-admission)：进入上下文后选择并执行生成，退出后由外层 finally 归还 semaphore 名额。
- [Step 010 本轮问题](../../../../../../step-010-generate-and-rm/04-flow.md#generation-admission-questions)。示例为静态构造，未运行并发或模型请求。
- [两种 context 与记录分工](../../../../../../step-010-generate-and-rm/04-flow.md#context-kinds-and-card-boundaries)。HarnessContext 原卡保留自己的历史版本，本轮只用其数据类职责作对照。

</details>
