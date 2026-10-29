# call_dynamic_filter

- 源码定位：[filter_hub/base_types.py:30–46](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/filter_hub/base_types.py#L30-L46)，固定版本 `18868a79`，由助手核对。
- 首次接触：Step 013 第四步，先作为 _generate_rollout_async 的过滤接口定位；2026-10-26 用户确认独立建卡。
- 最近认识更新：2026-10-26，用户将整体作用概括为“通过这种方式做到比较高效的筛选”。已记录筛选职责的理解；源码支持统一接口和可替换规则，运行效率未做测量，具体三段机制仍按已表达内容保留边界。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：父函数已经取到一个完成的 group，需要调用配置的过滤器，得到可供分支判断的统一结果。
2. **具体内容**：按条件保存过滤前的奖励总和与数量，调用 fn，再把结果统一为 DynamicFilterOutput 并附上统计。是否加入 collected 由父函数决定。
3. **建议构建的心智模型**：

   > 这是组级过滤的适配入口：**读取已有奖励统计 → 调用过滤规则 → 统一返回判定**。
   >
   > 奖励统计记录调用前的数据；实际保留规则由 fn 决定。这里的 reward 读取代码不调用奖励模型。

4. **调用代码**（_generate_rollout_async:314–315）：

   ```python
   verdict = call_dynamic_filter(dynamic_filter, args, group)
   metric_gatherer.on_group_completed(verdict)
   ```

   返回后，父函数读取 verdict.keep 决定保留或丢弃；raw_reward_stats 先交给统计器。见[父函数收集阶段](../../fully_async_rollout.py/_generate_rollout_async.md#collect-filter-retain)。

## 本场景的输入与输出

**教学构造，静态推导**：沿用父卡中会被丢弃的 G8。假设这一组有两个普通 Sample，已有奖励都是 0.0；加载好的 fn 本次返回布尔值 False。这里只指定其返回结果，具体业务规则仍留白。

| 输入 | 本例内容 |
| --- | --- |
| fn | 父函数加载的过滤函数；本次返回 False |
| args.reward_key | None，直接读取 Sample.reward |
| args.rollout_sample_filter_path | None；本例因为 fn 非空而进入统计分支 |
| samples | G8，由两个 Sample 组成，两者 reward 均为 0.0 |
| kwargs | 空；当前父函数没有传额外关键字参数 |

**返回值**：

```python
DynamicFilterOutput(
    keep=False,
    reason=None,
    keep_when_insufficient=False,
    raw_reward_stats=(0.0, 2),
)
```

其中 keep 来自 fn 的布尔返回值，raw_reward_stats 是调用 fn 前读取的奖励总和与数量。reason 和 keep_when_insufficient 沿用类的默认值；后者属于其他调用路径可能使用的策略字段，本步父函数只直接检查 keep。

<a id="function-body"></a>

### 对应函数：完整执行体与三段标记

以下保留原函数的签名、逻辑和原注释，只增加①②③中文标记；不是重新实现的过滤函数。

```python
def call_dynamic_filter(fn, args, samples, **kwargs):
    # ① 保存过滤前的已有奖励统计
    reward_stats = None
    if fn is not None or getattr(args, "rollout_sample_filter_path", None) is not None:
        # Context-window segments share one outcome; count the terminal reward
        # once per trajectory, before a custom filter can mutate it.
        trajectories = [sample[-1] if isinstance(sample, list) else sample for sample in samples]
        if all(sample.reward is not None for sample in trajectories):
            rewards = [sample.get_reward_value(args) for sample in trajectories]
            reward_stats = (float(sum(rewards)), len(rewards))

    # ② 调用配置的过滤函数；没有配置则默认保留
    output = fn(args, samples, **kwargs) if fn is not None else True

    # ③ 统一返回类型，再附上统计
    # compatibility for legacy version
    if not isinstance(output, DynamicFilterOutput):
        output = DynamicFilterOutput(keep=output)

    return replace(output, raw_reward_stats=reward_stats)
```

- **① 统计已有奖励。** 有 fn 或批次过滤 hook 时才尝试统计。samples 的某个元素若是分段列表，就取最后一段作为该轨迹的统计对象；普通 Sample 直接使用。所有对象都有 reward 才计算总和与数量，否则保留 None。
- **② 调用实际规则。** 有 fn 就把同一份 samples、args 和额外参数交给它；没有 fn 则得到 True。fn 可以读取或修改样本，所以统计先于它执行。这里不规定所有过滤器都按同一种“数据质量”标准筛选。
- **③ 统一返回。** 已是 DynamicFilterOutput 时保留其字段；旧式布尔结果被装入 keep。最后 replace 创建一个新结果对象，保留其他字段并设置 raw_reward_stats；如果 fn 自带同名统计，这里也会用步骤①的值覆盖。

本例的数据变化：

```text
已有 reward：0.0、0.0
    → reward_stats = (0.0, 2)
    → fn(...) 返回 False
    → 统一为 keep=False 的判定，附上统计
    → 返回父函数，进入丢弃分支
```

<a id="branch-boundaries"></a>

### 两个容易混淆的边界

| 情况 | 本函数的行为 |
| --- | --- |
| 没有 fn，也没有批次过滤 hook | 默认 keep=True，raw_reward_stats=None |
| 没有 fn，但有批次过滤 hook | 仍默认 keep=True；可先统计已有奖励，hook 本身稍后才执行 |
| fn 返回 DynamicFilterOutput | 保留 keep、reason 等字段，附上当前统计 |
| 任一统计对象缺少 reward | raw_reward_stats=None；这项检查本身不会替代 fn 作保留决定 |

[Sample.get_reward_value:270–271](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L270-L271)只是读取已有 reward 或其中指定的键。因此构造 rewards 列表是收集已有分数，不是计算新的奖励。推导式与生成器表达式的补充解释见[已有参考](../../../../../../../../../02-rollout-reward/steps/step-013-completed-group-handoff/references/dynamic-filter-reward-reading.md)。

## 我的直接表述（原话）

用户对用途及 reward 部分提出的理解和疑问：

> 那么这里需要需要单独看一下这里的call dynamic filter吗？这里的机制吗？
> 还是说简单理解为这里按照这里的数据质量可以简单做一个过滤方法吗？
> （不过这里里面看下来感觉耕读的偶尔就像是一个通过迭代器直接生成这里的reward部分？

随后澄清问的是卡片归属，并确认独立建卡：

> 我的意思是需要单独看一下这里的
> call dynamic filter的部分是否需要单独在这里开一个short term memory 是这个意思

> 好的那么生成一个这样子short term memory 以及对应的函数吧

用户阅读卡片后对整体作用的概括：

> 反正就是通过这种方式
> 来做到了一种比较高效的筛选方式
> 可以这么理解吗？

[本次概括与性能边界](../../../../../../../../../02-rollout-reward/steps/step-013-completed-group-handoff/04-flow.md#step013-filter-purpose-versus-performance)。

## 尚不清楚

- 用户已概括整体筛选作用；尚未独立说明过滤前统计、实际规则调用与输出适配三者的区别。
- 具体 fn 怎样判断一个组是否应保留；本例返回 False 是教学设定。
- 分段轨迹为什么以末段奖励统计、MetricGatherer 怎样汇总，以及 keep_when_insufficient 在其他调用路径中的用途；当前保留边界。

<details>
<summary>来源、验证与完整例子</summary>

- [实际定义与输出类型](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/filter_hub/base_types.py#L5-L46)；[当前调用与返回后的分支](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L297-L330)。
- [父函数卡](../../fully_async_rollout.py/_generate_rollout_async.md#dynamic-filter-interface)保留调用位置与组的最终去向；[本步 scope](../../../../../../../../../02-rollout-reward/steps/step-013-completed-group-handoff/01-scope.md#reading-order)保留阅读导航。
- [本次确认与建卡](../../../../../../../../../02-rollout-reward/steps/step-013-completed-group-handoff/04-flow.md#step013-filter-card-created)；[此前记录粒度澄清](../../../../../../../../../02-rollout-reward/steps/step-013-completed-group-handoff/04-flow.md#step013-filter-separate-card-question)。
- 函数执行体按固定版本源码保留；示例为静态推导，未运行真实过滤插件、worker 或训练。

</details>
