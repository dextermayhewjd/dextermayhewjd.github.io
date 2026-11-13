> 2026-11-04：Step 000 收窄为第一步整体骨架之前的快照；链接按实际保存位置调整。

# main · run_swebench_fleet.py

[本步 scope](../../../../../../01-scope.md#reading-navigation) · [本脚本提供的回调](../../../../../../../../reserve/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/_record.fn.md) · [本轮讨论](../../../../../../../../../04-flow.md#run-swebench-script)

- 源码定位：[examples/run_swebench_fleet.py:47](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/examples/run_swebench_fleet.py#L47)。
- 首次接触：Step 000，2026-11-04，用户要求查看这个脚本的具体运行内容。
- 最近认识更新：本轮开始脚本入口与回调交接的阅读；尚无用户对这条调用关系的独立复述。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：直接运行 run_swebench_fleet.py 时，由文件末尾的入口调用 main。
2. **具体内容**：读取运行配置，创建 Fleet，加载 SWE-bench 任务，构造并传入探针回调，最后输出结果。
3. **建议构建的心智模型**：

   > main 把通用的 Fleet 与本例的数据来源、具体处理函数连接起来。它在这里决定 process_fn 是谁，再将整批执行交给 Fleet。

4. **调用代码**：

   ```python
   if __name__ == "__main__":
       main()
   ```

## 本场景的输入与输出

### 1. 输入

main 没有显式参数，主要从环境变量读取配置。本页以脚本默认分支定位执行关系；与此前两任务并发的教学例子区分。

| 配置 | 脚本默认值 |
| --- | --- |
| WARMPOOL_STRATEGY | naive |
| TASKS_LIMIT | 1 |
| MAX_CONCURRENT | 1 |
| PREPULL | 0，跳过独立预拉取 |
| REPORT_DIR | 空，跳过报告文件写入 |

完整集群、模板与数据集配置在原脚本中保留；本轮不逐项展开。TASKS_LIMIT 在脚本中取 0 表示读取全部，但直接调用 SweBenchSource(limit=0) 表示零条，两处语义不同。

### 2. 输出

1. main 自身隐式返回 None。
2. 向终端打印 JSON：strategy 是选定策略，tasks 是结果数量，results 是每条任务返回的记录列表。
3. 配置了 REPORT_DIR 且存在 fleet.report 时，额外写出报告的文本和 JSON 文件。

本次只阅读源码，没有下载数据、运行集群或产生真实任务结果。

### 3. 正常执行骨架

以下为教学裁剪，保留实际调用和可选分支，参数用省略号缩写。省略的环境变量读取已在输入部分定位。

```python
# [1] build configuration
template = TemplateSpec(...)
...
config = FleetConfig(...)

# [2] create the manager
fleet = SandboxFleet(config)

# [3] load tasks
fleet.load_tasks(SweBenchSource(...))

# [4] optional pre-pull
if prepull:
    fleet.preflight()
    fleet.plan()
    fleet.prepull(wait=True)

# [5] build the callback, then run the batch
results = fleet.run(_record(swebench_probe), strategy=strategy,
                    concurrency=max_concurrent)

# [6] print results
print(json.dumps({"strategy": strategy, "tasks": len(results),
                  "results": results}, indent=2))

# [7] optional report files
report_dir = _env("REPORT_DIR", "")
if report_dir and fleet.report is not None:
    _write_report(report_dir, fleet.report, strategy, len(results))
```

1. **[1] 配置**：第 48–82 行读取环境变量，创建模板配置、集群配置和 FleetConfig；这里创建的是配置对象。
2. **[2] 管理对象**：第 84 行构造 SandboxFleet，接回已读的 __init__。
3. **[3] 任务列表**：第 85–87 行先构造 SweBenchSource，再将它传给 load_tasks。load_tasks 经 to_tasks 调用 [source.load()](../../../../../../../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/SweBenchSource.load.md)，取得并保存 fleet.tasks；这一步在第 [5] 项 fleet.run 之前完成，更早于 run_naive 中的 setup。
4. **[4] 可选预拉取**：第 89–90 行，默认跳过；开启时先检查，再规划，然后预拉取。
5. **[5] 回调与执行**：第 92–93 行，先求值 _record(swebench_probe)，取得其返回的 fn；再将 fn 作为第一个实参交给 fleet.run。
6. **[6] 结果输出**：第 94–95 行，等 fleet.run 返回后打印结果列表。
7. **[7] 可选报告**：第 97–99 行，默认跳过。

### 4. 当前重点：第 [5] 行的两个时刻

为看清求值顺序，下面作等价拆写；callback 是讲解中新增的局部变量名。

```python
callback = _record(swebench_probe)
results = fleet.run(callback, strategy=strategy,
                    concurrency=max_concurrent)
```

1. 执行 _record 时，返回一个函数对象，此时还没有调用探针。
2. 进入 fleet.run 后，callback 由参数名 process_fn 接住。
3. 在默认 naive 分支中，Fleet 经 run_naive 进入 process_parallel。
4. 执行器取得 task 和 handle 后，才调用该函数对象。具体内容见 [_record.fn](../../../../../../../../reserve/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/_record.fn.md)。

## 我的直接表述（原话）

> 那么我们来看一下这里的run swebench fleet函数具体的运行内容吧

run_swebench_fleet.py 是脚本名，main 是其运行入口；本轮尚无对 main 执行关系的复述。

## 尚不清楚

1. 构造回调与逐任务调用回调的区别，尚待用户确认。
2. 数据加载已进入 SweBenchSource.load；资源配置和报告写入的内部实现仍未展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- main:47–99；入口调用:126–127；_record 与 fn:116–123。
- 本次只静态核对调用顺序；源码没有改动，也没有实际执行脚本。
- 原始记录：[Step 000 · 运行脚本与回调](../../../../../../../../../04-flow.md#run-swebench-script)。

</details>
