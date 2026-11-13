# main · run_swebench_fleet.py

[本步 scope](../../../01-scope.md#reading-navigation) · [接着看 run_naive](../../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) · [历史讨论](../../../04-flow.md#run-swebench-script)

当前 Step 000 通过 main 看输入、主要调用和输出；第一处构造调用配合 [SandboxFleet 类卡](SandboxFleet.md)阅读，回调、数据加载和资源管理的内部实现留在备用区。

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
3. **[3] 任务列表**：第 85–87 行将数据来源交给 load_tasks，取得并保存 fleet.tasks；这一步在第 [5] 项 fleet.run 之前完成，更早于 run_naive 中的 setup。本步先按这个接口理解。
4. **[4] 可选预拉取**：第 89–90 行，默认跳过；开启时先检查，再规划，然后预拉取。
5. **[5] 回调与执行**：第 92–93 行，先求值 _record(swebench_probe)，取得其返回的 fn；再将 fn 作为第一个实参交给 fleet.run。
6. **[6] 结果输出**：第 94–95 行，等 fleet.run 返回后打印结果列表。
7. **[7] 可选报告**：第 97–99 行，默认跳过。

### 4. 当前澄清：main 中没有 source 赋值语句

实际代码是 fleet.load_tasks(SweBenchSource(...))，执行关系为：

1. 先求值 SweBenchSource(...)，创建数据来源对象。
2. 将这个对象直接作为实参传给 fleet.load_tasks，不先赋给 main 中的 source 变量。
3. 进入 fleet.py:429 的 load_tasks(self, source, ...) 后，该对象由形参 source 接收；随后方法内调用 to_tasks(source)。

此前 scope 图里的 source = SweBenchSource(...) 是助手为展示而作的拆写，不是原始源码。现已改回嵌套调用。以上是静态源码澄清，尚无用户确认理解的反馈。

### 5. 当前第一处调用：fleet = SandboxFleet(config)

本次先看 main:84 的构造结果，按需回查已有的 [SandboxFleet.__init__ 记录](SandboxFleet.__init__.md)；不在这里展开全部初始化辅助调用。

1. Python 创建 SandboxFleet 实例，并调用其 __init__ 完成初始化；config 作为配置传入。
2. 初始化会复制配置、设置运行标识、准备集群客户端与放置策略，并建立任务及环境管理记录。
3. 构造完成后，main 中的 fleet 指向这个管理对象；__init__ 自身返回 None。

下面摘录 __init__ 中与当前交接直接相关的字段，省略其他初始化语句：

```python
self.tasks: list[Task] = []
self.plan_: FleetPlan | None = None
self._handles: list[SandboxHandle] = []
...
self._warmed: dict[str, int] = {}
```

此时任务列表为空，资源计划尚未生成，领取和预热记录也为空。这次构造没有创建远端 Sandbox、WarmPool 或 Pod；已存在的集群资源状况不能从这些本地空记录推断。下一行 load_tasks 才负责装入本批任务。当前先区分“管理对象已经初始化”和“环境已经准备好”，setup 的内部留到后续。

当前进一步回查构造入口的配置初始化（fleet.py:139–156）：

1. main 的 config 传入构造函数的同名形参；registry 未传，使用默认值 None。self 是正在初始化的新实例。
2. src = config or FleetConfig() 在本场景选用传入的配置；self.config 通过深复制保存该配置。
3. 随后构造函数会向 self.config.labels 写入本次运行标识，并应用运行隔离的命名设置。先复制可以避免这些修改直接改变调用方传入的配置对象。
4. 构造完成后，main 中的 fleet 指向该实例，因此构造函数里的 self.config 就是外部访问的 fleet.config。

这次只解释配置的交接与复制动机，集群注册表、命名和锁的内部实现继续保留在已有备用记录中；没有据此记录用户已经理解。

<details>
<summary>备用查阅：第 [5] 行的回调构造细节</summary>

为看清求值顺序，下面作等价拆写；callback 是讲解中新增的局部变量名。

```python
callback = _record(swebench_probe)
results = fleet.run(callback, strategy=strategy,
                    concurrency=max_concurrent)
```

1. 执行 _record 时，返回一个函数对象，此时还没有调用探针。
2. 进入 fleet.run 后，callback 由参数名 process_fn 接住。
3. 在默认 naive 分支中，Fleet 经 run_naive 进入 process_parallel。
4. 执行器取得 task 和 handle 后，才调用该函数对象。具体内容见 [_record.fn](../../reserve/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/_record.fn.md)。

</details>

## 我的直接表述（原话）

> 那么我们来看一下这里的run swebench fleet函数具体的运行内容吧

run_swebench_fleet.py 是脚本名，main 是其运行入口；本轮尚无对 main 执行关系的复述。

用户随后对图与源码的对应提出疑问：

> source = SweBenchSource(...)
> 哪里有这个部分呢?

本次选择从第一处调用继续阅读：

> 好的那么我们现在来看一下这里的这个fleet的部分吧
> 也就是这儿里的第一步吧

这次表述确认了阅读位置，尚未给出对构造结果的新理解。

## 尚不清楚

1. 构造回调与逐任务调用回调的区别，尚待用户确认。
2. 数据加载已进入 SweBenchSource.load；资源配置和报告写入的内部实现仍未展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- main:47–99；入口调用:126–127；_record 与 fn:116–123。
- 本次只静态核对调用顺序；源码没有改动，也没有实际执行脚本。
- 原始记录：[Step 000 · 运行脚本与回调](../../../04-flow.md#run-swebench-script)。
- 图与源码的对应纠正：[嵌套实参不是 main 的中间变量](../../../04-flow.md#nested-source-argument)。依据为固定版本的 run_swebench_fleet.py:84–87 与 fleet.py:429–436。

</details>
