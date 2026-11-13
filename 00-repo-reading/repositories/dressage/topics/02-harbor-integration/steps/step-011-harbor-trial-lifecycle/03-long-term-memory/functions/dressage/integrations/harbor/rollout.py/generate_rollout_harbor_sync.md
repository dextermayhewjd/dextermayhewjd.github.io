> Step 011 补充继承（2026-11-11）：来自 [Step 010 收束时的完整记录](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/generate_rollout_harbor_sync.md)。原话、日期、来源与未知保留；继承不表示本步新增理解。

# generate_rollout_harbor_sync

- 源码：[dressage/integrations/harbor/rollout.py:1257–1277](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1257)。
- 首次单独展开：Step 010，2026-11-09。
- 本轮说明：先看批量入口、同步/异步交接和训练返回对象，内部批次流程暂不下钻。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：训练脚本将本函数配置为 rollout-function-path，由它组织本轮 Harbor rollout 批次。
2. **具体内容**：把参数和数据源交给异步 _run_harbor_rollout，等待 groups、metrics；根据 evaluation 和运行环境，返回训练输出、评估输出或兼容的裸 groups。
3. **建议构建的心智模型**：

   > 接住一轮批量 rollout 请求，交给 Harbor 集成流程执行，再把样本组和指标交回训练侧。

   这里的 sync 指入口同步等待异步批次结果，不表示 Harbor 内部逐个串行运行任务。

4. **调用入口配置**（训练脚本:66–67 的参数节选）：

   ```bash
   --data-source-path dressage.integrations.harbor.data_source.HarborDataSource
   --rollout-function-path dressage.integrations.harbor.rollout.generate_rollout_harbor_sync
   ```

## 本场景的输入与输出

<a id="batch-entry"></a>

### 1. 先区分新旧入口的层级

此前 blackbox_dispatch.generate 用作单次任务的 custom-generate-function；当前示例用 rollout-function-path 指向本函数，接管的是一轮批量 rollout。它不是要求每个 Harbor Trial 再跑一遍旧的 Paddock/BlackboxServer generate。

| 输入 | 当前先理解成什么 |
| --- | --- |
| args | 本轮训练/rollout 配置 |
| rollout_id | 当前批次轮次编号 |
| data_buffer | 外层传来的数据源对象；传到 _run_harbor_rollout 后形参叫 data_source，当前要求 HarborDataSource training 模式 |
| evaluation | 本轮先选 False，走训练返回分支 |

完整函数，只添加中文注释：

```python
def generate_rollout_harbor_sync(
    args: Any,
    rollout_id: int,
    data_buffer: Any,
    evaluation: bool = False,
) -> Any:
    """Run one strict Harbor rollout batch and return slime's public output."""

    # 交给异步批次流程；run 等它完成，接住两份结果。
    groups, metrics = run(
        _run_harbor_rollout(
            args,
            rollout_id,
            data_buffer,
            evaluation=evaluation,
        )
    )
    if evaluation:
        return _eval_output(groups, metrics)  # 评估路径本轮仅定位。
    if RolloutFnTrainOutput is None:
        return groups  # 兼容返回，不当作完整训练集成已验证。
    return RolloutFnTrainOutput(samples=groups, metrics=metrics)
```

### 2. 本轮只看一次交接

```python
groups, metrics = run(_run_harbor_rollout(...))
return RolloutFnTrainOutput(samples=groups, metrics=metrics)
```

groups 是 Sample 分组列表，metrics 是统计指标。单组如何组织、多段如何归组，后续按批次组织与结果转换入口看；当前不把每组直接等同于单个 Sample。

run 正常由 slime.utils.async_utils 导入；缺少相关导入时本文件定义 asyncio.run 兼容实现。这里先按“同步等待异步工作返回”理解，不重读已知异步工具内部。

本函数自己没有创建 Sandbox/Job，也不直接填 tokens；具体批次动作从 _run_harbor_rollout 展开。读到当前两个返回值与返回包装清楚即可，本轮已接续 [_run_harbor_rollout 的取组段](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md#load-source-groups)。

<a id="batch-owner-and-source"></a>

### 外层批次与任务来源：放回入口层理解

| 层次 | 负责什么 |
| --- | --- |
| Slime train 外层循环 | 按 rollout_id 反复调用 rollout hook，每次请求一批结果 |
| Dressage HarborDataSource | 读取 Harbor JobConfig，组织其任务/Agent 规格并按游标提供模板组 |
| _run_harbor_rollout | 组织当前这一批工作，处理各组结果与后续重试 |
| Harbor Job/Trial | 执行具体任务、Agent 和评测 |

```python
# Dressage 固定子模块 Slime aaf5c209 的 train.py:49–53，节选。
for rollout_id in range(args.start_rollout_id, args.num_rollout):
    # ... 可选评估。
    rollout_data_ref = ray.get(rollout_manager.generate.remote(rollout_id))
    # ... 本批训练、权重更新，再继续下一批。
```

Slime 控制何时要下一批，不因此成为题目来源；任务来自 Harbor JobConfig 指定的任务集/本地任务。管理器保留同一个 HarborDataSource，其 get_samples 推进游标，按配置打乱并在耗尽后循环。num_rollout 控制外层 rollout 轮数，rollout_batch_size 控制每批训练取组目标。

每次进入 _run_harbor_rollout 都重新建立本批 pending/completed/final_errors；内部 execution_round/group_retry 不改变本批 rollout_id。

来源：[Slime train.py:49](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/train.py#L49)、[RolloutManager hook 调用:647](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/ray/rollout.py#L647)、HarborDataSource.get_samples:277 与 _next_training_spec:467。这里保留之前回查所得背景，不新增 Slime 阅读步骤。

## 我的直接表述（原话）

> 好的 那么看一下这里的这个step10吧

随后用户概括：

> 简单来说这里的generate rollout harbor sync 就是一个启动函数
> 吧哪些组启动的交给harbor rollout
> 然后最后这里还有对应的evaluation的部分
> 然后你觉得
> 我下一个应该看一下这里的这个run harbor rollout了对吗?

助手核对：可把它理解为同步批次入口，委派执行并包装返回；但它尚未选好要启动的组。传入的是配置、批次编号、数据源与 evaluation，具体任务组由 _run_harbor_rollout 从数据源取得。evaluation 同时传入批次流程，并决定外层采用评估或训练返回形式；不是本入口自行运行全部评测逻辑。下一处建议看 _run_harbor_rollout 的训练分支取组位置，先不展开整个批次重试循环。

## 尚不清楚

- _run_harbor_rollout 如何从数据源取得分组、分配给 Harbor Job。
- Job 与插件怎样配合，后续在本步逐段定位。
- 结果组的详细构造留到后续结果转换范围，不在入口卡全部展开。

<details>
<summary>来源与验证</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- examples/harbor/run_harbor_training_qwen3.5_4b.sh:66–67 为数据源和批量 hook 配置；旧入口对照 examples/scripts/run_blackbox_qwen3.5_4b_sync_local.sh:128–129。
- rollout.py:60–68 为导入/兼容分支；:1026–1038 为数据源模式检查；:1257–1277 为当前完整函数。
- 静态核对，无训练、Harbor Job、网络或集群执行。当前阅读的是 Dressage 自己的集成文件，无需为本入口先下载完整 Harbor 源码。
- 形成过程：[Step 010](../../../../../../../step-010-harbor-rollout-entry/04-flow.md#start-step010)。

</details>
