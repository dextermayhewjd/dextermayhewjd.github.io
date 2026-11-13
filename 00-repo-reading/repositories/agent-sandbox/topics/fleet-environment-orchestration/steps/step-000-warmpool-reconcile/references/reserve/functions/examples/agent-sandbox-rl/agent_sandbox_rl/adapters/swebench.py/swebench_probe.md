# swebench_probe

[返回调用方 _record.fn](../../../examples/run_swebench_fleet.py/_record.fn.md) · [返回 process_parallel](../../strategies.py/process_parallel.md) · [本步 scope](../../../../../../../../01-scope.md#reading-navigation) · [本轮讨论](../../../../../../../../04-flow.md#swebench-adapter-entry)

- 源码定位：[adapters/swebench.py:97](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py#L97)。
- 首次接触：Step 000，2026-11-04，用户选择直接看 SWE-bench 部分。
- 最近认识更新：用户已概括具体执行与返回字段的作用；output 类型及业务层与沙箱层的分工仍在校准，完整表述保存在调用方 fn 卡片。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：沙箱已领取，调用方希望在其中执行一条轻量探针命令。
2. **具体内容**：通过 handle.exec 执行 SWEBENCH_PROBE，去掉返回文本两端的空白，交回字符串。
3. **建议构建的心智模型**：

   > 这是一个环境探针回调。它示范已领取的沙箱怎样被实际使用，以及一份命令输出怎样返回执行器；返回值是探针文本。

4. **调用代码**：当前 process_fn 实际指向 _record(swebench_probe) 返回的 fn。下面是 fn 内部直接调用本探针的代码，其中 probe 已绑定为 swebench_probe。完整实参来路见[process_fn 的传入关系](../../strategies.py/process_parallel.md#process-fn-origin)。

   ```python
   out = probe(task, handle)
   return {"instance_id": task.id, "image": task.image,
           "cluster": handle.cluster_name, "hostname": handle.hostname,
           "output": out}
   ```

## 本场景的输入与输出

### 1. 输入

以下为沿用当前任务接口的教学构造，没有实际执行沙箱命令。

| 输入 | 本例含义 |
| --- | --- |
| task | 数据加载产生的任务描述，例如 Task(id="t1", image="image-a", metadata={})；image 告诉 Fleet 需要哪类环境，本函数自身不读取 task |
| handle | 由 fleet.acquire(task) 返回的沙箱操作对象，提供 exec；它引用已领取的环境，本例假设执行后返回下面的文本 |
| SWEBENCH_PROBE | 模块定义的命令参数列表，源码见下方折叠区 |

假设 handle.exec 返回：

```python
"READY pod-demo\nabc1234 example commit\n"
```

### 2. 输出

本函数去掉末尾换行，返回：

```python
"READY pod-demo\nabc1234 example commit"
```

这是构造的输出示意，类型是字符串而非退出码。示例中的 _record.fn 再将这段文本放进 output 字段，并加入任务与环境标识；该字典才是该示例交回 process_parallel 的结果。

### 3. 完整函数主体

以下只省略 docstring。

```python
def swebench_probe(task, handle) -> str:
    return handle.exec(SWEBENCH_PROBE).strip()
```

1. [handle.exec](../../handles.py/SandboxHandle.exec.md) 使用已领取环境的 Pod、namespace 和容器信息，经 Kubernetes exec 通道执行命令并取得输出。
2. strip 去掉输出两端的空白字符。
3. 返回字符串，交回调用它的 _record.fn；随后回到执行器的释放流程。

#### 3.1 本次真正执行的命令

```python
SWEBENCH_PROBE = [
    "bash", "-lc",
    "echo READY $(hostname); git -C /testbed log -1 --oneline 2>/dev/null"
    " || ls -d /testbed 2>/dev/null || ls /",
]
```

1. 输出 READY 和主机名。
2. 尝试显示 /testbed 仓库的最近一条提交。
3. 上一步失败时，依次尝试显示 /testbed 目录或根目录内容。

命令包含目录回退路径，所以探针有输出并不能证明题目的全部依赖已经齐备或测试已经通过。

#### 3.2 输出怎样回到调用方

1. [SandboxHandle.exec](../../handles.py/SandboxHandle.exec.md) 在当前无持久会话的分支中调用 exec_in_pod。
2. exec_in_pod 使用 Kubernetes exec API 读取命令的 stdout/stderr 文本。
3. 文本返回到本函数，经 strip 后交回 fn 的 out，随后被包装进结果字典。

<details>
<summary>4. 回查：数据、环境与回调的位置</summary>

1. **数据变成任务描述**：[SweBenchSource.load](SweBenchSource.load.md) 从数据集取出任务 ID、镜像等信息，构造 Task。
2. **按任务需求准备环境**：Fleet 在 setup 等准备流程中按镜像规划并准备预热环境。
3. **领取并取得操作对象**：executor 调用 fleet.acquire(task)，取得 handle。handle 引用一个具体沙箱，不是数据加载函数的返回值。
4. **使用已领取环境**：executor 将 task 和 handle 交给 process_fn；本例经 _record.fn 调到 swebench_probe，执行固定探针命令。
5. **交回执行结果**：swebench_probe 返回文本，_record.fn 将它装入结果字典，随后 executor 释放环境并收集结果。

本例演示的是“根据数据集选择环境，并从环境中取得命令输出”。swebench_probe 本身不创建环境，也不执行解题 Agent 或完整评测。task 虽未在探针体内被读取，但其 image 已供前面的环境选择使用，id 等字段也用于外层结果记录。

三种 adapter 的职责对照见[项目 reference](../../../../../../../../../../../../references/rl-environments-and-jd.md#adapter-roles)。

</details>

## 我的直接表述（原话）

> 可以直接看一下这里的swebench的部分吗?
> 这里的3个adapter是不是差不太多呢?

以上为起点的阅读请求。用户随后对具体执行及返回标识作了概括，完整原话与 output 类型的校准见[调用方 fn 卡片](../../../examples/run_swebench_fleet.py/_record.fn.md)。

随后用户追问：

> 我不是特别理解这里在做什么?
> 这里在做的事情就是通过数据集构造task的情况下把这样子的一个环境返还给这里的作为handle的韩式只是作为一个具体的process fn来构建一个这样子的环境的呢?
> 我不是特别理解

## 尚不清楚

1. Task 描述、handle 操作对象与回调结果的区别，以及它们各自的来源，尚待用户反馈。
2. 本轮已定位 handle.exec 到 Kubernetes exec API 的路径；具体协议和异常分支尚未展开，当前解释待用户反馈。
3. SweBenchSource 的数据字段转换现已单独开始阅读；真实任务如何接入评分仍未展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 探针常量：adapters/swebench.py:33–37；函数：97–103；数据加载：66–94。
- 实际示例：examples/run_swebench_fleet.py:92–95；结果包装：116–123。
- 样例文本为教学构造；源码及返回结构经静态核对，没有执行下载、沙箱命令或评测。
- 原始过程：[Step 000 · 选择 SWE-bench](../../../../../../../../04-flow.md#swebench-adapter-entry)。

</details>
