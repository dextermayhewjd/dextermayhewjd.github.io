# RolloutManager.eval

> **面包屑**：[Step 017](../../../../../01-scope.md#reading-order) → [train 的周期评估](../../../train.py/train.md#periodic-evaluation) → **本函数** → [返回主循环](#eval-return)。

- 源码定位：[slime/ray/rollout.py:392](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L392)；调用方 train.py:98–99。
- 首次单独记录：Step 017，2026-10-31；此前只在 train 父卡中定位。
- 最近个人认识：2026-10-31，用户已概括通过 rollout 函数取得评估数据、按配置保存调试数据并记录结果；本步所需的职责模型已有直接表述，具体评分和运行验证仍保留边界。

## 1. 定位：本轮权重同步后，按需检查模型表现

主循环完成本轮训练和权重同步后，判断是否到评估时点。条件满足才调用这里，并通过 ray.get 等待处理结束；条件不满足则跳过。

本步保留评估的职责、输入输出和主循环位置。评估数据集、评分细节、健康检查和服务资源清理的内部机制按需回查。

## 2. LLM 整理：使用场合、具体内容与心智模型

### 2.1 使用场合

按配置的间隔检查当前模型表现，形成可记录、可比较的评估结果。

### 2.2 具体内容

以 evaluation=True 调用已经配置好的评估生成实现，取得评估数据和指标；必要时整理共享生成服务的状态，再按配置保存调试数据并记录评估结果。正常结束返回 None。

<a id="mental-model"></a>

### 2.3 建议构建的心智模型

> 在选定的训练轮次，用当前模型完成一次评估，并整理、记录结果。它是训练主线中的检查环节，不负责再次训练或更新模型权重。

#### 2.3.1 主循环：到了评估时点才调用

```python
if should_run_periodic_action(rollout_id, args.eval_interval, num_rollout_per_epoch):  # 是否到评估时点
    ray.get(rollout_manager.eval.remote(rollout_id))  # 调用评估并等其处理结束
```

**这一段完成什么**：控制评估频率。eval_interval=None 时关闭；启用后，按指定间隔或 epoch 边界触发。该判断属于调用方，不在本方法中。

#### 2.3.2 评估入口：取得结果并记录

下面是阅读用伪代码，保留真实函数名、字段和执行顺序；省略设置日志轮次、健康检查和具体保存参数，不是独立可运行程序。

```python
RolloutManager.eval(rollout_id)  # 本次评估使用的轮次编号
    if self.args.debug_train_only: return None  # 只调试训练时跳过评估
    ...  # 设置当前轮次，恢复本轮健康监测
    result = call_rollout_fn(
        self.eval_generate_rollout, self.args, rollout_id, self.data_source,
        evaluation=True,  # 让配置好的实现走评估路径
    )
    if self.serving is not None:
        self.servers = ray.get(self.serving.finish_rollout.remote())  # 整理共享服务状态
    data = result.data  # 取得评估数据
    save_debug_rollout_data(..., evaluation=True)  # 按配置保存调试数据
    log_eval_rollout_data(rollout_id, self.args, data, result.metrics)  # 记录评估结果
    return None  # 本轮评估处理结束；原方法为隐式返回
```

**这一段完成什么**：把“执行评估 → 整理结果 → 记录结果”组织起来。评估结果用来观察模型表现；本方法没有调用训练组做梯度更新。

### 2.4 调用代码与返回位置

主调用见 2.3.1。外层 ray.get 等待的是本次 eval 调用完成，不接收一份新的训练 batch；本方法正常返回 None，主循环没有保存这个返回值。

## 3. 本场景的输入与输出

### 3.1 输入与中间结果

| 项目 | 内容与用途 |
| --- | --- |
| rollout_id | 标识本次评估所属的训练轮次 |
| self.eval_generate_rollout、args、data_source | 已配置的评估实现、参数和数据源 |
| result.data | 评估数据；供保存和记录使用 |
| result.metrics | 评估实现提供的可选指标；交给日志函数 |

call_rollout_fn 在 evaluation=True 时统一接收 RolloutFnEvalOutput；评估实现返回字典时，包装为其 data 字段。这里只核对接口，不展开每种数据集的内部结构。

### 3.2 最终输出与副作用

- **返回值**：正常返回 None；debug_train_only 分支也直接返回 None。
- **主要结果**：记录评估结果，按配置保存调试数据；使用 serving 时整理共享服务并更新本地服务器句柄。
- **运行证据**：以上来自静态源码，本轮没有实际评估分数、文件产物或模型运行结果。

<a id="eval-return"></a>

### 3.3 返回主循环

回到 train.py:99，外层等待结束；当前循环体随后结束。还有下一轮就继续生成和训练，没有下一轮则离开 train。当前只需知道评估在本轮权重同步之后的位置。

## 4. 我的直接表述（原话）

> 好的 但是我觉得这一块更多的就只是一个做一下评估方面的内容
> 你现在以及收录了这里的function的short term memory了吗??

用户已将这段与评估用途联系起来；请求检查记录是否存在，不等于已确认所有实现细节。

用户随后对职责的直接表述：

> 这里基本上就是 评估的部分希望通过这里的rollout fn 还有eval的以西类步骤
> 获取到这里的评估数据
> 并且配置保存调试数据
> 最后记录评估的结果
>
> 这是我对于这里rolloutmanager eval的理解
> 那么我们现在还有什么需要做的吗?
> 或者有什么需要看的吗?
> 还是这里对于slime的部分就告一段落了?

这段与本函数的正常职责一致；“按配置保存”保留可选调试输出的含义。由此按本步范围收束正常主线，未将详细评分、资源管理或真实评估运行记为掌握。见[本轮收束](../../../../../../step-017-generation-training-loop/04-flow.md#normal-loop-reading-closure-20261031)。

## 5. 尚不清楚

- 具体评估数据、评分算法和指标含义，本步不展开。
- 共享服务清理、健康监测与调试文件保存的内部机制，按需回查。
- 错误路径、真实评估结果与实验复跑，尚未验证。

## 6. 来源、验证与完整例子

<details>
<summary>源码与形成过程</summary>

- 固定版本 18868a79：train.py:98–99；RolloutManager.eval:392–412；call_rollout_fn:28 起的 evaluation 分支；should_run_periodic_action:119–140。
- 当前 checkout 540ea919 的相关方法用于静态对照；未运行 Ray、模型或评估。
- [本轮独立记录](../../../../../../step-017-generation-training-loop/04-flow.md#eval-short-term-card-20261031)。

</details>
