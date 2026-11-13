# _record.fn · SWE-bench 示例传入的 process_fn

[返回 main](../../../../../../../02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) · [调用它的 process_parallel](../../agent_sandbox_rl/strategies.py/process_parallel.md#process-fn-origin) · [它调用的探针](../../agent_sandbox_rl/adapters/swebench.py/swebench_probe.md)

- 源码定位：[examples/run_swebench_fleet.py:118](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/examples/run_swebench_fleet.py#L118)。
- 首次接触：Step 000，2026-11-04，从脚本实际传入的回调进入。
- 最近认识更新：用户已概括具体执行内容和返回的任务/环境标识；当前校准 output 的类型、业务回调与沙箱执行通道的分工，未据此认定内部机制已掌握。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：执行器已经取得一条 task 和对应 handle，调用当前 process_fn。
2. **具体内容**：调用绑定的 probe，取得输出，再加上任务和环境标识，返回一份字典。
3. **建议构建的心智模型**：

   > fn 使用已领取的 handle 执行探针，并将输出与任务、环境标识关联成一份结果。运行什么由具体回调及 probe 决定，实际执行通道由 handle 提供；_record 则负责预先创建这个回调。

4. **调用代码**：来自 process_parallel 的 _one；当前 process_fn 就指向这个 fn。

   ```python
   return process_fn(task, handle)
   ```

## 本场景的输入与输出

### 1. 输入

| 内容 | 本例含义 |
| --- | --- |
| task | 执行器传入的当前任务，提供 id、image |
| handle | 执行器传入的已领取沙箱，提供 cluster_name、hostname 和执行接口 |
| probe | 创建 fn 时由 _record 保存，本例绑定为 swebench_probe |

### 2. 输出

返回字典中的字段如下：

| 字段 | 来源与含义 |
| --- | --- |
| instance_id | task.id，标识当前题目/任务 |
| image | task.image，本任务使用的镜像标识 |
| cluster | handle.cluster_name，所属 Kubernetes 集群的名称 |
| hostname | handle.hostname，本实现取 Sandbox 资源名，作为集群内访问名；不是承载它的节点名称 |
| output | probe 返回的命令输出字符串，已去掉首尾空白；不是数字退出码 |

调用如果抛出异常，fn 不会构造这份正常结果字典；异常沿调用链交给外层执行器处理。正常返回后，执行器进入释放流程，再将结果存到对应任务的位置。此字典是执行记录，字段中没有自动计算的 reward。

<a id="execute-after-input"></a>

### 3. 收到 task 和 handle 后实际执行什么

当前只看已经被执行器调用的 fn。这里的 probe 已绑定为 swebench_probe。

```python
def fn(task, handle):
    out = probe(task, handle)  # [1]
    return {"instance_id": task.id, "image": task.image,
            "cluster": handle.cluster_name, "hostname": handle.hostname,
            "output": out}   # [2]
```

1. **[1] 执行固定探针**：进入 [swebench_probe](../../agent_sandbox_rl/adapters/swebench.py/swebench_probe.md)，它把 SWEBENCH_PROBE 命令交给 handle.exec。具体进入 Pod 的通道见 [SandboxHandle.exec](../../agent_sandbox_rl/handles.py/SandboxHandle.exec.md)。
2. **[2] 包装输出**：取回文本后，读取 task 的 id/image 和 handle 的环境标识，把它们与 out 一起放进结果字典。

这里的职责分为三层：

1. 具体回调与 probe 决定运行什么、怎样组织返回结果。本例的命令在 adapters/swebench.py 中，结果字典的包装在示例脚本的 fn 中。
2. handle.exec 提供把命令送入指定容器并读回输出的通用通道。
3. Fleet 和执行器负责环境准备、领取、任务安排与释放。

本例中 task 的题目内容没有参与命令选择；每条任务在自己领取的环境里运行同一组探针命令。工作负载相关的回调通过 handle 接口使用沙箱，而不是把整个执行基础设施都实现到 adapter 中。

<details>
<summary>回查：fn 如何由 _record 创建并传出</summary>

下面保留 _record 和其内层 fn 的全部执行语句，只省略 docstring。

```python
def _record(probe):
    def fn(task, handle):
        out = probe(task, handle)
        return {"instance_id": task.id, "image": task.image,
                "cluster": handle.cluster_name, "hostname": handle.hostname,
                "output": out}
    return fn
```

1. main 调用 _record(swebench_probe)，定义并取得 fn，此时不执行 fn 的函数体。
2. fn 传入 fleet.run，之后由执行器逐任务调用。

看完回到 main:92 的调用关系；完整批次结果由 fleet.run 返回，main 再打印。

</details>

## 我的直接表述（原话）

<details>
<summary>此前关于函数来源和执行位置的追问</summary>

此前对函数来源的追问：

> 还是说这里的这个process fn是被传入进来的呢?
> 然后这个传入的process_fn?
> 我不是特别理解了?

本轮用户要求查看 run_swebench_fleet 的具体运行内容，尚未对该回调作技术复述。

随后明确：

> 我想要了解的是这里的process_fn
> 在拿到了task和handle之后是如何具体的去执行的这个会比较重要
> 这里是swebench 的function
> 他是怎么做的

</details>

本轮用户概括：

> 好的我大概理解了
> 也就是这里的其实是一个非常具体的内容
> 包括了这一个环境应该运行什么和返回什么内容也是这个task具体是哪一个问题
> task id
> 以及环境
> image
> 在哪一个cluster
> 还有哪一个hostname (属于k8s)的范畴
> 还有output是什么(这个或许是0或者报错之类的?)
> 我是这么理解的
>
> 简单来说就是把这个执行的过程全部都放到了这里的这个adapter这里
> 是我的理解
>
> 里面具体是如何做的是这个问题特定的相关的
> 和sandbox本省或许每uyoushenmetebiede相关性是我的理解

## 尚不清楚

1. return fn 与 fn 内部返回字典这两次交付的区别，尚待用户反馈。
2. output 文本、退出码和外层异常的区别，尚待本轮校准后的反馈。
3. 用户已概括业务执行与结果字段；其与通用沙箱能力的分工，以及固定探针和按题目解题的区别，仍需保留边界。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 工厂与闭包：run_swebench_fleet.py:116–123；构造及传入：92–93。
- 执行器调用：strategies.py:52；探针实现：adapters/swebench.py:97–103。
- 这里用 _record.fn 表示嵌套函数的来源，不表示它能从模块顶层直接导入。
- 本次为静态源码核对；未运行集群或下载数据。
- 完整记录：[Step 000 · 运行脚本与回调](../../../../../../../04-flow.md#run-swebench-script)。

</details>
