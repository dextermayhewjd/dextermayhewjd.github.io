# apply_rollout_sample_hooks

- 源码定位：[slime/rollout/sample_hooks.py:52–64](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sample_hooks.py#L52-L64)。
- 首次接触：Step 010 的第三部分；2026-10-26 按用户要求展开。
- 最近认识更新：2026-10-26，用户将第三部分概括为获取样本后的二次处理；具体 hook 与字段继承机制尚待反馈。

[父函数 generate_and_rm 的结果后处理](../sglang_rollout.py/generate_and_rm.md#sample-postprocessing) → **本方法** → 返回父函数 `355` 再次继承任务上下文，随后判断评分责任。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：生成器已经返回结果，DP 上下文和 semaphore 的生成使用期已结束。框架在判断是否补奖励前，执行用户配置的样本后处理 hook。
2. **具体内容**：读取 hook 路径。没有配置则原样返回输入；有配置时，对单个 Sample 执行 hook 链，对列表逐项递归处理，接住修改或替换后的 Sample。
3. **建议构建的心智模型**：

   > 这是生成后的可配置处理入口：结果已经生成，框架把每个 Sample 交给 hook 按顺序处理，再把结果交回后续流程。没有配置 hook 时，不附加处理。

4. **调用代码**：

   ```python
   # generate_and_rm:353–355，使用同一个输入上下文快照
   sample = inherit_queue_context(queue_input, sample)
   sample = await apply_rollout_sample_hooks(args, sample, evaluation=evaluation)
   sample = inherit_queue_context(queue_input, sample)
   ```

## 本场景的输入与输出

**输入**：

- `args`：读取 `rollout_sample_hook_path`，由可重复的 `--rollout-sample-hook-path` 配置为路径列表，默认空列表。
- `value`：当前 Coding Agent 正常生成返回的 `list[Sample]`。调用处变量仍叫 sample，但已经可能是列表；通用接口还接受单个 Sample 和嵌套列表。
- `kwargs`：父函数传入 `evaluation=False`；配置 hook 时还补入当前 rollout_id，优先使用任务上下文中的值，否则使用模块默认值。rollout 上下文机制本轮只定位来源。

示例启动脚本没有显式配置样本 hook；按默认配置理解本场景时，paths 为空，直接返回同一个 value。本轮没有取得实际运行参数，不据此断言任何正在运行的作业都没有 hook。

**输出**：

| 条件 | 输出与对象关系 |
| --- | --- |
| 没有配置 hook | 原样返回 value，同一对象 |
| 配置 hook，输入单个 Sample | 返回 hook 链处理后选定的 Sample，可能是原对象，也可能是替换对象 |
| 配置 hook，输入列表 | 按原嵌套结构生成结果列表；叶子由单样本处理决定 |

不在这里选择评分器或执行框架补奖励。hook 自身的具体业务行为由配置函数决定，不能从这个入口推断它一定计算 reward 或修改某个字段。

### 1. 决定是否处理，以及按何种形状处理

真实入口：

```python
async def apply_rollout_sample_hooks(args, value, **kwargs):
    """Apply user hooks; the owning queue publication persists replay tensors."""

    paths = getattr(args, "rollout_sample_hook_path", None) or []
    if not paths:
        return value
    rollout_id = _task_rollout_id.get()
    kwargs.setdefault("rollout_id", rollout_id if rollout_id is not None else _current_rollout_id)
    if isinstance(value, Sample):
        return await _apply_to_sample(args, value, paths, **kwargs)
    if isinstance(value, list):
        return [await apply_rollout_sample_hooks(args, item, **kwargs) for item in value]
    raise TypeError(f"Rollout sample hooks expected Sample or list, got {type(value).__name__}.")
```

- 先看 paths：无配置时连后面的遍历都不做。
- 当前返回列表时，逐项递归到单个 Sample；此处按列表顺序 await，不新建一批并发 Task。
- 后面的每个 hook 接收一个 Sample，不是把整个列表作为一个参数交给单样本 hook。

### 2. 对一个 Sample 顺序应用 hook

`_apply_to_sample:37–49` 是本轮必要的下一层，先在本卡保留交接，不另建卡：

```python
for path in paths:
    hook = load_function(path)
    result = hook(args, sample, **_accepted_kwargs(hook, kwargs))
    if inspect.isawaitable(result):
        result = await result
    if result is not None:
        if not isinstance(result, Sample):
            raise TypeError(...)
        sample = result
return sample
```

这是教学裁剪，省略错误消息文本。hook 可同步，也可返回可等待对象；需要等待时才 await。`_accepted_kwargs` 只传入 hook 支持的关键字参数，接受 **kwargs 的 hook 则保留全部。

| hook 返回 | 链中的后续行为 |
| --- | --- |
| None | 继续使用当前 Sample；hook 已在原地做的修改仍然保留 |
| 一个 Sample | 用该对象接着执行下一个 hook |
| 其他类型 | 抛出 TypeError，不把错误结果交给后续评分 |

### 3. 接回两次任务上下文继承

[inherit_queue_context](../../data/transport.py/inherit_queue_context.md) 从生成前保留的输入中继承队列身份等字段。它按输出中的各个 Sample 操作，返回同一个输出容器，不把生成内容整体换回旧输入。

第一次继承覆盖生成器新建 Sample 的情况，第二次覆盖 hook 又替换 Sample 的情况。没有这些队列字段的普通输入不会凭空得到队列身份；完整队列协议和字段约束本轮暂不展开。

第二次继承完成后，父函数到 `358` 判断 group_rm，之后才检查是否需要补奖励。

### 局部验证与边界

2026-10-26，从固定源码原样提取 Sample 类、load_function、sample_hooks 模块及已有测试中的三个 hook，放在隔离命名空间执行。省去 NumPy/PyTorch 等未使用的模块导入；原方法体不改，未加载完整 Slime 运行环境。

```text
Unconfigured hooks: original Sample object returned
Configured sync + async hooks: nested shape preserved, metadata updated, unsupported kwargs filtered
Invalid hook result: TypeError propagated
```

配置实验采用已有测试场景的 evaluation=True 和 rollout_id=7，与正文当前正常训练参数不同。它用于核对接口行为，不是本次真实生成结果，也未运行模型、队列发布或训练。

## 我的直接表述（原话）

> 好的我大概理解了
> 其实这里就只是一个简单的控制层
> 核心的运行generate的部分还是解耦分开的
>
> 那么我们现在是否应该看一下这里的第三个部分了呢？
> 也就是这里的sample？
> 还有这里的apply rollout sample hooks这一个部分的内容吧

前半是对上一部分控制与实际生成分工的概括；后半确认第三部分的阅读范围。尚无 hook 内部机制的个人复述。

用户随后对这一阶段的概括与阅读要求：

> 简单来说就是获取sample之后二次处理对吗？
> 那么现在是否需要重新看一下这里的inherit queue context的部分呢？

已把这一概括作为阶段层面的理解保存；当前转入字段继承方法，不据此认定 hook 内部机制已经掌握。

## 尚不清楚

- 生成结果里的单个 Sample、列表容器及 hook 替换对象的关系，等待反馈。
- 当前任务实际配置了哪些 hook，尚无运行证据；已有示例未配置不等于所有作业都如此。
- rollout_id 上下文、队列身份字段的完整协议及具体业务 hook 的内部实现尚未展开。

<details>
<summary>来源与返回位置</summary>

- Slime 固定版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`：[入口和辅助函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sample_hooks.py#L30-L64)、[配置定义:537–545](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/arguments.py#L537-L545)。
- [任务上下文继承:207–230](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L207-L230)、[调用及后续评分:353–380](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L353-L380)。
- [已有测试样例](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/test_rollout_sample_hooks.py)。隔离验证不等于完整测试套件运行。
- [本轮过程](../../../../../04-flow.md#sample-postprocessing-reading)；读完回到父函数 355，再到评分判断。

</details>
