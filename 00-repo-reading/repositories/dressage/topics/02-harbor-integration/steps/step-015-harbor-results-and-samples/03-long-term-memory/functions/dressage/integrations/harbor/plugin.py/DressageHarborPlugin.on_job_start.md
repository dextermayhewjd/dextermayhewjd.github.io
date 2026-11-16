# DressageHarborPlugin.on_job_start

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin.on_job_start.md) 完整继承；不改变原认识时间或掌握状态。

- 源码：[plugin.py:261–418](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L261)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独展开：Step 014，2026-11-13；此前 Step 010 看过调用位置，Step 011 看过部分回调登记。
- 最近认识更新：2026-11-13，用户已概括配置/URL 准备、写入配置与回调登记；各辅助实现未通读。

[Step 010 的 _run_partition](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#run-job) → **当前 on_job_start** → 返回后调用 job.run。此处是为解释 CLI 请求路由而回查较早的准备阶段。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Harbor Job 与插件对象已经创建，Job 尚未开始执行。
2. **具体内容**：取得 Gateway，为各份 TrialConfig 注入路由配置，保存关联资料，再登记生命周期回调。
3. **建议构建的心智模型**：

   > 先给待执行任务接好请求地址和事件处理，随后让 Harbor 正常运行 Job。

4. **调用代码**（_run_partition:760–762）：

   ```python
   await plugin.on_job_start(job)  # 直接执行当前准备函数。
   result = await job.run()        # 它返回后，Harbor 才开始执行这些尝试。
   await plugin.on_job_end(result)
   ```

## 本场景的输入与输出

输入是已创建的 Harbor Job；其待运行 TrialConfig 尚可修改。插件已有集成配置和 trial_bindings。正常返回 None，但 Job 的 Agent 配置与回调登记已更新，插件保存了 Gateway 租约和各 trial 的 slot 资料。

以下按正常路径保留三段交接。重复/恢复检查、网络审计、身份计算和失败清理折叠，未删除源码中的这些行为。

<a id="job-start-mainline"></a>

### 1. 取出待执行配置，取得 Gateway

```python
self._job_id = str(getattr(job, "id"))
self._compat = self._compat or _load_compat()
pending = list(_pending_trial_configs(self._compat, job))  # 已有的待运行 TrialConfig。

# 原码在此先检查配置和任务网络要求。
runtime = self._runtime or _default_gateway_runtime()
self._runtime = runtime
self._lease = await _maybe_await(runtime.acquire(self.config))
registry = runtime.secret_slots
gateway_url = _gateway_public_url(self.config, self._lease)  # 给 Agent 使用的地址。
```

<a id="job-start-routing"></a>

### 2. 给每份配置注入地址与身份

```python
for trial_config in pending:
    trial_name = str(getattr(trial_config, "trial_name"))
    original_agent = getattr(trial_config, "agent")
    agent = _deep_copy_model(original_agent)  # 修改配置副本，不是在这里创建运行中的 Agent。

    # 原码还计算并发分组、实例身份和网络审计信息。
    slot_id = f"{self._job_id}:{trial_name}"
    env_name = "DRESSAGE_HARBOR_ROUTE_" + hashlib.sha256(
        slot_id.encode()
    ).hexdigest()[:24].upper()
    token = registry.create(job_id=self._job_id, slot_id=slot_id, env_name=env_name)
    token = registry.current(slot_id)
    os.environ[env_name] = token             # 保存本次路由凭证。
    _inject_agent_routing(agent, self.config, env_name, gateway_url)
    trial_config.agent = agent              # 写回，供后续 Harbor 创建 Agent。
    # 原码将 slot_id/env_name/实例身份等保存到 self._slots[trial_name]。
```

上面调用的 [_inject_agent_routing](_inject_agent_routing.md#inject-routing-mainline) 写入 BASE_URL 和 token 引用；它返回后继续处理下一份配置。这一段准备 slot，具体尝试的 route/Proxy 在后面的 START 回调中登记。

<a id="job-start-hooks"></a>

### 3. 登记回调，返回 Job 调用方

```python
self._ensure_artifact_dependencies()
# 以下是在登记函数；不是现在执行这些回调。
job.on_trial_started(self._safe(self._on_start, "START"))          # 以后登记尝试路由。
job.on_agent_started(self._safe(self._on_agent_start, "AGENT_START")) # 以后打开本轮 turn。
job.on_agent_ended(self._safe(self._on_agent_end, "AGENT_END"))
job.on_verification_started(
    self._safe(self._on_verification_start, "VERIFICATION_START")
)
job.on_trial_cancelled(self._safe(self._on_cancel, "CANCEL"))
job.on_trial_ended(self._safe(self._on_end, "END"))
self._started = True
```

正常返回 [_run_partition](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#run-job)，下一行是 `await job.run()`。之后各 Trial 运行到对应事件，才触发刚登记的回调；需要继续追具体 Trial 路由时，再回查已登记的 [_on_start](DressageHarborPlugin._on_start.md#trial-start-mainline)；仅解释配置改写时，读完本段即可回到 ClaudeCode.run。

<details>
<summary>完整函数：检查、网络审计、身份资料与失败清理</summary>

```python
async def on_job_start(self, job: Any) -> None:
    """Validate/mutate pending configs and register all Trial hooks."""

    if self._started:
        raise RuntimeError("DressageHarborPlugin is already attached to a job")
    if bool(getattr(job, "is_resuming", False)):
        raise ValueError("Harbor job resume is not supported by this integration")

    self._job_id = str(getattr(job, "id"))
    self._compat = self._compat or _load_compat()
    pending = list(_pending_trial_configs(self._compat, job))
    if not pending:
        raise ValueError("Harbor job has no pending TrialConfigs")
    pending_names = {str(getattr(item, "trial_name")) for item in pending}
    if "" in pending_names or len(pending_names) != len(pending):
        raise ValueError("pending Harbor TrialConfigs must have unique non-empty names")
    unknown_bindings = sorted(set(self._trial_bindings) - pending_names)
    if unknown_bindings:
        raise ValueError(
            "trial_bindings contains unknown Harbor trial names: "
            + ", ".join(unknown_bindings)
        )
    # Resolve all fail-fast policy decisions before allocating a listener
    # or creating the first secret slot.  A CLI construction error must
    # never leave a usable route credential behind.
    _backend_headers(self.config)
    trial_network: dict[str, tuple[str, str]] = {}
    for trial_config in pending:
        trial_name = str(getattr(trial_config, "trial_name"))
        candidate_agent = getattr(trial_config, "agent")
        protocol = _agent_protocol(candidate_agent, self.config)
        _reject_alternative_auth(candidate_agent, protocol)
        task_dir = _existing_task_directory(getattr(trial_config, "task", None))
        if task_dir is None:
            raise RoutingPolicyError(
                "cannot locate resolved Harbor task.toml before allocating "
                "Gateway or route credentials"
            )
        cached = self._task_dir_audits.get(task_dir)
        if cached is None:
            cached = _audit_task_network_file(task_dir)
            self._task_dir_audits[task_dir] = cached
        digest, network_class = cached
        existing_class = self._network_audits.setdefault(digest, network_class)
        if existing_class != network_class:
            raise RoutingPolicyError(
                f"resolved task {digest} produced inconsistent network classes"
            )
        trial_network[trial_name] = (digest, network_class)
        if network_class == "public" and _routing_is_enforced(self.config):
            raise RoutingPolicyError(
                f"resolved Harbor task {digest} uses public network access and "
                "cannot satisfy security.routing_guarantee='enforced'"
            )

    public_count = sum(value == "public" for value in self._network_audits.values())
    if public_count and not _routing_is_enforced(self.config):
        logger.warning(
            "Harbor Job %s contains %d unique public-network task(s); "
            "configure_only injects Dressage routing but does not claim isolation",
            self._job_id,
            public_count,
        )

    runtime = self._runtime or _default_gateway_runtime()
    self._runtime = runtime
    self._lease = await _maybe_await(runtime.acquire(self.config))
    registry = runtime.secret_slots

    try:
        gateway_url = _gateway_public_url(self.config, self._lease)
    except Exception:
        await self.aclose()
        raise
    seen_names: set[str] = set()
    for trial_config in pending:
        trial_name = str(getattr(trial_config, "trial_name"))
        if not trial_name or trial_name in seen_names:
            raise ValueError(
                f"pending Harbor TrialConfig has duplicate/empty trial_name {trial_name!r}"
            )
        seen_names.add(trial_name)

        original_agent = getattr(trial_config, "agent")
        original_key = str(
            getattr(original_agent, "concurrency_key", _stable_dump(original_agent))
        )
        agent = _deep_copy_model(original_agent)
        if (
            getattr(agent, "n_concurrent", None) is not None
            and getattr(agent, "concurrency_group", None) is None
        ):
            agent.concurrency_group = (
                "dressage:" + hashlib.sha256(original_key.encode()).hexdigest()[:24]
            )

        protocol = _agent_protocol(agent, self.config)
        _reject_alternative_auth(agent, protocol)
        task_fingerprint = _stable_dump(getattr(trial_config, "task", None))
        agent_fingerprint = hashlib.sha256(original_key.encode()).hexdigest()
        instance_id = _logical_instance_id(
            self._job_id,
            task_fingerprint,
            agent_fingerprint,
        )
        binding = self._trial_bindings.get(trial_name)
        if binding is not None:
            instance_id = binding.instance_id
        resolved_task_sha256, task_network_class = trial_network[trial_name]
        slot_id = f"{self._job_id}:{trial_name}"
        env_name = "DRESSAGE_HARBOR_ROUTE_" + hashlib.sha256(
            slot_id.encode()
        ).hexdigest()[:24].upper()
        try:
            token = registry.create(
                job_id=self._job_id,
                slot_id=slot_id,
                env_name=env_name,
            )
            if inspect.isawaitable(token):
                raise TypeError("SecretSlotRegistry.create must be synchronous")
            token = registry.current(slot_id)
            os.environ[env_name] = token
            _inject_agent_routing(agent, self.config, env_name, gateway_url)
            trial_config.agent = agent
            self._slots[trial_name] = SlotRecord(
                slot_id=slot_id,
                env_name=env_name,
                trial_name=trial_name,
                instance_id=instance_id,
                agent_fingerprint=agent_fingerprint,
                resolved_task_sha256=resolved_task_sha256,
                task_network_class=task_network_class,
                bound_attempt_ordinal=(
                    binding.attempt_ordinal if binding is not None else None
                ),
                expected_weight_version=(
                    binding.expected_weight_version if binding is not None else None
                ),
            )
        except Exception:
            await self.aclose()
            raise

    try:
        self._ensure_artifact_dependencies()
        job.on_trial_started(self._safe(self._on_start, "START"))
        job.on_agent_started(self._safe(self._on_agent_start, "AGENT_START"))
        job.on_agent_ended(self._safe(self._on_agent_end, "AGENT_END"))
        job.on_verification_started(
            self._safe(self._on_verification_start, "VERIFICATION_START")
        )
        job.on_trial_cancelled(self._safe(self._on_cancel, "CANCEL"))
        job.on_trial_ended(self._safe(self._on_end, "END"))
    except Exception:
        await self.aclose()
        raise
    self._started = True
```

</details>

## 我的直接表述（原话）

> 好的 那么当前是否能够在这个step14展开呢? 你觉得?

本轮职责复述（节选）：

> 好的 我的简单理解是 这里一开的步骤更多的是
> config
> 然后一些就是网络部分相关的url什么的内容
> 之后在这个config里面写入一系列内容
> 等级一系列的回调

用户同时反馈函数多、内容杂。助手据本轮目标收拢为地址、路由身份、回调登记三个成果；配置检查与辅助实现继续按需回查，不将全部函数列为下一轮必读。

## 尚不清楚

- _on_start 已进入独立卡；_on_agent_start 怎样开启 turn，后续沿实际需要继续。
- Gateway 请求分派、网络审计与异常清理的内部实现暂缓。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对 plugin.py:261–418、_inject_agent_routing:1031–1074 与 rollout.py:760–762。
- 本页为同一正常路径的阶段节选，完整参数与失败路径可在折叠源码中核对；未把省略视为行为不存在。
- Dressage 的原依赖约束仍是 Harbor 0.18；当前 Harbor 阅读基线为 v0.25.0，_load_compat 等跨版本运行尚未实际验证。
- 未执行 Gateway 启动、token 写入、Job 或模型请求。[本轮记录](../../../../../../../step-014-model-routing-and-api-contract/04-flow.md#on-job-start-expanded)。

</details>
