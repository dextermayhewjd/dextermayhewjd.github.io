# Trace 的保存与查看

[返回 scope 的整体交接](../01-scope.md#trace-collection) · [返回 examples](../02-short-term-memory/examples/README.md)

这份参考只回答：已经写在内存里的 Trace 怎样保存、之后怎样查看。它不是新的 Trace API，也不是每次打点都要经过的全局收集器；需要导出或查看记录时再读。源码固定在 18868a79，以下命令是使用示例。

## 第一层：写入目标的内存容器

```text
目标是 Sample              → sample.trace["events"]
目标是 TraceHandle         → handle.carrier["events"]
目标是多个目标的列表        → 分别写进每个目标的容器
绑定的是独立字典 carrier   → 只留在该 carrier，调用者负责交付/保存
```

trace_utils 没有一个自动搜集全系统事件的全局队列。两个 ContextVar 栈用于确定当前目标/父阶段，实际事件保存在 carrier。export_trace/import_trace 也不会自动把远端 events 拉回本地。

## 第二层 A：通用 rollout debug dump

启用 --save-debug-rollout-data 后，正常生成路径是：

```text
RolloutManager._generate 取得 data
    → save_debug_rollout_data(path_template, data, ...)
    → 各 sample.to_dict() 保留 trace
    → torch.save({"rollout_id": ..., "samples": [...]}, path)
```

配置示例，仅展示保存参数，不在本轮启动训练：

```text
--save-debug-rollout-data /tmp/rollout_{rollout_id}.pt
```

当 rollout_id=0 时，文件是 /tmp/rollout_0.pt。其中第 i 个样本的事件位置为：

```text
dump["samples"][i]["trace"]["events"]
```

- path_template 为 None 时不写文件；内存里的事件仍可能存在。
- 这条路径保存传给 helper 的样本，不因此承诺保留此前被过滤掉的每次尝试。
- evaluation=True 时会从各评估分组提取样本。
- 文件名以 .straw.json 结尾时走 RolloutArchive.save 归档分支；它不是普通 .pt 或下文逐行 JSON。此处只定位，不声称查看器可直接打开该归档。

来源：[RolloutManager._generate:335–365](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L335-L365)、[保存函数:136–163](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/rollout_data_utils.py#L136-L163)、[Sample.to_dict:246–251](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L246-L251)。

## 第二层 B：Coding Agent 的每次轨迹 JSONL

当前业务还有一条独立的收集路径：

```text
examples/coding_agent_rl/generate.py::generate
    → finally（无论 _generate 正常返回还是抛出）
    → 检查 SWE_TRACE_DIR
    → 追加到 rollouts-<本工作进程标识>.jsonl
```

示例配置：

```bash
export SWE_TRACE_DIR=/tmp/slime-traces
```

这只是说明如何启用后续运行的写盘，不代表本轮已运行 Agent。环境变量未设置或为空时，不生成这些 JSONL 文件。

每次写入的一行包含：

```text
{
  "index": ...,
  "group_index": ...,
  "trace": base_sample.trace,
  "status": ...,
  "reward": ...,
  "response_length": ...,
  "metadata": ...
}
```

所以事件位于每行 record["trace"]["events"]。这条路径在返回给后续组过滤前就尝试写入，目标是覆盖包括被过滤或被打断的轨迹；写文件异常会记录日志。它与通用 rollout dump 的保存时机、样本范围不同。

来源：[generate:225–251](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L225-L251)、[Coding Agent 输出说明](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/README.md#outputs-and-restart)。

## 第三层：查看器读取已有文件

以下是使用示例，不在本轮执行：

```bash
python tools/trace_timeline_viewer.py /tmp/rollout_0.pt --no-serve

cat /tmp/slime-traces/rollouts-*.jsonl > /tmp/coding-traces.jsonl
python tools/trace_timeline_viewer.py /tmp/coding-traces.jsonl --no-serve
```

查看器支持 .pt 与 .jsonl，读取每个样本/记录里的 trace，再生成同名的 .trace_timeline_cache.json 和 .trace_timeline_viewer.html。它是消费已有记录，不会重新执行 Agent。

来源：[文件读取:571–589](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tools/trace_timeline_viewer.py#L571-L589)、[输出路径:615–622](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tools/trace_timeline_viewer.py#L615-L622)。

## 证据与认识边界

保存链路和查看器入口已按固定源码核对。此前用原 generate 配合业务替身，在临时目录核对正常和异常路径的 JSONL 追加；未运行真实 Agent、训练、实际 .pt 保存或时间线服务。案例的 expected.json 是教学快照，不是这些保存出口生成的日志。

用户仍表示对原 procedures 不清楚，本次只是调整归属，不记为已掌握两种保存时机。[本轮调整](../../step-014-agent-run-trace/04-flow.md#step014-procedures-retired)；原说明与验证边界保留在[历史稿](history/procedures/trace-collection.md)。
