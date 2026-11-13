# SandboxFleet.load_tasks

> 继承快照：来自 [Step 000 原记录](../../../../../../../step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.load_tasks.md)。以下“当前／本轮”保留原步骤语境；本次继承不改变认识时间，也不表示重新阅读或掌握。

[返回 main](../../examples/run_swebench_fleet.py/main.md) · [SandboxFleet 类卡](../../../../../classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md) · [本步 scope](../../../../../../../step-000-warmpool-reconcile/01-scope.md#current-excerpt)

- 源码定位：[fleet.py:429–453](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L429)。
- 首次接触：Step 000，2026-11-04，在 main 的任务加载调用中接触；本次按用户要求建立独立方法卡。
- 最近认识更新：2026-11-04，用户明确概括为通过 source 取得 Task 列表，并追问其与 Fleet 初始化、config 的区别；具体字段与返回语义不据此标为全部掌握。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：main 刚创建 fleet，接着提供本次要执行的任务来源；这一步发生在 fleet.run 和环境准备之前。
2. **具体内容**：把传入来源转换为 Task 列表，保存到 self.tasks，并返回同一列表。方法也支持可选的镜像改写，本次调用没有启用。
3. **建议构建的心智模型**：

   > load_tasks 把“从哪里取得任务”落实成“Fleet 现在持有哪些任务数据”。它登记任务，供后续规划与执行使用；这里还没有创建 Pod 或执行题目。

4. **调用代码**：main:85–87 的真实嵌套调用，调整换行便于阅读。

   ```python
   fleet.load_tasks(SweBenchSource(
       dataset=_env("DATASET_NAME", "R2E-Gym/SWE-Bench-Verified"),
       split=_env("DATASET_SPLIT", "test"),
       limit=tasks_limit,
       offset=offset))
   ```

## 本场景的输入与输出

### 1. 输入从哪里来

| 输入 | 当前场景 |
| --- | --- |
| self | main 上一行创建的 fleet；刚构造时 tasks 为空列表 |
| source | SweBenchSource(...) 创建的数据来源对象，已保存 dataset、split、limit、offset 等读取条件 |
| image_rewrite | 未传，默认 None，本次不改写镜像名 |
| image_field、id_field | 未传，均为 None；当前来源的字段转换由 SweBenchSource.load 负责 |

Python 先求值 SweBenchSource(...)，再调用 fleet.load_tasks。前者的构造只保存读取条件；读取数据发生在后者委托来源执行 load 时。main 中没有额外的 source 变量，这个名字是 load_tasks 的形参。

### 2. 本次调用的核心代码

以下是原方法的教学裁剪：保留真实语句，省略日志及本次未启用的 image_rewrite 分支。

```python
tasks = to_tasks(source, image_field=image_field, id_field=id_field)
self.tasks = tasks
return self.tasks
```

1. **转换来源，取得列表（436）**：to_tasks 接收来源对象；当前 SweBenchSource 满足 TaskSource 接口，因此走 source.load() 分支，取得 Task 列表。来源内部的数据集切片与字段映射暂按接口理解。
2. **写入 Fleet（450）**：self.tasks = tasks 将列表保存到同一个 Fleet 对象；这是替换当前任务列表，不是追加。
3. **交回列表（453）**：返回的就是 self.tasks。main 没有单独接收这个返回值，后续通过 fleet.tasks 使用已经登记的任务。

### 3. 完成后发生什么变化

1. 调用前，当前 fleet.tasks 为 []。
2. 正常返回后，fleet.tasks 保存来源提供的 Task 列表；如果来源没有任务，列表仍可能为空。
3. 每条 Task 包含 id、image、metadata，分别表示任务标识、所需环境镜像和附加信息。这些是数据，不是 Pod 或任务执行结果。
4. 回到 main，后续 fleet.run 选择策略；naive 路径的 setup 使用已加载任务准备环境，executor 随后接收 fleet.tasks。

<details>
<summary>未展开的可选分支</summary>

传入 image_rewrite 时，方法逐条处理任务的镜像名。镜像发生变化时复制 Task，并在 metadata 中记录 original_image；随后保存改写后的列表。当前 main 没有传这个参数，因此不进入该分支。

to_tasks 还支持其他来源形态，本轮只看 SweBenchSource 的 TaskSource 路径，不展开全部输入兼容逻辑。

</details>

## 我的直接表述（原话）

用户要求保存当前任务加载部分：

> h好的那么现在把这个load tasks的部分放到这里的short term memory中吧

这是建立方法记录时的请求；当时尚无用户对转换、赋值与返回关系的独立复述。

随后用户给出当前理解：

> 好的 我大概理解了
> 也就是这里会需要通过获得的这个tasks
> 从souce中获取对应的images
> 然后返还给self
> 让fleet本身记录有这些image镜像
> 同时把这里的tasks返还给外部?
> 是我对于这个function的理解

用户已经注意到 Fleet 保留数据、函数同时向外返回的两处效果。助手校准：从 source 取得的是包含 id、image、metadata 的 Task 列表；self.tasks = tasks 是写入对象属性，return self.tasks 才是向调用方返回同一列表。image 记录镜像名称，不表示此处已经拉取镜像。对上述区别尚未收到用户确认。

用户随后明确概括来源到 Task 列表的关系，并提出新的对比问题：

> 好的 我差不多理解了
> 那么我们继续吧
> 这里更多的是这里在通过source取得task列表
> 那么一开始的fleet init更多的像什么呢/
> 我需要知道这两个的区别
> load tasks是和任务相关
> 那么config呢?

config 与 tasks 的对象层分工见 [SandboxFleet 类卡](../../../../../classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md#config-vs-tasks)。

在比较 config 与 tasks 后，用户反馈：

> 好的 我了解了
> 那么我们继续吧
> 下一个function我们要看什么呢?

该反馈针对上一轮“运行配置与具体任务数据”的区分；不扩展为全部字段转换、返回对象身份或初始化内部机制已掌握。

## 尚不清楚

1. 用户已明确“通过 source 取得 Task 列表”；用户在配置与任务的对比说明后表示了解。属性写入、返回值和 image 字段的具体语义不据此全部标为掌握。
2. SweBenchSource.load 内的数据集切片、字段映射与可选整行保存，当前未逐项展开。
3. 镜像改写和其他输入形态只保留用途，不作为本轮必读。

<details>
<summary>来源、验证与原始讨论</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 当前调用：examples/agent-sandbox-rl/examples/run_swebench_fleet.py:85–87。
- 方法主体：agent_sandbox_rl/fleet.py:429–453；来源分派：sources.py:308–319；Task 字段：sources.py:159–170。
- 数据来源：adapters/swebench.py:53–94；已有 [SweBenchSource.load 记录](../../../../../../../step-000-warmpool-reconcile/references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/SweBenchSource.load.md)仅按需回查。
- [本次建卡过程](../../../../../../../step-000-warmpool-reconcile/04-flow.md#load-tasks-method-card)。
- 本次按静态源码核对，没有下载数据集、创建客户端、部署 Pod 或执行真实任务。

</details>
