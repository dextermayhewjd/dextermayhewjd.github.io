# build_job_spec

> **调用链面包屑**：[Step 002 范围](../../01-scope.md#caller-breadcrumb) · [短期函数索引](../../02-short-term-memory/overview.md) → [_create_job 的 manifest 调用](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md#call-build-job-spec) → **build_job_spec** → 返回 Job 字典，由调用方的 manifest 接住。

- 源码：[k8s_reconciler.py:43](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43)；这是模块级函数，没有 `self` 参数。
- 首次接触：Step 000 中先定位其接口；2026-11-03 在 Step 002 明确独立阅读并建卡。
- 最近认识更新：2026-11-03，用户已将开头理解为检查 Job 模板，进一步猜测 env 与容器配置、LLM 地址和镜像的关系；两处 env 的区别及 Gateway 地址含义由助手校准，尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_create_job` 准备给一条排队任务创建 Job，先把这条 rollout 与控制器配置交进来，取得要提交的配置。
2. **具体内容**：取得模板文本，用任务输入渲染并解析为 Job 字典，补充身份标记、运行约束与容器访问 Gateway 的环境变量，返回字典。
3. **建议构建的心智模型**：

   > **拿到任务和模板，准备好这次创建 Job 所需的配置，再交回 `_create_job`。** 当前函数先处理配置数据，提交 Kubernetes 的动作发生在调用方。

4. **调用代码**（`_create_job:259`）：

   ```python
   manifest = build_job_spec(rollout, self._config)
   ```

## 本场景的输入与输出

沿用任务 r1：Gateway 中这条任务处于排队状态，调用方没有找到对应 Job，准备创建。`rollout` 带着任务输入和模板文本，`controller_config` 带着控制器设置；函数返回的 Job 字典由 `manifest` 接住。本轮从模板输入继续，按用户问题对照两处 env、Gateway 地址与镜像字段；中间各项运行约束仍保留位置。

<details>
<summary>同一教学场景的整体输入与输出节选：用于后续逐段对照</summary>

任务字段为教学构造。以下是 rollout 的部分字段，不是完整模型构造参数；`config.k8s.job_template` 使用仓库 [SWE-smith 模板](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/job-template-openai.yaml)的完整文本，单独链接以避免把整份 YAML 塞入 JSON。

```jsonc
{
  "rollout_id": "r1",                    // 用于生成 Job 名和关联标记
  "is_train": true,
  "input": {
    "image_name": "example/swe-task",    // 本例给模板使用的教学值
    "problem_statement": "修复示例任务"
  },
  "config": {
    "timeout_seconds": 3600
  }
}
```

控制器配置沿用仓库 [controller.yaml](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/config/controller.yaml)：namespace 为 default，完成后保留 1200 秒，Gateway 地址为 `http://localhost:8080`，agent_url 未单设，key 为空字符串。

正常返回的配置字典包含下列身份字段。这是依照源码静态推导的输出节选，其他 spec、容器和环境变量字段仍会保留或补充，后续走到对应语句再展开：

```json
{
  "apiVersion": "batch/v1",
  "kind": "Job",
  "metadata": {
    "name": "agl-rollout-r1",
    "namespace": "default",
    "labels": {
      "app.kubernetes.io/managed-by": "agentlightning",
      "agentlightning/rollout-id": "r1",
      "agentlightning/attempt-id": "0"
    }
  }
}
```

身份字段的输出节选仍按源码推导；本轮另对 Jinja 渲染及 URL/env 处理片段作了本地验证，尚未执行包含 YAML 解析的完整函数或创建 Job。

</details>

<a id="function-skeleton"></a>

### 整个函数的骨架：各处问题仍接回同一个函数

教学裁剪保留处理顺序；校验与详细字段赋值暂用 `...` 折叠，不能直接运行。

```python
def build_job_spec(rollout, controller_config):
    template = rollout.config.k8s.job_template if rollout.config.k8s else None
    ...  # 检查模板存在

    env = Environment()
    env.filters["yaml_escape"] = ...
    rendered = env.from_string(template).render(...)
    docs = [doc for doc in yaml.safe_load_all(rendered) if doc is not None]
    ...  # 检查只得到一份 Job 配置
    job = docs[0]

    metadata = job.setdefault(...)
    ...  # 补名称、namespace 与关联标签
    spec = job.setdefault(...)
    ...  # 补 Job 的运行约束
    pod_spec = spec.setdefault(...).setdefault(...)
    ...  # 补 Pod 的重启策略与 Gateway 地址
    for container in pod_spec.get(...):
        env = container.setdefault(...)
        ...  # 按名称添加或覆盖容器环境变量

    return job
```

后续代码仍属于当前函数，只有需要理解某个实际调用时才从这里下钻。各段位置继续以 [scope 的局部导航](../../01-scope.md#reading-navigation)为准。

<a id="template-input"></a>

### 当前段：先从 rollout 取得模板（45–47 行）

```python
template = rollout.config.k8s.job_template if rollout.config.k8s else None
if not template:
    raise ValueError("invalid rollout config: missing config.k8s.job_template")
```

- 若这条 rollout 有 `config.k8s`，就取其中的 `job_template`，交给变量 `template`；没有该配置时得到 `None`。
- 这里取得的是**已经放在 rollout 配置中的模板文本**。不是这里才拿文件路径去打开文件。
- 如果模板缺少或为空，抛出 `ValueError`；没有继续到创建请求。调用方已有模板错误的处理分支。

本例拿到的文本开头，是下面这个真实模板的节选：

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ job_name }}
```

这时它仍是文字，`{{ job_name }}` 也仍在文本里。当前这几行只是**取得模板并检查是否存在**，后面的渲染才会使用具体的任务数据。

这里的文件是用于生成**完整 Job 清单**的 Jinja 文本模板；生成后的 Job 内部还有 Kubernetes 的 `spec.template`，它描述 Pod。两种“模板”的位置见 [Job 清单与 Pod 模板](../../../../../kubernetes/03-workloads/job-manifest-and-pod-template.md)。

| 需要回查时打开 | 读完回到哪里 |
| --- | --- |
| [本例完整模板](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/job-template-openai.yaml#L4) | 带着 `template` 的具体内容，回到 build_job_spec 第 49 行 |
| [模板文本的上游读取位置](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/agl_rollout_manager.py#L283) | 只核对文本如何进入配置，然后回到第 45 行；不沿此处展开 Trainer |

<a id="jinja-env"></a>

### 前面的 env：Jinja2 模板处理对象（49–54 行）

```python
from jinja2 import Environment  # 文件顶部的导入：Environment 是 Jinja2 提供的类

env = Environment()            # 创建模板处理对象
env.filters["yaml_escape"] = lambda value: json.dumps(str(value), ensure_ascii=True)
rendered = env.from_string(template).render(
    job_name=build_job_name(rollout.rollout_id),
    input=rollout.input,
)
```

这里的 `env` 用来配置过滤器、加载模板和执行渲染。`rendered` 是填入任务数据后的文本；还没有在这几行里配置容器环境变量。后面 55 行的 YAML 解析再把文本变成 Python 数据。

<a id="agent-gateway-url"></a>

### 后面的 agent_base_url：Agent 使用的 Gateway 地址（79–85 行）

先保留中间标签、运行约束的位置，本轮按问题接到地址构造：

```python
mode = "train" if rollout.is_train else "val"
agent_base_url = str(
    controller_config.agl_server.get("agent_url", None) or controller_config.agl_server.url
).rstrip("/")
agl_openai_base_url = (
    f"{agent_base_url}/proxy/rollout/{rollout.rollout_id}/attempt/{DEFAULT_ATTEMPT_ID}/mode/{mode}/openai/v1"
)
```

`agent_url` 优先，未提供时退回 `agl_server.url`。它们都指向 **Agent Lightning Gateway**：前者供 Agent 所在环境访问，后者也是 Controller 使用的 Gateway 地址。本例默认配置算出 `agent_base_url="http://localhost:8080"`，这只是地址字符串的计算，不等于已经验证容器能连接。

对 r1 的训练场景，拼出的代理入口是：

```text
http://localhost:8080/proxy/rollout/r1/attempt/0/mode/train/openai/v1
```

Agent 用它发送模型请求；Gateway 再选择实际模型服务并转发。因此不能从 `agent_base_url` 判断 LLM 是本地还是云端，也不能将它直接当作模型服务器的地址。当前关系是：**Agent 进程通过 HTTP 访问 Gateway 代理入口，Gateway 再访问模型服务。**

配置时要从调用者的位置判断可达性。默认 Pod 网络中，Pod 内的 localhost 不等于 Controller 所在机器；实际部署可能需要设置 `agl_server.agent_url`。两个地址的项目定义见[控制器文档](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/docs/30-controller-configuration.md#connect-to-the-api-gateway)。

<a id="container-env"></a>

### 后面的 env：每个容器的环境变量列表（86–100 行）

```python
for container in pod_spec.get("containers", []):
    env = container.setdefault("env", [])  # 此处重新赋值；env 现在是一个列表
```

变量名被复用了：这个 `env` 与前面的 Jinja2 对象不是一回事。它对应 `job["spec"]["template"]["spec"]["containers"][i]["env"]`，也就是 Pod 模板里第 i 个普通容器的环境变量列表。

本函数只为每个容器添加或覆盖以下三项；模板原有的其他环境变量继续保留，没有把 Controller 进程的所有环境变量复制进去。本例中的结果节选：

```yaml
env:
  - name: AGL_OPENAI_BASE_URL  # Agent 发送模型请求的 Gateway 代理入口
    value: http://localhost:8080/proxy/rollout/r1/attempt/0/mode/train/openai/v1
  - name: AGL_EVENT_URL       # 向 Gateway 上报执行事件
    value: http://localhost:8080/api/rollouts/r1/attempt/0/events
  - name: AGL_KEY             # 本例默认配置为空字符串
    value: ""
```

同名项已存在时清空并写入新的 name/value，不存在则追加。这里修改的是**待提交的 Job 配置**；之后 Kubernetes 创建 Pod/容器时才应用它。通用的字段层次与作用见[容器镜像、命令与 env](../../../../../kubernetes/04-runtime-environment/container-image-and-env.md)。

<a id="image-boundary"></a>

### 当前函数与镜像有关的部分在哪里

本例的镜像选择来自输入模板这一行：

```yaml
image: {{ (input.image_name ~ ":openai") | yaml_escape }}
```

教学输入 `input.image_name="example/swe-task"` 会在渲染后得到镜像引用 `example/swe-task:openai`。模板还指定 `imagePullPolicy: IfNotPresent`。镜像用于运行 Agent 程序和依赖；上面的 Gateway URL 则是 Agent 运行时拿到的访问配置。

本函数把镜像引用放入最终 Job 数据，并补充运行配置；它没有构建或拉取镜像。该示例准备镜像的代码在 [`pull_images.py`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/pull_images.py)，当前只定位来源，不另开函数卡。

整个函数围绕 **Job 工作负载配置**：既有 Job 层的名称、标签和生命周期设置，也有 Pod/容器的镜像、命令与 env。不能把每一行都理解成修改容器本身。

<a id="return-to-create-job"></a>

### 最后返回哪里

整个函数正常结束时，`return job` 返回配置字典，回到调用方完成 `manifest = build_job_spec(...)` 的赋值。之后由 `_create_job` 取得客户端、构造 kr8s Job 对象，并等待 `job.async_create()`。

回到[调用方的 manifest 位置](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md#call-build-job-spec)。当前还没有逐段读到返回处，这里先保留完整导航。

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

## 尚不清楚

- 用户已有检查 Job 模板的初步理解；Jinja 文本模板、Job 内部 Pod 模板与返回字典的区别仍待反馈。
- Jinja Environment 对象与容器 env 列表复用同一个变量名，刚由助手解释，尚未确认理解。
- Agent 的 Gateway 地址、代理路径与实际模型端点的区别，以及容器的地址可达性，当前已定位合同，未开展部署验证。
- 镜像引用、实际镜像构建和运行时配置的分工，尚待反馈；脚本与挂载、YAML 解析、运行约束仍按后续问题展开。

<details>
<summary>来源与验证边界</summary>

- [哪些知识归入 k8s 基础目录](../../../../references/kubernetes-integration.md#build-job-spec-knowledge-boundary) · [本次归类讨论](../../04-flow.md#k8s-note-boundary)。
- [本轮模板、env、URL 与镜像的讨论](../../04-flow.md#template-env-url-image)。
- Jinja2 导入与两处 env 见同文件 25、49–54、86–100 行；Agent 在 [`smith_agent.py:862–875`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/agents/smith_agent.py#L862) 读取 AGL_OPENAI_BASE_URL 并创建客户端；Gateway 在 [`server/routes/proxy.py`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/server/routes/proxy.py) 选择服务器并转发，最终使用 server.endpoint。
- 固定源码 `0029dbb35c467799d35fee81d15d80264b0d1bd3`；当前片段 45–47 行，完整函数 43–101 行，调用方 259 行。
- [Step 002 的首次独立阅读](../../04-flow.md#build-job-spec-start)。
- 模板来自 `examples/swe_smith/job-template-openai.yaml`，控制器配置来自 `agentlightning/config/controller.yaml`，任务字段为教学构造。
- 已用原始 49–54 行和 79–100 行片段作本地核对：真实模板生成预期镜像引用与任务文本，URL 正确拼接，三个 AGL 变量按名称补入各容器并保留其他项。使用教学输入与内存配置，没有运行 YAML 解析、完整 build_job_spec、创建 Job 或访问 Gateway。

</details>
