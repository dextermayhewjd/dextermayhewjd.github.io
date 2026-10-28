# @contextmanager：用 yield 连接进入、使用与退出

[返回 dp_rank_context 函数卡](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/GenerateState.dp_rank_context.md) · [本步 scope](../01-scope.md) · [网页中的机制说明](http://localhost:1313/projects/slime/rollout-reward/#contextmanager-yield)

这份参考承接当前 DP 计数场景，只解释生成器、yield、with 和显式 try/finally 的分工。它不是新函数卡，不增加阅读步骤，也不表示已经掌握完整生成器或装饰器机制。

## 1. 先保留一个模型

**生成器可以暂停和继续；@contextmanager 把这种能力接到 with 的进入与退出。**

```text
调用被装饰的方法 → 得到上下文管理器
进入 with       → 驱动内部生成器，执行到 yield
yield           → 交出值，并暂停生成器
with 主体       → 调用方执行自己的代码
退出 with       → 恢复内部生成器，完成退出处理
```

生成器也是迭代器，但这里用它组织一次进入、使用、退出，不是在循环遍历一批数据。正常使用要求底层生成器恰好 yield 一次。

## 2. 对照当前真实方法

下面保留 Slime `18868a79` 的完整方法体，仅补充注释；它依赖原文件的 contextmanager、numpy 和已初始化的 GenerateState，不是独立脚本。

```python
@contextmanager
def dp_rank_context(self):
    # 进入：选当前计数最少的 rank，并登记本次占用
    candidates = [i for i, count in enumerate(self.dp_counts) if count == min(self.dp_counts)]
    dp_rank = int(np.random.choice(candidates))
    self.dp_counts[dp_rank] += 1
    self.dp_rank = dp_rank
    try:
        yield dp_rank  # 交出编号并暂停；这时运行调用方的 with 主体
    finally:
        self.dp_counts[dp_rank] -= 1  # 退出：撤销本次登记
        assert self.dp_counts[dp_rank] >= 0
```

真实调用的结构是：

```python
with state.dp_rank_context() as _:
    ...  # 选择生成函数、创建调用并等待生成结果
```

| 对象或代码 | 在本例里是什么 |
| --- | --- |
| `state.dp_rank_context()` 的调用结果 | 供 with 使用的上下文管理器 |
| 内部生成器 | 执行上述方法体，能在 yield 处暂停与恢复 |
| `yield dp_rank` 交出的值 | 整数 rank，交给调用方的 `_` |
| `with` 主体 | 调用方的生成代码，不是 yield 下方的代码 |

所以“暂停方法体”不表示停止整个程序：此时要执行的是调用方 with 内的生成任务。

## 3. yield 与 try/finally 各负责什么

- **yield 是进入和退出之间的分界。** 正常进入时执行到这里，正常退出时从这里继续。
- **try/finally 是源码显式写出的清理保证。** @contextmanager 不会自动生成计数减一，也不会把原函数自动改写成 try 与 finally。
- 本例选 rank 和加一在 try 之前，因此“进入就是执行 try”也不准确。
- with 主体正常结束时，内部生成器继续执行；主体抛出异常时，异常送回 yield 位置。本例两种情况都会经过 finally，给之前选定的同一个 rank 减一。

在没有其他调用修改计数的例子中：`[2, 0, 1] → 进入后 [2, 1, 1] → 退出后 [2, 0, 1]`。退出不重新选择 rank；这里维护的是当前占用登记，不是累计完成量。

## 4. 回到当前阅读

带着“进入登记、退出撤销”回到 [dp_rank_context 函数卡](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/GenerateState.dp_rank_context.md)。完整装饰器实现、生成器异常协议及 DP 实际请求路由继续按后续问题展开，不因这份参考被创建而自动推进。

<details>
<summary>源码、书面依据与版本</summary>

- Slime：[dp_rank_context:123–133](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L123-L133)、[调用处:337–349](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L337-L349)。
- [Python 3.12 官方 contextmanager 说明](https://docs.python.org/3.12/library/contextlib.html#contextlib.contextmanager)。本地对照 Python 3.12.3 的 `contextlib._GeneratorContextManager.__enter__/__exit__`；在线文档随维护版本更新。
- 《Fluent Python》第 2 版中英对照及精确小节行号，见[函数卡中的依据 A](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/GenerateState.dp_rank_context.md#依据-a)：英文 `corpus/en/ch18.md:266–436`、中文 `corpus/zh/ch18.md:260–419`，共同锚点 `using-contextmanager`；书籍基于 Python 3.10。
- 这份说明来自源码与文档核对；计数示例为静态推演，没有新增真实生成或训练运行。用户确认纳入的过程见[本步记录](../04-flow.md#contextmanager-reference-saved)。

</details>
