# SandboxHandle.exec

[返回 swebench_probe](../adapters/swebench.py/swebench_probe.md) · [回调 fn](../../examples/run_swebench_fleet.py/_record.fn.md) · [本轮讨论](../../../../../../../04-flow.md#swebench-command-execution)

- 源码定位：[handles.py:314](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/handles.py#L314)。
- 首次接触：Step 000，2026-11-04，从 SWE-bench 回调的具体执行问题进入。
- 最近认识更新：本轮开始核对命令进入 Pod 的通道；尚无用户独立复述。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：swebench_probe 已收到已领取的 handle，通过本方法执行固定探针命令。
2. **具体内容**：确定目标容器，取得 Kubernetes 客户端，将命令交给 exec_in_pod，返回命令通道的输出文本。
3. **建议构建的心智模型**：

   > handle 已保存远端环境的定位信息。exec 使用这些信息将本次命令送进已运行的容器，读取输出后返回调用方。

4. **调用代码**：来自 swebench_probe。

   ```python
   return handle.exec(SWEBENCH_PROBE).strip()
   ```

## 本场景的输入与输出

### 1. 输入

选择当前非 recycle、未打开持久会话的正常路径，self._session=None。

| 输入或已有状态 | 本场景作用 |
| --- | --- |
| command | SWEBENCH_PROBE：一个 bash -lc 命令参数列表 |
| self.pod_name | 这条任务已领取环境对应的 Pod 名称 |
| self._cluster | 持有 namespace 及该集群的客户端 |
| container | 未指定，继续使用 target_container 或 runtime_container；本场景使用运行任务镜像的容器 |
| timeout | 未指定，默认 None |

task 没有作为本方法参数传入；这里需要的是命令和 handle 已有的环境定位信息。

### 2. 输出

1. 返回 exec 通道读取到的 stdout/stderr 文本，正常返回类型为 str。
2. 返回 swebench_probe 后，由其 strip() 去掉首尾空白。
3. 该文本再回到 fn 的 out，随后被放入结果字典的 output 字段。

本次只静态核对，没有向真实 Pod 发出命令。返回文本不自动表示测试成功或得到 reward。

### 3. 当前分支如何执行

下面从实际方法中裁剪未打开持久会话的正常分支，省略会话复用和异常诊断。

```python
# [1] choose the container
target = container or self.target_container or self.runtime_container

# [2] get the cluster client
core = self._cluster.exec_core_api()

# [3] execute in the selected pod
return exec_in_pod(core, self.pod_name, self._cluster.namespace, command,
                   container=target)
```

1. **[1] 选择容器**：优先使用本次显式参数，其次是 handle 的默认目标容器，最后是任务运行容器。
2. **[2] 取得客户端**：从 handle 所属集群取得当前线程使用的 CoreV1Api。
3. **[3] 提交本次命令**：将客户端、Pod 名、namespace、命令列表和容器名一起交给 exec_in_pod。

#### 3.1 跨到 Kubernetes 的位置

exec_in_pod 的以下调用是真正的 exec API 入口：

```python
out = stream(
    core_api.connect_get_namespaced_pod_exec,
    pod, namespace, command=command,
    stderr=True, stdin=False, stdout=True, tty=False,
    _preload_content=True, **exec_container_kwargs(container))
```

1. connect_get_namespaced_pod_exec 指定 Kubernetes 的容器内执行接口；本段不调用 kubectl 命令行。
2. stream 建立执行通道，将 command 交给指定 Pod 的容器执行。
3. stdout 和 stderr 被读取为输出；_preload_content=True 在该调用中收集通道内容。
4. exec_in_pod 将返回内容规范化为字符串，交回本方法。

<details>
<summary>暂未展开的分支</summary>

1. handle 上已有目标容器的持久会话时，exec 会改为调用 self._session.run。
2. 此版本的 timeout 参数只在会话分支生效；本例 timeout=None，使用一次性 exec 路径。
3. 发生异常时，方法调用 _raise_if_lost 核对环境失效，再继续抛出异常。
4. exec_in_pod 还处理字符串命令的 bash 包装，以及 None、bytes 等返回类型；本例输入已经是列表。

</details>

## 我的直接表述（原话）

本轮问题：

> 我想要了解的是这里的process_fn
> 在拿到了task和handle之后是如何具体的去执行的这个会比较重要
> 这里是swebench 的function
> 他是怎么做的

尚无对本方法的技术复述。

## 尚不清楚

1. 命令在 Pod 中执行、输出沿同一通道返回的关系，尚待用户确认。
2. 持久会话、超时及环境失效处理的内部机制尚未展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 当前方法分支：handles.py:337–347；exec_in_pod:53–73；客户端取得：cluster.py:84。
- 默认新 handle 的 _session=None，定义于 handles.py:307；本轮选择非 recycle 的执行路径。
- 源码静态核对；没有执行集群命令或测量实际输出。
- 原始记录：[Step 000 · SWE-bench 命令执行](../../../../../../../04-flow.md#swebench-command-execution)。

</details>
