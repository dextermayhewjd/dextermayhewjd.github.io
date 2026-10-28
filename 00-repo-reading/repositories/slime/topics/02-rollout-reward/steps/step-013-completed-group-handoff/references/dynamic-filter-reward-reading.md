# call_dynamic_filter：过滤判定与已有奖励统计

[回到父函数卡](../02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md#dynamic-filter-interface) · [原始追问](../04-flow.md#step013-filter-reward-statistics)

当前只澄清 reward 相关代码与过滤调用的区别，不作为新增函数卡或完整过滤机制阅读。Slime 源码固定为 18868a79；下面是同一函数的三段摘录，省略了部分条件和上下文，按需回看[完整定义](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/filter_hub/base_types.py#L30-L46)。

## 1. 读取已有奖励，留下过滤前的统计

```python
trajectories = [sample[-1] if isinstance(sample, list) else sample for sample in samples]
if all(sample.reward is not None for sample in trajectories):
    rewards = [sample.get_reward_value(args) for sample in trajectories]
    reward_stats = (float(sum(rewards)), len(rewards))
```

- 每个元素若是一条轨迹的分段列表，取最后一个 Sample 作为奖励统计对象；普通 Sample 直接使用。这样一条轨迹只统计一次。
- all(...) 检查每条轨迹都有 reward；满足后才读取并汇总。
- rewards 是已有奖励值组成的列表；reward_stats 是奖励总和与数量。例如已有奖励 [0, 1, 1] 得到 (2.0, 3)，不产生新的单样本评分。
- 这段只在有动态过滤函数或批次过滤 hook 时尝试记录；条件不满足或缺少奖励时，reward_stats 保持 None。统计放在自定义函数调用前，因为自定义函数可能修改样本。

[Sample.get_reward_value:270–271](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L270-L271)实际只是读取 reward：

```python
def get_reward_value(self, args) -> float:
    return self.reward if not args.reward_key else self.reward[args.reward_key]
```

没有 reward_key 时取整个 reward；配置了键时从 reward 字典中取对应值。当前代码没有调用奖励模型。

## 2. 调用真正的过滤规则

```python
output = fn(args, samples, **kwargs) if fn is not None else True
```

fn 是父函数加载的动态过滤函数。这一层负责把组交给它，并接回保留判定；没有配置 fn 时默认保留。具体 fn 可以按奖励差异、任务有效性等条件筛选，不能仅从适配器推断实际业务规则。

例如仓库现有 [check_reward_nonzero_std](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/filter_hub/dynamic_sampling_filters.py#L9-L17)读取已有奖励，按组内奖励标准差是否超过阈值决定保留。这里只举筛选条件，不展开策略的训练原理。

## 3. 统一输出，交回父函数决定去向

```python
if not isinstance(output, DynamicFilterOutput):
    output = DynamicFilterOutput(keep=output)
return replace(output, raw_reward_stats=reward_stats)
```

兼容旧的布尔返回值，再附加过滤前的统计。父函数读取 verdict.keep 决定加入 collected 或执行丢弃处理；raw_reward_stats 留给 MetricGatherer 汇总。

## 书上怎么说

生成器表达式与列表推导式句法相似，常见区别是圆括号与方括号。[依据 A]

## 我的判断（本书未覆盖）

Slime 这里的 rewards = [...] 是列表推导式；all(... for ...) 的参数是生成器表达式，用来提供逐项检查结果。它们是遍历和组织已有数据的写法；是否产生新奖励取决于所调用的业务函数。此处 get_reward_value 只读字段，因此得到奖励列表不等于重新评分。

### 依据 A

- 《Fluent Python, 2nd Edition》第 2 章，Generator Expressions。
- 英文：/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/en/ch02.md:246–292，anchor：generator-expressions。
- 中文：/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/zh/ch02.md:231–277，2.3.4 生成器表达式，同一 anchor。
- 版本：本书基于 Python 3.10；当前本地 Python 3.12.3。
- 原文：“Genexps use the same syntax as listcomps, but are enclosed in parentheses rather than brackets.”
- 对照：“生成器表达式的句法跟列表推导式几乎一样，只不过把方括号换成圆括号而已。”

中英小节范围与引文已据本地镜像核对。Slime 业务结论依据上面链接的固定源码；未运行真实过滤插件。
