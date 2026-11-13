> Step 011 补充继承（2026-11-11）：来自 [Step 010 收束时的完整记录](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.__init__.md)。原话、日期、来源与未知保留；继承不表示本步新增理解。

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.__init__.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.__init__.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

# HarborDataSource.__init__

- 源码：[dressage/integrations/harbor/data_source.py:123–255](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L123)。
- 首次独立建卡：Step 010，2026-11-10；来自父卡“准备运行条件”中的前置回查。
- 最近认识更新：尚无对初始化机制的完整复述；本次整理已讨论的数据来源，不代表整段初始化已掌握。

[从 _run_harbor_rollout 第 1 段回查](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md#prepare-runtime) → **数据源初始化** → [回到读取 integration_config 的位置](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md#prepare-runtime)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：外层创建 HarborDataSource，供后续多次 rollout 调用使用；当前是在阅读已存在的 data_source 时回查其来源。
2. **具体内容**：加载接入与 Job 配置，组织训练及可选评估规格，建立 ID 查询表；还保存采样参数、运行标识、游标和恢复时使用的摘要。本轮只重点看配置、spec 与查询表。
3. **建议构建的心智模型**：

   > 先把任务与 Agent 配置整理成可取样、可按 ID 查回的规格，再让后面的 rollout 从这个数据源取得模板和执行资料。

4. **调用位置**：[训练脚本](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh#L66)通过配置指定数据源类型：

   ```text
   --data-source-path dressage.integrations.harbor.data_source.HarborDataSource
   ```

   数据源构造早于当前 `_run_harbor_rollout`；后者只接收并使用对象，不在函数体内重新调用该构造方法。

## 本场景的输入与输出

**输入**：外层传入 `args`，构造方法从参数或环境变量取得配置来源。当前沿训练数据源、已有有效配置的正常路径阅读，配置来源优先级与每项验证暂不展开。

**先分清名称**：`HarborDataSource` 是类；`data_source` 是指向实例的变量；`__init__` 是创建实例时执行的初始化方法。它把配置、规格与游标等写入 `self`。

```python
# 构造语法示意，不是 _run_harbor_rollout 中新增的一行。
data_source = HarborDataSource(args)
```

**结果**：上面的类调用得到初始化后的对象，赋给 `data_source`；`__init__` 方法本身返回 `None`。这里不返回 Sample 组，也不创建 Harbor Job 来执行任务。

下面是对象状态示意，只列当前需要的字段，不是真实运行打印。假设配置解析后得到 A、B 两份训练规格，且没有单独配置评估源：

```text
data_source（HarborDataSource 实例）
  ├─ integration_config：已加载的接入配置
  ├─ job_config：已加载的 Harbor 执行配置
  ├─ _specs：(A规格, B规格)
  ├─ _spec_by_id：{A的spec_id: A规格, B的spec_id: B规格}
  ├─ sample_group_index：0
  └─ sample_index：0
```

先看清这个结果，再回到下面第 2 项 `_build_registry`，只追问“A/B 这些规格怎样从任务与 Agent 配置产生，指纹在哪里写入”。无需先展开全部加载器。

<a id="data-source-precondition"></a>

### 本轮先看数据源已准备的配置与规格

`data_source` 是已创建的 `HarborDataSource` 对象。下面是它在进入 rollout **之前**完成的初始化节选，不是 `_run_harbor_rollout` 在这里执行的代码；其中的 `self` 就是后来传入的数据源对象。

```python
# 1. 保存两份用途不同的配置。
self.integration_config = _load_integration_config(integration_source)
self.job_config = _load_job_config(job_source, job_config_type)

# 2. 从任务和 Agent 配置建立规格记录。
tasks = _resolve_tasks(self.job_config)
self._specs = _build_registry(
    tasks=tasks,
    agents=getattr(self.job_config, "agents", None),
    integration_fingerprint=self.integration_fingerprint,
    scope="train",
)

# 3. 保存按 spec_id 查询规格的表；评估规格的准备在此省略。
self._spec_by_id = {
    spec.spec_id: spec for spec in (*self._specs, *self._eval_specs)
}
```

这里只回查三个问题，不必通读整个类：

| 看哪里 | 当前要弄清什么 | 读到哪里停 |
| --- | --- | --- |
| [HarborDataSource.__init__:123](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L123)，重点 142、182–189 行 | `integration_config` 管接入条件，`job_config` 描述 Harbor 执行安排；初始化由后者取得任务和 Agent 配置 | 看清两份配置和 `_build_registry` 调用，不展开配置加载器 |
| [_build_registry:665](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L665)，重点 684–718 行 | 为任务与 Agent 组合建立 `HarborPromptSpec`；按 Agent 配置计算 `runtime_fp`，写入 `runtime_fingerprint` | 看清 spec 的 `task_config`、`agent_config`、`spec_id` 和运行指纹；不展开所有摘要、脱敏算法 |
| [__init__:214](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L214) 与 [resolve_spec:269](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L269) | `_spec_by_id` 保存对应表，`resolve_spec(spec_id)` 查回已有 spec | 看清“保存 → 按 ID 取回”，返回本段读取配置的位置 |

这些准备接到已经读过的流程：`get_samples` 选择已有 spec，`_sample_group` 把 spec_id 等标识写入模板；`_resolve_work` 再查回完整 spec；最后 `_partition_work` 使用它的运行指纹分组。

**回到父卡**：`config = getattr(data_source, "integration_config", None)` 只是取出已保存的接入配置。源码初始化片段之间还包含模式检查、采样参数、评估规格和游标设置，本次按当前问题省略。


### 初始化结果后来在哪里使用

| 已保存的内容 | 后续使用位置 |
| --- | --- |
| `integration_config` | `_run_harbor_rollout` 第 1 段读取，得到局部 `config` |
| `job_config` | `_run_partition` 生成临时 Job 配置时使用 |
| `_specs`、采样数量与游标 | [get_samples](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.get_samples.md#get-samples-mainline) 选择规格并取得模板组 |
| `_spec_by_id` | [_resolve_work](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_resolve_work.md#resolve-work-mainline) 通过 resolve_spec 查回完整规格 |
| spec 中的 `runtime_fingerprint` | [_run_round](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) 按 Agent 运行身份将工作分区 |

其中 `_build_registry` 是被调用的辅助函数：运行指纹实际在它内部计算并写入 `HarborPromptSpec`，不是构造方法在外面逐字段补写。本轮回查上述三个源码入口即可，完整实现保留在下方。

<details>
<summary>其余初始化内容：本轮只识别用途</summary>

采样相关配置包括训练/评估的每组尝试数、seed 和 shuffle；配置了评估源时也会建立 `_eval_specs`，统一纳入查询表。构造方法还设置 run_id，初始化 epoch/sample 游标和最近批次状态，计算后续一致性检查使用的摘要。它们不等同于 runtime_fingerprint，具体校验与恢复策略按相关问题再读。

</details>

## 我的直接表述（原话）

用户要求将数据源内容独立保存（节选）：

> 我觉得这里应该是单独生成一下这里的这个data source部分的内容?
> 不太适合直接在这个scope这里占看是我的理解?

这是记录位置与阅读范围的确认；尚无对完整初始化过程的独立复述。

随后用户询问：

> 那么这里的这个harbordatasource init的部分
> 我其实不是特别清楚
> datasource是创建harbordata source的对象?
> 然后这里的这个init就是这个data srouce创建的过程?
>
> 那么现在十二直接给出这里的这个datasource最终的返回的内容具体是什么样子吗?
> 还是说需要看一下这里第二build registry?
> 我其实不是特别清楚了

助手区分类、实例变量与初始化方法，先给出初始化后的对象状态示意，再建议看 _build_registry 如何产生其中的规格。尚未据此确认用户已理解构造语义。

## 尚不清楚

- 当前需要接清“配置 → spec/运行指纹 → ID 查询”的关系，效果待实际阅读反馈。
- 其他配置校验、规格摘要算法、训练/评估采样及持久化机制未完整展开。
- 外层框架构造数据源的调用栈不在本卡展开，当前只核对脚本入口与已收到的数据源对象。

<details>
<summary>完整构造方法与来源</summary>

固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`，本轮静态读取本地源码；未执行数据源初始化、Harbor Job 或模型请求。主线代码是跨位置节选，完整方法如下。

```python
def __init__(self, args: Any) -> None:
    self.args = args
    job_config_type = _harbor_job_config_type()

    integration_source = _first_config_value(
        args,
        (
            "harbor_integration_config",
            "harbor_integration_config_path",
            "dressage_harbor_integration_config",
            "dressage_harbor_integration_config_path",
        ),
        "DRESSAGE_HARBOR_INTEGRATION_CONFIG",
    )
    if integration_source is None:
        raise HarborDataSourceConfigurationError(
            "Harbor integration config is required; set "
            "DRESSAGE_HARBOR_INTEGRATION_CONFIG or args.harbor_integration_config"
        )
    self.integration_config = _load_integration_config(integration_source)
    if self.integration_config.execution_mode != "training":
        raise HarborDataSourceConfigurationError(
            "HarborDataSource requires integration execution_mode='training'"
        )
    self.integration_fingerprint = self.integration_config.fingerprint()

    self.n_samples_per_prompt = _positive_int_arg(
        args, "n_samples_per_prompt", default=1
    )
    estimator = str(getattr(args, "advantage_estimator", "") or "").lower()
    if estimator in {"grpo", "gspo"} and self.n_samples_per_prompt < 2:
        raise HarborDataSourceConfigurationError(
            f"{estimator.upper()} Harbor training requires "
            "n_samples_per_prompt >= 2"
        )
    self.n_samples_per_eval_prompt = _positive_int_arg(
        args,
        "n_samples_per_eval_prompt",
        default=self.n_samples_per_prompt,
    )

    self.rollout_seed = int(getattr(args, "rollout_seed", 42))
    self.rollout_shuffle = bool(getattr(args, "rollout_shuffle", False))

    job_source = _first_config_value(
        args,
        (
            "harbor_job_config",
            "harbor_job_config_path",
            "dressage_harbor_job_config",
            "dressage_harbor_job_config_path",
        ),
        "DRESSAGE_HARBOR_JOB_CONFIG",
    )
    if job_source is None:
        raise HarborDataSourceConfigurationError(
            "Harbor job config is required; set DRESSAGE_HARBOR_JOB_CONFIG "
            "or args.harbor_job_config"
        )
    self.job_config = _load_job_config(job_source, job_config_type)
    tasks = _resolve_tasks(self.job_config)
    self._specs = _build_registry(
        tasks=tasks,
        agents=getattr(self.job_config, "agents", None),
        integration_fingerprint=self.integration_fingerprint,
        scope="train",
    )

    eval_source = _first_config_value(
        args,
        (
            "harbor_eval_job_config",
            "harbor_eval_job_config_path",
            "dressage_harbor_eval_job_config",
            "dressage_harbor_eval_job_config_path",
        ),
        "DRESSAGE_HARBOR_EVAL_JOB_CONFIG",
    )
    self.eval_job_config: Any | None = None
    self._eval_specs: tuple[HarborPromptSpec, ...] = ()
    if eval_source is not None:
        self.eval_job_config = _load_job_config(eval_source, job_config_type)
        eval_tasks = _resolve_tasks(self.eval_job_config)
        self._eval_specs = _build_registry(
            tasks=eval_tasks,
            agents=getattr(self.eval_job_config, "agents", None),
            integration_fingerprint=self.integration_fingerprint,
            scope="eval",
        )

    self._spec_by_id = {
        spec.spec_id: spec for spec in (*self._specs, *self._eval_specs)
    }
    if len(self._spec_by_id) != len(self._specs) + len(self._eval_specs):
        raise HarborDataSourceConfigurationError(
            "resolved Harbor registry contains duplicate spec IDs"
        )

    run_id = _first_nonempty_attr(
        args, ("harbor_run_id", "training_run_id", "run_id")
    )
    if run_id is None:
        run_id = os.environ.get("DRESSAGE_HARBOR_RUN_ID")
    self._run_id_explicit = run_id is not None and run_id != ""
    self.run_id = str(run_id) if self._run_id_explicit else uuid.uuid4().hex

    self.epoch_id = 0
    self.sample_offset = 0
    self.sample_group_index = 0
    self.sample_index = 0
    self.last_batch_weight_version: str | None = None
    self.last_runtime_incarnation: str | None = None

    self._source_digest = _source_digest(
        self.job_config,
        n_samples=self.n_samples_per_prompt,
        seed=self.rollout_seed,
        shuffle=self.rollout_shuffle,
    )
    self._resolved_digest = _registry_digest(self._specs)
    self._eval_source_digest = (
        _source_digest(
            self.eval_job_config,
            n_samples=self.n_samples_per_eval_prompt,
            seed=self.rollout_seed,
            shuffle=False,
        )
        if self.eval_job_config is not None
        else None
    )
    self._eval_resolved_digest = (
        _registry_digest(self._eval_specs) if self._eval_specs else None
    )
```

形成过程：[Step 010：独立数据源构造卡](../../../../../../../step-010-harbor-rollout-entry/04-flow.md#datasource-constructor-card)。原有前置回查从父卡移入此处，来源和未读边界保留。

</details>
