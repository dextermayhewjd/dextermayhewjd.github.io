# 六个队列字段：在什么时刻加到哪个对象上

[返回 inherit_queue_context](../02-short-term-memory/functions/slime/data/transport.py/inherit_queue_context.md) · [此前字段总表](queue-context-fields-before-runtime-stages-2026-10-26.md)

本页固定在 Slime `18868a79`。先走一份全新任务通过 straw 队列读取的路径，再分别说明其他字段的出现条件。这里的流程是源码核对，未运行真实队列。

## 1. Sample 类没有声明，与实例后来拥有，是两件事

Sample 没有 slots 限制。创建普通 Sample 时可以没有下面的字段；后续代码仍可对同一实例执行属性赋值。

```python
sample = Sample(prompt="示例任务")
# 此时没有 _queue_lease
sample._queue_lease = {"task_id": "task-A"}  # 示意字段值，并非完整领取凭据
# 同一个实例现在有了 _queue_lease
```

使用真实 Sample 类的隔离实例验证：

```text
Declared dataclass field: False
Before assignment: hasattr = False
After assignment: hasattr = True
Instance value: {'task_id': 'task-A'}
```

这只验证属性可以动态附加，不表示已经领取队列任务。如果你看到的是 Sample 类定义，确实没有这六项；如果你检查的是某个运行实例，需要知道它是否已经过下面的队列读取路径。

## 2. 队列读取时，先加哪些字段

准确的方法归属是 **QueueReader.get_samples**，QueueDataSource 继承它。此前写成 QueueDataSource.get_samples 指的是通过子类调用继承方法，此处补准实际定义位置。

前提：已经启用队列数据源，队列返回一个 assignment，其中有本次领取的 lease，以及任务输入的存储引用 task.input_ref。下面摘自 queue_data_source.py:1080–1096：

```python
lease = assignment.lease
group = codec.load(assignment.task.input_ref, reader=session)
pristine = all(
    s.status == Sample.Status.PENDING and not s.response_length for s in iter_samples(group)
)
for sample in iter_samples(group):
    if pristine and not hasattr(sample, "_queue_original_input"):
        sample._queue_original_input = DiskPayloadRef(
            assignment.task.input_ref, self.args.rollout_data_dir
        )
    sample.__dict__.pop("_queue_receipt", None)
    sample._queue_lease = asdict(lease)
    sample._queue_source_positions = assignment.task.metadata.get("source_positions", [])
```

对于本页选定的“全新任务，原来没有队列字段”场景：

| 时刻 | 同一个输入 Sample 新增什么 | 为什么此时加 |
| --- | --- | --- |
| 取回任务输入、遍历 group 时 | `_queue_original_input` | 这时知道最初输入存在哪里；只在全部还未生成且没有旧引用时添加 |
| 领取任务后 | `_queue_lease` | 这时才得到本次领取凭据，之后提交结果要使用它 |
| 同一次读取中 | `_queue_source_positions` | 把任务 metadata 中的来源记录位置附到 Sample；全新任务可以是空列表 |

此处还会清掉旧的 `_queue_receipt`，因为重新领取的是一次新的任务授权，不应继续带着旧结果回执冒充当前身份。

这些赋值完成、方法返回 group 之后，生成侧拿到的实例已经可以包含上述三项。字段不是到 inherit_queue_context 才第一次出现。

## 3. 进入生成函数后，在快照上追加请求记录

sglang_rollout.py:316–325 先保存输入快照，再判断是否来自队列：

```python
queue_input = copy.copy(sample)
if hasattr(sample, "_queue_lease") or hasattr(sample, "_queue_receipt"):
    queue_input.queue_generation_requests = list(getattr(sample, "queue_generation_requests", [])) + [
        {
            "sampling_params": copy.deepcopy(sampling_params),
            "generate_function": sample.generate_function_path or args.custom_generate_function_path,
            "input_index": sample.index,
            "input_group_index": sample.group_index,
        }
    ]
```

`queue_generation_requests` 这次是加在 **queue_input** 上，保留本次生成的配置和输入编号；不是模型返回的一部分，也不是等待执行的任务队列。

于是，本例生成前的快照可以携带：原输入引用、领取凭据、来源位置、生成请求记录。仍然不要求有完成回执或 resume_origin。

## 4. 生成结果继承；并不是重新产生这些信息

生成器可能返回新的 Sample，或者返回多个 Sample。这些对象可能只有生成内容，没带齐输入的附加字段。

```text
queue_input：题目原输入引用 + 领取凭据 + 来源位置 + 生成请求记录
     │
     └─ inherit_queue_context ─→ 新结果 Sample：原生成内容 + 上述已有字段
```

这就是当前函数的职责。它不领取任务，不生成凭据，也不提交结果；它从 source 中读取已经存在的值，按检查规则附到输出上。hook 可能再次换对象，所以 hook 后再做一次。

## 5. 六项分别在什么条件下出现，后面为什么还需要

| 字段 | 添加时机与条件 | 具体用途 |
| --- | --- | --- |
| `_queue_lease` | QueueReader.get_samples 领取到 assignment 后，给本次输入写入 lease | pack_rollout_group 提交结果时，把它交给 controller.complete，标识当前任务尝试 |
| `_queue_source_positions` | 同一次读取，将任务 metadata.source_positions 写入；没有来源时写空列表 | 构建训练批次时汇总依赖的结果记录位置；后续返还任务也保留这些来源 |
| `_queue_original_input` | 同一次读取；group 全部 PENDING、尚无响应且该属性不存在时，保存原始输入引用 | 需要从 checkpoint 重新生成时加载原题，避免使用已被改写的输入 |
| `queue_generation_requests` | generate_and_rm 已保存 queue_input，且输入含 lease 或 receipt 时，在快照上追加 | 随结果保存本次采样参数和生成函数等记录；未查到以其重新调度生成的专用消费者 |
| `_queue_receipt` | 结果已接受并需要放回 Sample 时写入，例如 QueueReader.add_samples 查到 receipt、或 load_rollout_samples 物化已接受结果时 | 表示已经被接收的结果及其位置；后续追踪来源。不是“训练完成”的标记 |
| `_queue_resume_origin` | 当前仓库只找到继承和归档清理引用，未找到实际添加代码 | 具体业务语义与生产方未知；当前实例没有它时，继承逻辑跳过 |

receipt 的细节尤其要分开：straw 路径提交成功时，回执可以先存在返回的 RolloutGroupRef 中，不一定当场写进每个 Sample；物化或重新整理已接受结果时，才有把它附到 Sample 的代码。

## 6. 如果当前实例确实没有字段

先区分两种情况：

1. 只是在类定义中找不到：这不代表运行中不会添加，请看第 2、3 节的赋值位置。
2. 调试中的具体实例也没有：它可能尚未经过队列读取，或走的是不使用这些字段的普通数据源。inherit_queue_context 逐项跳过 source 中不存在的字段，不会凭空创建这六项的业务值。

现有 Coding Agent 示例脚本默认把 ROLLOUT_DATA_TRANSPORT 设为 straw；参数处理会在没有显式覆盖数据源时选择 QueueDataSource。这证明示例支持这条路径，不等于本轮已经取得用户实际运行配置或证明某个实例经过它。

六项不是每个阶段的必填集合。例如新领取时主动移除旧 `_queue_receipt` 并写入 `_queue_lease`，此时缺少 receipt 正常。仅当已确认实际路径在当前阶段要求某字段，缺失才需要回查上游；不能仅凭缺项断言出错。

## 7. 源码入口

- [Sample 定义](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L106-L170)；动态属性实验仅用了这个类。
- [QueueReader 及 get_samples](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/queue_data_source.py#L1002-L1100)；[QueueDataSource 继承关系](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/queue_data_source.py#L1280)。
- [生成前快照及请求记录](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L312-L325)。
- [继承函数与提交结果](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L207-L249)；[物化已接受结果](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L300-L318)。
- [add_samples 中写入回执、整理来源](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/queue_data_source.py#L1144-L1195)。
- [批次记录来源](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/batch_builder.py#L100-L118)；[恢复时加载原始输入](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/rewind.py#L51-L65)。
- [示例脚本默认传输配置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/run_qwen38_27b_fully_async.sh#L130-L134)；[数据源默认选择](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/arguments.py#L2006-L2014)。

这里补的是当前继承函数需要的字段来路，没有运行队列、提交任务、修改外部服务或另开上游阅读步骤。
