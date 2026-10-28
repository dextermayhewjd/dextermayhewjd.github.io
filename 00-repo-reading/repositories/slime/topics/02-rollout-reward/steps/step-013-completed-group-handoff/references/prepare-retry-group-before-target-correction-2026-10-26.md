# 此前误展开的 prepare_retry_group 参考

用户随后澄清，希望补的是 _make_done_cb 的整体小骨架。本页保留助手上一轮对 helper 的静态说明，供按需回查；不能视为用户要求深入此函数或已读懂。

<a id="prepare-retry-group-skeleton"></a>

#### prepare_retry_group：为下次重试逐项选择输入

沿当前调用 `prepare_retry_group(retry_group, result)` 进入：inputs 接住外层准备的输入，results 接住这次 Task 返回的组。这里决定每个位置继续使用哪一个对象；返回后仍由父函数的 data_buffer.add_samples 提交。

下面来自 [base_types.py:107–122](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/base_types.py#L107-L122)：省略 docstring，仅将长条件换行，保留实际函数名、参数、list 判断、状态和 zip(strict=True)。

```python
def prepare_retry_group(inputs, results):
    return [
        (
            original
            if isinstance(result, list)
            and any(
                sample.status in (Sample.Status.ABORTED, Sample.Status.PENDING)
                for sample in iter_samples(result)
            )
            else result
        )
        for original, result in zip(inputs, results, strict=True)
    ]
```

| 每一项的情况 | 放进返回组中的对象 |
| --- | --- |
| result 是分段 list，且其中有 ABORTED/PENDING | 对应的 original 输入 |
| 其他情况 | 保留当前 result，包括普通 Sample 的部分生成结果 |

例如，某个位置已有完成结果 A，另一个位置返回了含 ABORTED 的分段列表 B；返回组就是 `[结果 A, 对应 B 的原输入]`。实际原输入可能来自外层保存的副本，不据变量名假定所有对象都经过深拷贝。

这个 helper 只组装并返回列表。接回父函数后，`self.data_buffer.add_samples([返回组])` 才将它交回输入端。iter_samples 的递归、会话为何不能续接以及深拷贝规则继续按需回查。此处为父卡内局部骨架，不新建独立函数卡；来源与实际讨论见[本轮过程](../04-flow.md#step013-retry-helper-skeleton)。

