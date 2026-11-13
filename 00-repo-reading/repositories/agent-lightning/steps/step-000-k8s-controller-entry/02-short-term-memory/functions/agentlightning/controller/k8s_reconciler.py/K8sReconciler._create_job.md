# K8sReconciler._create_job

> **调用链面包屑**：[Step 000 范围](../../../../../01-scope.md) · [短期函数索引](../../../../overview.md) → [_reconcile_once 的无 Job 分支](K8sReconciler._reconcile_once.md#call-create-job) → **_create_job** → [build_job_spec（源码）](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43)

- 源码：[k8s_reconciler.py:242](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L242)；骨架编号 [2]。
- 首次实际阅读：Step 000，2026-11-03。本次用户明确选择进入；此前同名未读备稿已撤回，不作已读依据。
- 最近认识更新：2026-11-03，用户将本函数概括为通过 manifest 创建 Job，并询问其他部分是否可以暂不深究。用途已有初步表述，底层实现继续留白。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：父函数没有找到对应 Job，且当前 rollout 仍是 `QUEUING`，于是把这条完整任务交进来。
2. **具体内容**：检查当前控制器的创建速率，构造 Job 配置，使用 Kubernetes 客户端提交，并登记本次成功创建的时间。
3. **建议构建的心智模型**：

   > 把一条待执行任务转换成 Job 创建请求，并提交给 Kubernetes。具体运行由 Kubernetes 承接；本函数正常返回 `None`。

4. **调用代码**（父函数 179–182 行）：

   ```python
   if job is None:
       if rollout.status.state == RolloutState.QUEUING:
           await self._create_job(rollout)
           continue
   ```

## 本场景的输入与输出

沿用教学任务 r1。假设 Job 模板有效、创建额度允许、API 请求成功；下表为字段节选，没有运行集群。

| 输入或前提 | 本例含义 |
| --- | --- |
| `rollout.rollout_id` 为 `"r1"` | 生成与关联 Job 名称的任务标识 |
| `rollout.input` | 当前任务的输入，可供模板使用 |
| `rollout.config.k8s.job_template` | 用来构造 Job manifest 的模板 |
| `self._config` | 控制器的 namespace、运行约束和服务连接配置 |
| `self._job_creation_timestamps` | 当前控制器近期成功创建 Job 的时间记录 |

**正常输出**：提交名为 `agl-rollout-r1` 的 Job 创建请求；请求成功后登记创建时间，返回 `None`。成功路径不会在这里把 Gateway 的 rollout 状态立即写成 `RUNNING`，也不等待 Pod 中的整个工作完成。

### 本函数的骨架

教学裁剪：日志、异常诊断与细节折叠，保留创建额度判断和正常交接。参数省略处可由后面的入口表回查。

```python
job_name = build_job_name(rollout.rollout_id)
...  # 清除 60 秒窗口之前的创建时间
if len(self._job_creation_timestamps) >= self._runner_config.max_jobs_per_minute:
    return

manifest = build_job_spec(rollout, self._config)
...  # 从 manifest 的标签取得 attempt_id，用于日志
api = await self._get_k8s_api()
job = k8s_objects.Job(manifest, api=api)
await job.async_create()
self._job_creation_timestamps.append(time.monotonic())
```

### 当前先看正常提交的四项交接

| 语句 | 本函数在交接什么 |
| --- | --- |
| `manifest = build_job_spec(rollout, self._config)` | 用任务与控制器配置取得 Job manifest；它是一份描述资源的字典 |
| `api = await self._get_k8s_api()` | 取得此前已读过的 Kubernetes 客户端 |
| `job = k8s_objects.Job(manifest, api=api)` | 在 Python 中用配置和客户端构造 Job 对象 |
| `await job.async_create()` | 通过 Kubernetes API 发出创建请求，等待该操作返回 |

最后一项在核对版本的 kr8s 中会发送 `POST`，并把响应数据保存回对象。它与“等待任务执行完成”分属不同阶段。

**本轮可以先停在职责层**：`rollout` 与控制器配置生成 manifest，再据此提交 Kubernetes Job。能接回父函数的创建分支即可；限速、异常分类和底层请求实现在遇到相应问题时再回查。

### 需要深入时，一次进入一个函数

| 打开哪里 | 读完回到哪里 |
| --- | --- |
| [build_job_spec（源码）](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43) | 带回 `manifest`，继续取得客户端和构造 Job 对象；当前先看其输入输出，未独立建卡 |
| [_get_k8s_api（已有卡）](K8sReconciler._get_k8s_api.md) | 带回 Kubernetes 客户端 `api`，交给 Job 对象 |
| [Job.async_create 的库实现](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L365) | 创建操作返回后，继续登记时间；本轮只核对提交职责，不展开库内 HTTP 实现 |

### 返回父函数

| 返回入口 | 接下来执行什么 |
| --- | --- |
| [_reconcile_once 的创建调用](K8sReconciler._reconcile_once.md#call-create-job) | 181 行等待结束，随后 `continue`，进入下一条 rollout |

<details>
<summary>限速和失败路径：先保留边界</summary>

- 创建次数达到当前控制器的分钟上限时直接返回，稍后再由协调循环处理；它限制创建速率，不是正在运行的 Job 总数。
- 模板构造或资源配置被判断为无效时，通过 `_fail_invalid_job_spec` 请求写回任务失败。
- 其他创建请求错误会记录日志，等待后续协调再次尝试。
- 这些分支和正常路径均可能以 `None` 返回，父函数不凭本函数返回值断言 Job 已运行。

</details>

## 我的直接表述（原话）

本轮范围选择：

> 所以我觉得我需要看一下这里的这个create job?
> 然后我们再来看一下这里的patch status吧?

完整的父流程复述保存于 [父卡](K8sReconciler._reconcile_once.md#creation-reading-request)。

<a id="creation-purpose-understood"></a>

本轮用途复述：

> 我的简单理解是
> 这里通过create job的方式来创建这里的任务
> 通过manifiest来创建这个job
> 是我的理解
> 别的部分我觉得应该不需要特别深究对吗?

助手核对：通过 manifest 提交 Kubernetes Job 的职责理解成立；Gateway 中的 rollout 是传入时已经存在的任务记录。当前以能说明用途和交接为停止点，不把该表述扩展成已掌握限速、异常或全部请求实现。

## 尚不清楚

- manifest 的具体结构和模板如何使用 `rollout.input`，尚未独立展开。
- 创建 Job 的用途已有初步表述；Python Job 对象与提交请求的具体区别仍未单独复述。
- 限速、失败判定、重试以及创建后的状态回写，后续按实际问题阅读。

<details>
<summary>来源与验证边界</summary>

- Agent Lightning 固定提交：`0029dbb35c467799d35fee81d15d80264b0d1bd3`；本函数从 242 行开始，manifest 构造在 259 行，创建请求在 270 行。
- kr8s 版本：项目锁定 `0.20.15`，`APIObject.async_create` 从 `_objects.py:365` 开始。
- [本轮用户选择与阅读记录](../../../../../../step-000-k8s-controller-entry/04-flow.md#create-job-reading-start)。
- [本轮用途理解与阅读深度](../../../../../../step-000-k8s-controller-entry/04-flow.md#create-job-purpose-and-depth)。
- 本卡依据静态源码，示例条件为教学假设，没有部署 Job 或运行 Agent。

</details>
