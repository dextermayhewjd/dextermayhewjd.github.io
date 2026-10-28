# 六个 queue context 字段：来源、用途与继承规则

[返回 inherit_queue_context](../02-short-term-memory/functions/slime/data/transport.py/inherit_queue_context.md) · [当前 scope](../01-scope.md)

本参考绑定 Slime `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。这些字段不是 Sample 构造器统一要求的六个必填参数，也不是 inherit_queue_context 自己创造出来的业务值。上游队列和生成流程按阶段附加其中一些字段；本函数只负责检查并传递 source 中已经存在的信息。

## 1. 从整个生命周期定位

```text
队列把任务交给读取者
  → 输入 Sample 附上领取凭据、来源位置
  → 全新任务还保留原始输入的存储引用

generate_and_rm 开始
  → queue_input = copy.copy(sample)
  → 给 queue_input 补本次生成请求记录

生成器或 hook 返回新的 Sample
  → inherit_queue_context 把已有附加信息带到输出上

结果提交并被接受
  → 某些路径去掉领取凭据，写入完成回执
  → 后续构建批次、返还队列、恢复时读取相关信息
```

这是不同阶段的信息流，六项不必同时出现。再次领取一个任务也可能获得新的领取凭据，并清除旧回执；不能把 lease 与 receipt 当作固定并存的一对字段。

## 2. 逐字段核对

| 字段 | 具体保存什么、用来做什么 | 当前核对到的来源 | 后续使用依据 |
| --- | --- | --- | --- |
| `_queue_lease` | 当前这次领取任务的凭据。标识任务及本次尝试，提交结果时带回协调器 | `QueueDataSource.get_samples` 从 `assignment.lease` 取得，再 `asdict` 写到 Sample；1095 行 | `pack_rollout_group` 经 group_lease 取回，交给 controller.complete；transport.py:239–248 |
| `_queue_receipt` | 已被队列接受的结果回执，包含结果记录位置等信息；它不表示模型已经训练完 | 例如 `QueueDataSource.add_samples` 取到已有结果回执后写入；1150 行。结果物化或分布式生成路径也会写入 | batch_builder.py:103–104 读取 position；返还结果到队列时也可作为来源 |
| `_queue_source_positions` | 这个 Sample 依赖的已有队列结果记录位置列表，供后续保留来源关系 | get_samples:1096 从任务 metadata.source_positions 取得；add_samples:1175–1186 汇总原来源与已有回执位置 | batch_builder.py:100–118 将这些位置写入批次计划 input_positions |
| `_queue_original_input` | 原始题目输入在共享存储中的引用，不是另一份生成结果 | 输入尚未生成且无旧引用时，get_samples:1082–1091 用 assignment.task.input_ref 构造 DiskPayloadRef | rewind.regeneration_groups:60–65 加载原输入，恢复重新生成所需的题目，避免沿用被 hook 改过的内容 |
| `queue_generation_requests` | 本次及之前记录下来的生成请求信息：采样参数、生成函数路径、输入 index/group_index | generate_and_rm:317–325 在 queue_input 上追加本次记录 | inherit 将记录保留到结果；现有测试验证序列化后仍存在。当前未找到以它为输入再次调度生成的专用消费者，不将它说成执行队列 |
| `_queue_resume_origin` | 当前只能确认它是允许透传、并在归档读取时清理的字段 | 当前 checkout 全仓检索未找到实际写入处 | 只在 inherit 清单和 archive 清理清单中出现；具体生产方和业务语义仍待查，不能只按名字断定已经实现某种恢复机制 |

因此，前面把 `_queue_resume_origin` 简写成“恢复来源”不够严谨；目前只保留名称提示，实际来源明确标为未知。

## 3. 这些属性是怎样放到对象上的

队列读取路径中的真实代码节选：

```python
# QueueDataSource.get_samples：领取任务后附加动态属性
lease = assignment.lease
sample._queue_lease = asdict(lease)
sample._queue_source_positions = assignment.task.metadata.get("source_positions", [])
```

而当前生成调用的记录写在输入快照上：

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

这些是运行阶段按需要附加的属性。已有序列化数据也可以经 Sample.from_dict 恢复非 dataclass 字段；这不等于每个新 Sample 一开始都有这些字段。

## 4. “存在就 setattr”还缺少哪一步

源对象存在字段只是第一道条件：

1. source 没有该字段：跳过。
2. lease/receipt：目标已有不同值则抛错；没有冲突才深拷贝写入。
3. queue_generation_requests：source 有就用其深拷贝更新。
4. 其他三个字段：仅目标没有时补入，目标已有则保留。

最后返回原 output；不创建新容器，不修改回答、token 或 reward。

## 5. 本次查阅的源码位置

- [队列领取与输入附加字段](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/queue_data_source.py#L1069-L1099)。
- [回执写入与返还任务的来源整理](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/queue_data_source.py#L1144-L1195)。
- [生成请求记录](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L312-L325)。
- [提交结果使用 lease](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L233-L249)；[批次来源位置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/batch_builder.py#L100-L118)。
- [恢复时读取原始输入](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/rewind.py#L51-L65)；[归档去掉队列控制信息](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/archive.py#L187-L198)。
- [生成请求记录的保留测试](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/test_distributed_rollout.py#L1933-L1953)。该项本轮只读源码，未运行完整测试。

本轮是静态来源核对，不是队列端到端运行，也没有开启对这些上游函数的新阅读步骤。当前仍回到 inherit_queue_context 理解它为什么只传递已有字段。
