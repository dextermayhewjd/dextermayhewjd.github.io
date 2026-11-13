# 任务怎样领取对应预热池中的环境

[返回当前 scope](../01-scope.md) · [回到 start_warmpools 卡](../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.start_warmpools.md)

当前实现是“先确定 task，再按 task.image 选择池，申请一个环境”。它不是先扫描哪个池已经热好，再从任务列表里反向挑选任务。任务从 tasks 来，环境从池或相应模板来。

## 1. 执行器先拿到一个任务

[process_parallel](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L34)按传入任务列表逐项安排 _one(task)。在并发分支中会提交多个任务，但并未按池的 Ready 数量重新筛选任务。其核心调用为：

```python
handle = fleet.acquire(task)
# ... record runtime metadata ...
return process_fn(task, handle)
```

这段省略了原代码中 finally 的 release 和运行记录，只展示任务与环境的交接。process_fn 要等 acquire 返回 handle 后才开始。

## 2. 用 task.image 找到确定的目标池

[acquire](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1426)做本地并发额度预留后进入 [_acquire_reserved](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1464)。计划命中时，源码为：

```python
entry = self.plan_.for_image(task.image) if self.plan_ else None
on_demand = entry is None
if not on_demand:
    cluster = self.registry.get(entry.cluster)
    pool = entry.pool
```

1. for_image 按镜像检索既有计划。
2. 计划同时给出集群和池名。
3. 随后 SDK 的 create_sandbox 接收 warmpool=pool、namespace=cluster.namespace。

因此，镜像 A 的任务定向申请 A 对应的池；不会因为 B 池空闲就把这条任务分给 B 环境。若镜像不在计划中，普通模式可另建按需池；adopt_existing 模式会按相应限制报错。这与“目标池存在但暂时没有可用候选”是不同情况。

## 3. Claim 把池名交给控制器

[SDK create_sandbox](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox_client.py#L126)创建 SandboxClaim，[K8sHelper](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/k8s_helper.py#L102)将目标池写入：

```python
spec: dict[str, Any] = {
    "warmPoolRef": {
        "name": warmpool
    }
}
```

这是原代码片段，warmpool 来自上一步的池名。匹配发生在指定 namespace 和 warmPoolRef.name 下，不是向所有预热池随机申请。

```text
task.image
  -> FleetPlan.for_image(task.image)
  -> entry.cluster + entry.pool
  -> create_sandbox(warmpool=pool, namespace=...)
  -> SandboxClaim.spec.warmPoolRef.name
       -- Kubernetes reconciliation --> matching pool candidates
  <- claim bound + Ready
  <- SandboxHandle
  -> process_fn(task, handle)
```

## 4. 指定目标池后，是否一定热命中

| 控制器看到的情况 | 当前实现的处理 |
| --- | --- |
| 已有这个 Claim 的绑定 | 继续使用既有绑定，不重新分配 |
| 指定池中有可采用的 Ready 沙箱 | 优先采用，并将 Sandbox 的控制归属转给 Claim |
| 没有 Ready 候选，但有符合条件的未就绪候选 | 可能采用该候选；客户端仍需等待 Claim Ready |
| 没有可采用的池内候选 | 可以按该池引用的模板冷创建新 Sandbox |

[getCandidate](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L1166)优先选 Ready，并保留未就绪候选作为 fallback；尚未观察到 Pod IP 的候选存在有界重试。[getOrCreateSandbox](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L2230)尝试已有绑定和池内采用，[reconcileActive](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L580)在没有候选时走冷创建。[completeAdoption](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L1478)移除池成员标记并转移归属。

[SDK 等待逻辑](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox_client.py#L223)及 [wait_for_claim_ready](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/k8s_helper.py#L151)要等 Claim 既绑定 Sandbox、又显示 Ready，才继续交回句柄；超时或失败会抛错。指定 warmPoolRef 不是“只准热命中”的保证。池或模板不存在等错误也不等于必然成功冷创建。

<details>
<summary>本轮只定位的其他边界</summary>

1. Claim 的容器 env 或 volumeClaimTemplates 等自定义需求可能强制冷启动；本轮按示例无这些覆盖的普通领取路径核对。
2. 候选选择还会检查归属、模板版本和并发采用冲突；此处不展开这些内部算法。
3. 控制器不从训练任务队列挑题；它只处理已到达的 Claim。

</details>

## 5. 为什么当前 naive 路径通常先准备好再领取

run_naive 在 executor 前同步调用 setup；setup 用 wait=True 调用 start_warmpools。因此首次正常进入执行器前，预热过程已经等待所需池就绪。但开始领取后，库存会变化，仍可能出现未就绪或冷启动路径。

如果目标是“只挑环境已经 Ready 的任务来跑”，需要任务调度层维护按镜像划分的待执行任务和供给状态。这不是当前 process_parallel 的选择规则。当前实现提供的是按任务定向领取环境，而不是按现有环境反向调度任务。

## 来源与本轮边界

固定版本为 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。上述是跨接口的静态核对，没有发送 Claim、启动 Pod 或运行真实任务。这里用于回答任务与池的匹配问题，不代表所有被引用函数都已经逐行阅读，也不据此预建函数卡。
