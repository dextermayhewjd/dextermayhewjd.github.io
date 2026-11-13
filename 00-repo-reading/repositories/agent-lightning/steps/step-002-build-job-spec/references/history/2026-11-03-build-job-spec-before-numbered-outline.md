# build_job_spec

> **调用链面包屑**：[Step 002 范围](../../01-scope.md#caller-breadcrumb) · [短期函数索引](../../02-short-term-memory/overview.md) → [_create_job 的 manifest 调用](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md#call-build-job-spec) → **build_job_spec** → 返回 Job 字典，由调用方的 manifest 接住。

- 源码：[k8s_reconciler.py:43](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43)；这是模块级函数，没有 `self` 参数。
- 首次接触：Step 000 中先定位其接口；2026-11-03 在 Step 002 明确独立阅读并建卡。
- 最近认识更新：2026-11-03，用户已将开头理解为检查 Job 模板，进一步猜测 env 与容器配置、LLM 地址和镜像的关系；两处 env 的区别及 Gateway 地址含义由助手校准，尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_create_job` 已决定为 r1 创建 Job，手上有任务和共享模板，现在需要得到这一次执行可以提交的具体配置。
2. **具体内容**：先把模板和任务输入变成 Job 字典，再补任务身份与运行约束，最后给各容器补上访问 Gateway 的配置。
3. **建议构建的心智模型**：

   > **把一份共享的 Job 模板，变成 r1 这一次任务专用的 Job 配置。** 当前函数负责准备配置，调用方 `_create_job` 负责把它提交给 Kubernetes。

4. **调用代码**（`_create_job:259`）：

   ```python
   manifest = build_job_spec(rollout, self._config)
   ```

## 本场景的输入与输出

**整张卡解释一个问题：共享模板已经在手上，还需要做什么，才能用它创建这一次任务的 Job？** 以下始终使用同一条 r1 任务；输入为教学构造，结果只展示相关字段。

输入中的任务字段节选：

```jsonc
{
  "rollout_id": "r1",                    // 这一次任务的编号
  "input": {
    "image_name": "example/swe-task",    // 交给模板填写镜像引用
    "problem_statement": "修复示例任务"  // 交给模板填写任务内容
  },
  "is_train": true,
  "config": {"timeout_seconds": 3600}
}
```

同一个 rollout 的 `config.k8s.job_template` 保存 [SWE-smith 模板的完整文本](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/job-template-openai.yaml)。控制器采用[默认配置](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/config/controller.yaml)：namespace 为 default、TTL 为 1200、Gateway URL 为 `http://localhost:8080`、agent_url 未单设、key 为空。

**输出是一个完整 Job 字典，下面用 YAML 显示其中几项字段。** 未展示的标签、运行约束和 Gateway 环境变量仍属于最终配置，在后两段分别解释。

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: agl-rollout-r1              # 这份配置属于 r1
  namespace: default
spec:
  template:
    spec:
      containers:
        - name: agent
          image: example/swe-task:openai
          env:
            - name: AGL_TASK_INPUT
              value: 修复示例任务
```

返回这个字典后，调用方才取得 `manifest` 并提交 Job。上面是最终配置的节选，不是已经运行的容器；完整函数尚未端到端执行。

<a id="function-skeleton"></a>

### 先把三个处理阶段连起来

三个阶段都在 **同一次 `build_job_spec` 调用**里。下面是教学裁剪，`...` 表示省略的真实语句；完整展开在对应段内，不引入新的包装函数。

```python
def build_job_spec(rollout, controller_config):
    # 模板 + 本次任务 -> Job 字典
    template = rollout.config.k8s.job_template if rollout.config.k8s else None
    env = Environment()
    ...  # 配置模板过滤器与必要检查
    rendered = env.from_string(template).render(...)
    docs = [doc for doc in yaml.safe_load_all(rendered) if doc is not None]
    job = docs[0]

    # Job 字典 -> 带任务身份和运行约束的 Job
    metadata = job.setdefault(...)
    spec = job.setdefault(...)
    ...
    pod_spec = spec.setdefault(...).setdefault(...)

    # 给容器补连接信息 -> 交回可提交配置
    ...  # 准备 Gateway 地址
    for container in pod_spec.get(...):
        env = container.setdefault(...)
        ...  # 添加或覆盖三个 AGL 环境变量
    return job
```

**当前先读通下面的“模板怎样成为 Job 字典”。** 后两段先看其问题和交接，已有详细讨论放在各自展开区，随卡点回看。scope 中的逐行入口继续见[局部导航](../../01-scope.md#reading-navigation)。

<a id="template-input"></a>
<a id="jinja-env"></a>

### 模板怎样成为这次任务的 Job 字典（45–61 行）

**这一段要解释：模板中的空位怎样填上 r1 的数据，文字又怎样变成可继续补字段的配置？**

入口已有 `rollout`。代码先取模板，再渲染，最后解析；下面为连续源码，仅添加两条旁注。

```python
template = rollout.config.k8s.job_template if rollout.config.k8s else None
if not template:
    raise ValueError("invalid rollout config: missing config.k8s.job_template")

env = Environment()  # Jinja2 模板处理对象
env.filters["yaml_escape"] = lambda value: json.dumps(str(value), ensure_ascii=True)
rendered = env.from_string(template).render(
    job_name=build_job_name(rollout.rollout_id),
    input=rollout.input,
)
docs = [doc for doc in yaml.safe_load_all(rendered) if doc is not None]
if len(docs) != 1:
    raise ValueError("invalid rollout config: config.k8s.job_template must render exactly one YAML document")

job = docs[0]  # 这里开始拿到 Python 中的配置数据
if not isinstance(job, dict) or job.get("kind") != "Job":
    raise ValueError("invalid rollout config: config.k8s.job_template must render a Kubernetes Job")
```

- **取出模板**：`template` 是 rollout 配置中已有的文本。空模板在这里报错。
- **填写本次任务**：`Environment` 从 Jinja2 导入，`env` 在这里是模板处理对象；`render` 接收生成的 job_name 与同一份 `rollout.input`，交出 `rendered` 文本。
- **得到配置数据**：`yaml.safe_load_all` 解析文本；确认只有一个文档、且它是 Job 字典后，`job` 才交给下一段补字段。

<a id="image-boundary"></a>

例如，真实模板中的这一行：

```yaml
image: {{ (input.image_name ~ ":openai") | yaml_escape }}
```

填入本例输入后成为：

```yaml
image: "example/swe-task:openai"
```

这就在解释本函数与镜像的关系：**填出这次要使用的镜像引用**。镜像构建、拉取和容器启动由其他环节完成。此处没有因为 `env` 这个变量名就开始设置容器环境变量。

| 需要回查的材料 | 读完返回哪里 |
| --- | --- |
| [真实模板](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/job-template-openai.yaml#L4) | 回到本段 `env.from_string(template).render(...)`，继续看输入填到哪里 |
| [Job 清单与 Pod 模板](../../../../../kubernetes/03-workloads/job-manifest-and-pod-template.md) | 回到模板的 `spec.template`，确认它描述 Pod |

<details>
<summary>已讨论的补充：转义、模板来源与镜像边界</summary>

`yaml_escape` 使用 `json.dumps(str(value), ensure_ascii=True)` 处理填入模板的字符串。这里先知道它服务于文本生成，转义细节按实际输入问题再看。

模板在上游[读取为文本](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/agl_rollout_manager.py#L283)，本函数不再按路径打开文件。两种“模板”也要分开：Jinja 文本模板用于生成整个 Job 清单，Job 内的 `spec.template` 是 Kubernetes 的 Pod 模板。

SWE-smith 模板另有 `imagePullPolicy: IfNotPresent`；[镜像、命令与 env 的通用说明](../../../../../kubernetes/04-runtime-environment/container-image-and-env.md)已保存在 k8s 目录。准备镜像的 [`pull_images.py`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/pull_images.py)仅定位，未作为当前子函数展开。

</details>

<a id="job-identity-and-policy"></a>

### 怎样让这份 Job 关联任务，并带上运行约束（63–77 行）

**这一段要解释：创建后的 Job 怎样被前面读过的查询和事件处理识别，又按什么约束执行？**

接住上一段的 `job`，补名称、namespace、关联标签和运行设置，取得内部的 `pod_spec`，再交给下一段。这里尤其连接到前两步读过的 `agentlightning/rollout-id`；其他运行参数尚未逐项阅读。

<details>
<summary>展开这一段的连续源码；先定位，后续按问题细读</summary>

```python
metadata = job.setdefault("metadata", {})
metadata["name"] = build_job_name(rollout.rollout_id)
metadata["namespace"] = controller_config.k8s_runner.namespace
labels = metadata.setdefault("labels", {})
labels["app.kubernetes.io/managed-by"] = "agentlightning"
labels["agentlightning/rollout-id"] = rollout.rollout_id
labels["agentlightning/attempt-id"] = DEFAULT_ATTEMPT_ID

spec = job.setdefault("spec", {})
spec["backoffLimit"] = 0
spec["ttlSecondsAfterFinished"] = controller_config.k8s_runner.ttl_after_finished
if rollout.config.timeout_seconds:
    spec["activeDeadlineSeconds"] = rollout.config.timeout_seconds
pod_spec = spec.setdefault("template", {}).setdefault("spec", {})
pod_spec["restartPolicy"] = "Never"
```

本例会写入 `name=agl-rollout-r1`、`namespace=default` 与任务编号标签。随后对 Job 的重试、清理、超时和 Pod 的重启策略设置参数。它们分别属于 Job 或 Pod 模板，不把这一整段当成容器环境变量操作。

</details>

<a id="agent-gateway-url"></a>
<a id="container-env"></a>

### Agent 启动后，怎样知道去哪里请求模型和上报事件（79–101 行）

**这一段要解释：给 Pod 模板中的容器补入哪些运行时连接信息，并怎样把最终配置交回调用方？**

接住上一段的 `pod_spec`，先构造 Gateway 地址，再对各个 `containers` 条目的 env 添加或覆盖三项。`env = container.setdefault("env", [])` 在这里得到的是**容器的环境变量列表**；它与第一段的 Jinja 对象复用了变量名，但服务于不同阶段。

这个列表的完整位置是 `job["spec"]["template"]["spec"]["containers"][i]["env"]`。

本例补入的三项为：

```yaml
env:
  - name: AGL_OPENAI_BASE_URL  # 模型请求先发往 Gateway 的代理入口
    value: http://localhost:8080/proxy/rollout/r1/attempt/0/mode/train/openai/v1
  - name: AGL_EVENT_URL       # 向 Gateway 上报执行事件
    value: http://localhost:8080/api/rollouts/r1/attempt/0/events
  - name: AGL_KEY
    value: ""
```

**地址的第一站是 Gateway。** 实际模型服务由 Gateway 选择；这几个字段配置的是 Agent 怎样连接服务，未改变镜像内容。模板已有的其他 env 保留，三个同名项被覆盖，并不是把 Controller 的全部环境变量搬进容器。

<details>
<summary>展开这一段源码，以及已讨论的地址选择与可达性</summary>

```python
mode = "train" if rollout.is_train else "val"
agent_base_url = str(
    controller_config.agl_server.get("agent_url", None) or controller_config.agl_server.url
).rstrip("/")
agl_openai_base_url = (
    f"{agent_base_url}/proxy/rollout/{rollout.rollout_id}/attempt/{DEFAULT_ATTEMPT_ID}/mode/{mode}/openai/v1"
)
for container in pod_spec.get("containers", []):
    env = container.setdefault("env", [])  # 这里的 env 是这个容器的变量列表
    for name, value in {
        "AGL_OPENAI_BASE_URL": agl_openai_base_url,
        "AGL_EVENT_URL": (
            f"{agent_base_url}/api/rollouts/{rollout.rollout_id}/attempt/{DEFAULT_ATTEMPT_ID}/events"
        ),
        "AGL_KEY": str(controller_config.agl_server.key or ""),
    }.items():
        existing = next((item for item in env if item.get("name") == name), None)
        if existing is None:
            env.append({"name": name, "value": value})
        else:
            existing.clear()
            existing.update({"name": name, "value": value})
return job
```

`agent_url` 优先，未提供时回退到 `agl_server.url`。本例采用默认地址，只验证其字符串构造；默认 Pod 网络中的 localhost 指向 Pod 自己，不等于 Controller 所在机器。实际部署时使用从 Agent 环境可达的 Gateway 地址，配置含义见[控制器文档](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/docs/30-controller-configuration.md#connect-to-the-api-gateway)。

Agent 读取 AGL_OPENAI_BASE_URL 创建客户端，Gateway 再按实际模型的 server.endpoint 转发。单凭 agent_base_url 不能判断模型部署在本地还是云端。此处只核对调用合同，没有展开代理内部。

</details>

<a id="return-to-create-job"></a>

### 三段合在一起，交回哪份结果

`return job` 交回的是已经填写任务、补齐身份和运行配置的 **同一份 Job 字典**。回到 `_create_job` 后，由 `manifest` 接住；调用方接着构造 kr8s Job 对象并执行 `await job.async_create()`。

[返回调用方的 manifest 位置](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md#call-build-job-spec)。本页展示的是三个阶段怎样完成一个配置构造任务；各段是否理解，继续按实际反馈记录。

## 我的直接表述（原话）

用户本轮选择：

> 那么当前应该看哪一个函数呢?
> 当前看一下这里的build job spec?

当时确认的是阅读入口。此前关于模板是否应该先于函数出现的定位纠正，见 [scope 的调用面包屑](../../01-scope.md#caller-breadcrumb)。

<a id="env-url-image-question"></a>

用户本轮的理解与问题：

> 好的 我的理解是这里的在做的内容是先检查模板
> 这里的模板应该是k8s job的模板对吗?
> (这一部分需要补充道k8s的只是当中吗?)
> 然后下面的内容是env?
> 这里怎么感觉像是一个python的文件包?
> 然后这里做的内容是根据这里的job
> 把这里的环境变量全部放到这里的这个pod里面?
> 是我的理解
> 同时配置一下这里agent base url应该是本地或者云端的llm的base url?
> 简单来说我感觉这里全部的内容都是和容器相关的?
>
> 这里有什么特别需要了解的或者这个function特别覆盖的到的关于镜像的方面吗?
> (例如llm的base url)?

“先检查 Job 模板”的职责理解与源码一致。两处 env 的不同对象、三项容器配置、Gateway 与实际模型端点，以及镜像引用与运行参数的分工是本轮助手校准，未写成用户已掌握。

<a id="layout-feedback"></a>

用户对详略与总分结构的反馈：

> 1.好的 那么请把这些补充进去吧
> 如果已经补充了就不用了
> 2.这里build job spec具体的内容我觉得目前是很难直接了解了
> 但是这里的build job spec里的内容是不是详略不是特别合适?
> 或者需要考虑一下总和分的排版?
> 先讲清楚要解释的是什么
> 或许可以考虑一下之前,类似的short term memory的skills? 看看有没有reference可以参考

本次是阅读材料的组织反馈，不表示已经掌握各阶段实现。助手按既有 reference 重排整体输入输出与连续阶段；原来的理解、疑问与来源继续保留。

## 尚不清楚

- 用户已有检查 Job 模板的初步理解；Jinja 文本模板、Job 内部 Pod 模板与返回字典的区别仍待反馈。
- Jinja Environment 对象与容器 env 列表复用同一个变量名，刚由助手解释，尚未确认理解。
- Agent 的 Gateway 地址、代理路径与实际模型端点的区别，以及容器的地址可达性，当前已定位合同，未开展部署验证。
- 镜像引用、实际镜像构建和运行时配置的分工，尚待反馈；脚本与挂载、YAML 解析、运行约束仍按后续问题展开。

<details>
<summary>来源与验证边界</summary>

- 本轮排版依据：[BaseAdapter._run_turn](../../../../../../../.agents/skills/repo-reading-short-term-memory/references/base-adapter-run-turn.md) 的整体场景、分阶段交接，与[面包屑 reference](../../../../../../../.agents/skills/repo-reading-short-term-memory/references/breadcrumb-navigation-and-shared-infra.md) 的进入和返回。阶段数量按当前源码职责划分，没有套用样例的业务内容。
- [重排前的完整卡片](2026-11-03-build-job-spec-before-total-parts.md) · [本次重排与核对记录](../../04-flow.md#total-and-parts-layout)。


- [哪些知识归入 k8s 基础目录](../../../../references/kubernetes-integration.md#build-job-spec-knowledge-boundary) · [本次归类讨论](../../04-flow.md#k8s-note-boundary)。
- [本轮模板、env、URL 与镜像的讨论](../../04-flow.md#template-env-url-image)。
- Jinja2 导入与两处 env 见同文件 25、49–54、86–100 行；Agent 在 [`smith_agent.py:862–875`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/agents/smith_agent.py#L862) 读取 AGL_OPENAI_BASE_URL 并创建客户端；Gateway 在 [`server/routes/proxy.py`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/server/routes/proxy.py) 选择服务器并转发，最终使用 server.endpoint。
- 固定源码 `0029dbb35c467799d35fee81d15d80264b0d1bd3`；三个连续阶段为 45–61、63–77、79–101 行，完整函数 43–101 行，调用方 259 行。
- [Step 002 的首次独立阅读](../../04-flow.md#build-job-spec-start)。
- 模板来自 `examples/swe_smith/job-template-openai.yaml`，控制器配置来自 `agentlightning/config/controller.yaml`，任务字段为教学构造。
- 已用原始 49–54 行和 79–100 行片段作本地核对：真实模板生成预期镜像引用与任务文本，URL 正确拼接，三个 AGL 变量按名称补入各容器并保留其他项。使用教学输入与内存配置，没有运行 YAML 解析、完整 build_job_spec、创建 Job 或访问 Gateway。

</details>
