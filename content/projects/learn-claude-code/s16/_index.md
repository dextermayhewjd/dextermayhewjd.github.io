---
title: "S16 Workflow Runtime：用可恢复脚本编排多步工作"
weight: 160
summary: "在 S15 中注册 Workflow 工具，可信脚本通过并行原语、结构校验与 journal 协调单步调用，完整运行结束后返回一次结果。"
ShowToc: false
compactDiagramLegends: true
---

{{< chapter-outline id="s16-workflow-outline" title="S16 本章目录" >}}

## 1. 定位：模型做单步，脚本决定编排 {#workflow-position}

### 1.1 我想弄清楚的问题 {#workflow-question}

S15 由模型逐轮决定调用什么。反复做同一类审查时，我已经知道“多维度审计 → 验证发现 → 汇总排序”这套步骤，能否把顺序写成固定脚本，同时保存已经完成的结果？

我的理解是：**Workflow 是主工具循环中的一个入口，背后执行宿主保存的编排代码。模型负责每个单步的判断；脚本负责依赖、并行和汇总；journal 负责复用已完成调用。**

源码基准为本地 `ce8f9f1` 的 [s16_workflow_runtime/code.py](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s16_workflow_runtime/code.py)。函数按真实源码摘录，类方法保留 self；伪代码另行标记。按 [MIT 许可](/examples/s16-repo/NOTICE.txt)使用。

### 1.2 与 TODO、Task、Skill 和 Subagent 的区别 {#workflow-comparison}

| 机制 | 谁决定后续步骤 | 保存什么／返回什么 |
|---|---|---|
| TODO | 模型参考清单继续行动 | 当前会话清单 |
| Task System | 模型或队友按任务依赖行动 | 有 ID、owner 和状态的任务记录 |
| Skill | 模型阅读方法说明后选工具 | 可加载的指令与参考资源 |
| Subagent | 一个子循环选择自己的工具 | 父调用等待一次摘要 |
| Workflow | 宿主脚本预先写好编排 | 单步结构化值、运行产物与可复用 journal |

本地 workflow 子 Agent 也不等于 S06：真实 runner 每次只请求一个回答，没有 tools 参数和子工具循环；它只能判断传入的文本。

**等待边界：** 主 Agent 经同步适配器等待整套 workflow，最后收到一个 tool_result。内部多个调用可以并发，async_launched 与进度事件会在运行期间打印，但它们没有提前让父工具返回。

### 1.3 三图：从 S15 到可恢复脚本 {#workflow-architecture}

#### 图 1：回顾 S15 的默认总览

{{< architecture from="/projects/learn-claude-code/s15" width="1200" src="images/harness-agent-integration.svg" mode="baseline" modified="tools,pool,handler" label="图 1：直接保留 S15 整体结构，标出 Workflow schema 与同步 handler 的扩展位置" caption="图 1：保留 S15 的节点和连线。橙色位置将增加 Workflow 的模型定义与 handler；主模型循环、上下文、事件桥和原权限逻辑继续保留，不把新 runtime 提前画进第一张图。" >}}

#### 图 2：Workflow 作为工具连接完整系统

{{< architecture-explorer id="s16-workflow-explorer" modules="explorer.json" roles="function-roles.json" width="1200" src="images/workflow-agent-integration.svg" legend="evolution" label="图 2：Workflow 经 S15 权限与分发进入同步适配器，可信脚本用 runner 和 journal 执行完整运行，结束后一次返回" caption="图 2：原主线与 S15 模块位置保留，下方紫色展开 Workflow 入口、脚本原语、存储与事件／最终回传。一次 Workflow 调用等待运行完成，再经原 PostToolUse 与 tool_result 回到消息历史；进度不走 S15 异步事件桥。" >}}

默认 CLI 真正导入 S15 并安装这个工具，所以原能力继续可用。这里新增的是一个独立 runtime；不用复制另一份主 Agent Loop，也没有把 workflow 进度注册到 background_results 或 Lead 邮箱。

#### 图 3：运行、单步调用与续跑的最小核心

{{< architecture figureId="s16-workflow-core" functionExplorer="s16-workflow-explorer" trace="true" width="1000" src="images/workflow-core.svg" legend="evolution" label="图 3：校验与运行锁、可信脚本、单步调用、journal 命中或 runner 结构校验、资源边界和运行收尾" caption="图 3：上方是工具进入可信脚本，下方解释单步缓存、runner、资源与收尾。journal 命中直接回给脚本；未命中才运行模型并校验保存。_call_locked 负责整个生命周期，在准备和收尾两处出现不表示调用两遍。点击内部函数名查看源码。" >}}

{{< mechanism-function-index id="s16-workflow-functions" explorer="s16-workflow-explorer" class="WorkflowJournal" >}}

<details>
<summary>查看上游“一次调用、一次完整回传”的原图</summary>

![上游 Workflow Runtime 总览](/examples/s16-repo/workflow-runtime-overview.svg)

原图明确区分 async_launched 事件与最终返回。本博客借用这个边界，延续自己的演化颜色；所有循环回线仍放在主线下方。

</details>

## 2. 接入：注册可信脚本，再加入主工具池 {#workflow-install}

### 2.1 模型可提供名称与参数，宿主提供代码 {#workflow-schema}

模型只传 name、args、可选 resume_from_run_id。WORKFLOWS 保存可信的 meta 与 script_fn；模型不提交 Python 源码、函数对象或元数据。

```python
WORKFLOW_TOOL = {
    "name": "Workflow",
    "description": "Run a saved workflow by name. Pass input in args.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "args": {"type": "object"},
            "resume_from_run_id": {"type": "string"},
        },
        "required": ["name"],
        "additionalProperties": False,
    },
}

SAMPLE_META = {
    "name": "review-changes",
    "description": "Review changed files across dimensions, verify each finding",
    "phases": ["Review", "Verify"],
}

WORKFLOWS = {SAMPLE_META["name"]: (SAMPLE_META, sample_workflow)}
```

样例名是 review-changes。当前 schema 没有枚举已注册名称，安装也没有把整个 WORKFLOWS 目录写进 SYSTEM；示例使用用户明确提供的名称。若希望模型自主挑选脚本，可以另设计名称与用途目录，不能把“宿主已注册”理解成“模型自动知道所有名称”。

### 2.2 run_workflow 与同步适配器分别在哪一层 {#workflow-adapter}

**所属层：** 模型工具适配。run_workflow 校验参数、按名称查 registry，把宿主 meta / script_fn 交给 WorkflowTool；返回 JSON 可写的 launched、result 和 task。

```python
async def run_workflow(name, args=None, resume_from_run_id=None):
    """Model-facing adapter: resolve trusted code from the host registry."""
    if not isinstance(name, str):
        raise WorkflowInputError("workflow name must be a string")
    if name not in WORKFLOWS:
        raise WorkflowInputError(f"unknown workflow '{name}'")
    if args is not None and not isinstance(args, dict):
        raise WorkflowInputError("workflow args must be an object")
    meta, script_fn = WORKFLOWS[name]
    out = await WorkflowTool().call(
        meta,
        script_fn,
        args=args,
        resume_from_run_id=resume_from_run_id,
    )
    return {
        "launched": out["launched"],
        "result": out["result"],
        "task": serialize_task(out["task"]),
    }
```

```python
def serialize_task(task):
    return {
        "taskId": task.task_id,
        "taskType": "local_workflow",
        "runId": task.run_id,
        "workflowName": task.meta["name"],
        "status": task.status,
        "usage": dict(task.usage),
        "progress": list(task.progress),
    }
```

```python
def run_workflow_sync(**tool_input):
    """Bridge the synchronous host dispatcher to the async workflow runtime."""
    try:
        return json.dumps(asyncio.run(run_workflow(**tool_input)), default=str)
    except WorkflowInputError as exc:
        return f"Error: {exc}"
```

run_workflow_sync 用 asyncio.run 等待协程结束，再把整个返回值序列化成字符串。WorkflowInputError 在这个入口变成 Error；其他 handler 异常仍由 S15 的 call_tool_handler 处理。

### 2.3 install_workflow_tool：扩展组装函数，不改主循环 {#workflow-host}

**所属层：** 宿主安装。保存原 assemble_tool_pool，包装它的返回值，追加 schema 与同步 handler。重复安装不再追加工具；runner 工厂绑定宿主 client 与 MODEL。

```python
def install_workflow_tool(host):
    """Extend the s15 host tool pool without changing its dispatch loop."""
    global RUNNER_FACTORY
    RUNNER_FACTORY = lambda: AnthropicAgentRunner(host.client, host.MODEL)
    if getattr(host, "_workflow_tool_installed", False):
        return
    base_assemble = host.assemble_tool_pool

    def assemble_with_workflow():
        tools, handlers = base_assemble()
        if not any(tool.get("name") == "Workflow" for tool in tools):
            tools.append(WORKFLOW_TOOL)
        handlers["Workflow"] = run_workflow_sync
        return tools, handlers

    host.assemble_tool_pool = assemble_with_workflow
    host._workflow_tool_installed = True
```

```python
def load_integrated_host():
    """Load s15 lazily so deterministic workflow tests need no API key."""
    path = Path(__file__).resolve().parents[1] / "s15_integrated_harness" / "code.py"
    spec = importlib.util.spec_from_file_location("integrated_host", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load integrated host from {path}")
    host = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = host
    spec.loader.exec_module(host)
    return host
```

无 MCP 连接时，内置 schema 从 26 增至 **27**，普通 handler 从 25 增至 **26**；compact 的特殊分支保持不变。S15 的 SYSTEM 工具名称说明没有同步追加 Workflow，模型当前通过 tools 的定义获得这个入口。

默认 run_cli 调用这两个函数，再沿用 S15 的 history、context、agent_lock、后台服务与事件桥。主回合持锁执行 Workflow 时，其他主会话回合也要等待；脚本内部并发不会释放父工具的等待边界。

### 2.4 WorkflowTool.call：校验、分配身份与持锁 {#workflow-launch}

**所属层：** 内部运行入口。输入宿主提供的 meta / script_fn 与模型参数；校验元数据、检查配置，选择新 run ID 或续跑 ID，持整个 run 的锁后进入生命周期。

```python
async def call(self, meta, script_fn, args=None, resume_from_run_id=None):
    validate_meta(meta)
    check_permission(meta)
    resuming = resume_from_run_id is not None
    if resuming:
        run_id = validate_run_id(resume_from_run_id)
    else:
        run_id = reserve_run_id(meta)
    with workflow_run_lock(run_id):
        return await self._call_locked(
            meta, script_fn, args, run_id, resuming
        )
```

```python
def validate_meta(meta):
    """Validate name, description, and optional phases before launch."""
    if not isinstance(meta, dict):
        raise WorkflowInputError("meta must be an object literal")
    if not meta.get("name") or not meta.get("description"):
        raise WorkflowInputError("meta requires `name` and `description`")
    if not isinstance(meta["name"], str) or not WORKFLOW_NAME_RE.fullmatch(meta["name"]):
        raise WorkflowInputError(
            "meta.name must be a 1-64 character slug using letters, numbers, '.', '_', or '-'"
        )
    if not isinstance(meta["description"], str):
        raise WorkflowInputError("meta.description must be a string")
    if "phases" in meta:
        if not isinstance(meta["phases"], list) or not all(
            isinstance(phase, str) and phase for phase in meta["phases"]
        ):
            raise WorkflowInputError("meta.phases must be a list of non-empty strings")
    return meta
```

```python
def check_permission(meta, settings=None):
    """Apply the s03 allow/deny gate before launching a workflow."""
    settings = settings or {}
    if meta["name"] in settings.get("deny", []):
        raise WorkflowInputError(f"workflow '{meta['name']}' denied by settings")
    return "allow"
```

```python
def reserve_run_id(meta) -> str:
    """Reserve a fresh run identity before any journal can be truncated."""
    STORE.mkdir(parents=True, exist_ok=True)
    for _ in range(32):
        run_id = validate_run_id(create_run_id(meta))
        snapshot_path = STORE / f"{run_id}.json"
        try:
            fd = os.open(snapshot_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            continue
        os.close(fd)
        return run_id
    raise WorkflowInputError("could not allocate a unique workflow runId")
```

本地 check_permission 支持 deny 名单，但 call 没有传 settings，默认采用空配置放行。S15 的 PreToolUse 仍会运行；这里没有另加交互启动审批。

run ID 用安全名称和随机串组成，快照文件用排他创建预留，之后才打开新的 journal，避免名字碰撞时覆盖旧运行。LocalWorkflowTask 的 ID 是 local_workflow 类型，不是 S10 的 task_ ID，也不写入 .tasks。

## 3. 执行：固定脚本协调结构化单步 {#workflow-execution}

### 3.1 ExecutionState 向脚本提供哪些原语 {#workflow-primitives}

| 方法 | 输入 | 输出／副作用 |
|---|---|---|
| agent | prompt、可选 schema / label / phase | 单步值，或已缓存的值 |
| parallel | 一组延迟调用 thunks | 并发执行，等齐这组结果 |
| pipeline | items 与若干 stage | 各 item 独立按阶段传值，最后收集所有结果 |
| phase | 阶段名 | 标记显示阶段，首次出现时记录进度 |
| log | 日志文字 | 记录 workflow_log |
| workflow | 注册名称与 args | 内联调用一层子 workflow，共享本 run 的资源 |

ctx 不提供文件／Shell 工具；但注册脚本本身是宿主信任的 Python 函数，这个小接口不是沙箱。默认 runner 同样没有文件或 Shell 工具，变更必须通过 args.changes 等参数传入。

阶段名用于显示，不是执行屏障。共享 _phase 可能被别的 pipeline 分支更新，样例给 agent 显式 phase，让审计与验证分组仍清楚。

```python
def phase(self, title):
    """Start a phase; subsequent agent()s group under it. Upsert: emitting the
    same phase again (e.g. from each pipeline item) does not re-announce it."""
    self._phase = title
    if title not in self._phases_seen:
        self._phases_seen.add(title)
        self.task.progress_event("workflow_phase", title=title)
```

```python
def log(self, message):
    """Emit a workflow_log progress line."""
    self.task.progress_event("workflow_log", message=message)
```

```python
async def workflow(self, name, args=None):
    """Run a saved workflow inline as a child (one level), sharing this run's
    journal + budget + agent counter."""
    if self._depth >= 1:
        raise WorkflowInputError("workflow() nesting is one level only")
    if name not in WORKFLOWS:
        raise WorkflowInputError(f"unknown workflow '{name}'")
    meta, fn = WORKFLOWS[name]
    child = ExecutionState(self.task, self.journal, self.runner, self.budget,
                           args or {}, depth=self._depth + 1,
                           limits=self._limits)
    return await fn(child, args or {})
```

子 workflow 与父级共享 task、journal、runner、budget、agent 计数和 semaphore，不另分配 run ID；depth 限制只允许一层嵌套。

### 3.2 parallel 与 pipeline：等齐的位置不同 {#workflow-concurrency}

**parallel：** 先构造各 thunk 的协程，再 gather 并发；只有整组正常完成才返回结果。结果顺序对应输入顺序，而非完成顺序。[Python gather 文档](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.gather)

```python
async def parallel(self, thunks):
    """BARRIER: run all thunks concurrently and fail if any thunk fails."""
    return await asyncio.gather(*[thunk() for thunk in thunks])
```

**pipeline：** 每个 item 的 stages 顺序执行；不同 item 同时推进。item A 审计结束即可验证，不必等 item B 完成审计。外层 gather 最终仍等所有 item 返回。

```python
async def pipeline(self, items, *stages):
    """Per-item staged flow, NO barrier between stages: item A can be in
    stage 3 while item B is still in stage 1. Each stage gets
    (prev_result, original_item, index). A throwing stage fails the workflow."""
    async def run_item(item, idx):
        value = item
        for stage in stages:
            value = await stage(value, item, idx)
        return value
    return await asyncio.gather(*[run_item(it, i) for i, it in enumerate(items)])
```

```text
parallel:  A + B + C  -> wait for all -> aggregate
pipeline:  A: audit -> verify -> value
           B: audit -> verify -> value
           C: audit -> verify -> value
           wait for all final values -> aggregate
```

某一步异常会使脚本失败；gather 本身不保证自动取消所有其他 awaitable。这里不扩写通用错误恢复，理解它没有跨步骤回滚承诺即可。[对应行为](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.gather)

### 3.3 agent：先找缓存，未命中再调用 runner {#workflow-agent}

**所属层：** 单步执行。先计数与检查预算，计算 key、查看 journal；命中时按当前 schema 再验证并返回。未命中才在 semaphore 下执行同步 runner，校验结果、记录消耗并写 journal。

```python
async def agent(self, prompt, schema=None, label=None, phase=None):
    """Spawn one subagent. With a schema, force StructuredOutput + validate
    (retry once). On resume, a cached key short-circuits the run."""
    label = label or (prompt[:24] + "...")
    self._limits.claim_agent()
    if self.budget.remaining() <= 0:
        raise WorkflowInputError("token budget exceeded")

    key = self.journal.key("agent", label, prompt, schema)
    cached = self.journal.cached(key)
    if cached is not MISS:
        if schema is not None:
            ok, err = SimpleJsonSchema(schema).validate(cached)
            if not ok:
                raise WorkflowInputError(
                    f"cached agent output failed schema validation: {err}"
                )
        self.task.progress_event("workflow_agent", label=label,
                                 phase=phase or self._phase, status="cached")
        return cached

    async with self._limits.semaphore:
        run = await asyncio.to_thread(
            self.runner.run, prompt, schema, label
        )
        result = run.value
        tokens = run.tokens

    if schema is not None:
        ok, err = SimpleJsonSchema(schema).validate(result)
        if not ok:
            retry = await asyncio.to_thread(
                self.runner.run,
                prompt + "\n\nReturn valid JSON.",
                schema,
                label,
            )
            result = retry.value
            tokens += retry.tokens
            ok, err = SimpleJsonSchema(schema).validate(result)
            if not ok:
                raise WorkflowInputError(f"agent({{schema}}) invalid output: {err}")

    self.budget.add(tokens)
    self.task.usage["agents"] += 1
    self.task.usage["tokens"] += tokens
    self.journal.record(key, result)
    self.task.progress_event("workflow_agent", label=label,
                             phase=phase or self._phase, status="done")
    return result
```

asyncio.to_thread 把同步 runner 放在线程执行，避免阻塞内部事件循环。这个并发只属于 workflow 内部；父 S15 工具仍等待。

schema 不匹配时再请求一次合法 JSON，仍不合法就停止这次脚本。格式通过只说明结构符合要求，不保证发现的事实正确。

### 3.4 真实 runner 与简化结构校验 {#workflow-runner}

**所属层：** 模型调用边界。真实 runner 只带本步 prompt 和 schema 文字，单次请求 max_tokens=2000；没有 tools，也没有执行 Shell 的子循环。解析值与实际 usage 打包成 RunnerOutput。

```python
def run(self, prompt, schema=None, label=None):
    request = prompt
    if schema is not None:
        request += (
            "\n\nReturn only one JSON object matching this schema:\n"
            + json.dumps(schema, ensure_ascii=True, sort_keys=True)
        )
    response = self.client.messages.create(
        model=self.model,
        system=(
            "You are a focused workflow agent. Complete only the supplied step. "
            + f"{WORKFLOW_AGENT_ENVIRONMENT} "
            + "Do not claim access to files or results not included in the prompt."
        ),
        messages=[{"role": "user", "content": request}],
        max_tokens=2000,
    )
    text = _response_text(response)
    if schema is None:
        value = text
    else:
        try:
            value = _parse_runner_json(text)
        except WorkflowInputError:
            # Let ExecutionState's schema check trigger its single retry.
            value = text
    usage = getattr(response, "usage", None)
    tokens = int(getattr(usage, "input_tokens", 0) or 0) + int(
        getattr(usage, "output_tokens", 0) or 0
    )
    return RunnerOutput(value, tokens)
```

这里用提示要求 JSON，再由 _parse_runner_json 与本地 validator 解析／检查，不是配置 API 严格结构化输出解码。

**所属层：** 简化校验器。支持 required、object、array、string、boolean、number 与 enum 等本例需求；递归检查字段与元素。

```python
def validate(self, value, schema=None):
    schema = self.schema if schema is None else schema
    if "enum" in schema and value not in schema["enum"]:
        return False, f"expected one of {schema['enum']}"
    t = schema.get("type")
    if t == "object":
        if not isinstance(value, dict):
            return False, "expected object"
        for key in schema.get("required", []):
            if key not in value:
                return False, f"missing required key '{key}'"
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                ok, err = self.validate(value[key], sub)
                if not ok:
                    return False, f"{key}: {err}"
        return True, None
    if t == "array":
        if not isinstance(value, list):
            return False, "expected array"
        items = schema.get("items")
        if items:
            for i, el in enumerate(value):
                ok, err = self.validate(el, items)
                if not ok:
                    return False, f"[{i}]: {err}"
        return True, None
    if t == "string":
        return (isinstance(value, str), None if isinstance(value, str) else "expected string")
    if t == "boolean":
        return (isinstance(value, bool), None if isinstance(value, bool) else "expected boolean")
    if t in ("number", "integer"):
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
        return (ok, None if ok else "expected number")
    return True, None
```

它不是完整 JSON Schema：未知类型等会直接通过，integer 也沿用 int / float 检查。不要据此认为所有参数与输出规范都已严格实施。

### 3.5 review-changes：一份具体的可信脚本 {#workflow-example}

**脚本作用：** 四个维度各自审计，随后并行验证该维度的每项 finding；最后汇总 isReal 为真的发现，按 high / medium / low 排序。脚本里的值存在变量中，只有最终结果与任务状态回到父 messages。

```python
async def sample_workflow(ctx, args):
    """pipeline over review dimensions (audit -> verify-each), then keep only the
    findings a verifier confirms. The plan is code, not a chat turn."""
    ctx.phase("Review")
    changes = args.get("changes", "")
    if not isinstance(changes, str):
        raise WorkflowInputError("args.changes must be a string")
    review_input = changes.strip() or "No change context was supplied."

    async def audit(_value, dimension, _idx):
        out = await ctx.agent(
            f"Review this change context for {dimension} issues. "
            "Report only issues supported by the supplied text.\n\n"
            f"{review_input}",
            schema=FINDINGS_SCHEMA, label=f"audit:{dimension}", phase="Review")
        return {"dimension": dimension, "findings": out["findings"]}

    async def verify(audited, dimension, _idx):
        ctx.phase("Verify")
        # Each finding is verified by its own adversarial subagent, concurrently.
        verdicts = await ctx.parallel([
            (lambda f=f: ctx.agent(
                f"Adversarially verify this {dimension} finding against the "
                "supplied change context.\n\n"
                f"Change context:\n{review_input}\n\n"
                f"Finding:\n{json.dumps(f, ensure_ascii=True)}",
                schema=VERDICT_SCHEMA, label=f"verify:{dimension}:{f['title']}", phase="Verify"))
            for f in audited["findings"]])
        confirmed = [f for f, v in zip(audited["findings"], verdicts)
                     if v and v.get("isReal")]
        return {"dimension": dimension, "confirmed": confirmed}

    results = await ctx.pipeline(DIMENSIONS, audit, verify)
    confirmed = [{"dimension": r["dimension"], **f}
                 for r in results if r for f in r["confirmed"]]
    confirmed.sort(key=lambda f: {"high": 0, "medium": 1, "low": 2}.get(f["severity"], 3))
    ctx.log(f"confirmed {len(confirmed)} real finding(s)")
    return {"confirmed": confirmed}
```

lambda f=f 保存各次 finding，避免延迟调用都读到最后一项，语言细节可回看 [S14 的绑定说明](../s14/#mcp-binding)。这个样例做汇总与排序，没有实现去重；README 问题描述里的“去重”是应用目标示例，不是当前函数已有步骤。

## 4. 续跑与收尾：journal 保存调用结果，脚本重新执行 {#workflow-resume}

### 4.1 本地存储与整个 run 的互斥 {#workflow-storage}

产物默认放在 s16_workflow_runtime/.runtime，而非用户工作区的 .tasks：

```text
.runtime/
  wf_review-changes_<id>.json
  wf_review-changes_<id>.output.json
  wf_review-changes_<id>.journal.jsonl
  wf_review-changes_<id>.lock
  last_run.txt
```

| 文件 | 保存什么 |
|---|---|
| 快照 .json | workflowName、原 args、task 状态与进度；启动和结束时更新 |
| output.json | 最终脚本结果 |
| journal.jsonl | 每个成功校验单步的 key / value |
| .lock | 同 run 的线程／进程互斥协调 |
| last_run.txt | demo / resume 的最近运行入口 |

**所属层：** run 锁。线程锁加非阻塞 fcntl 文件锁，涵盖整次脚本执行与最终写盘；相同 ID 已在运行就拒绝，不让两个进程同时续跑它。

```python
@contextmanager
def workflow_run_lock(run_id: str):
    """Hold one run across threads and host processes for its full lifecycle."""
    with _run_locks_guard:
        local_lock = _run_locks.setdefault(run_id, threading.Lock())
    if not local_lock.acquire(blocking=False):
        raise WorkflowInputError(f"workflow run {run_id} is already active")

    handle = None
    try:
        STORE.mkdir(parents=True, exist_ok=True)
        handle = (STORE / f"{run_id}.lock").open("a+", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise WorkflowInputError(
                f"workflow run {run_id} is already active"
            ) from exc
        yield
    finally:
        if handle is not None:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()
        local_lock.release()
        with _run_locks_guard:
            if not local_lock.locked() and _run_locks.get(run_id) is local_lock:
                _run_locks.pop(run_id, None)
```

本地依赖 fcntl，按当前 Unix 环境阅读；文件锁只协调遵守这份契约的运行时。快照／输出通过 _write_json 的临时文件与 os.replace 写入，journal 则逐条追加并 flush。

### 4.2 Journal 初始化、稳定 key 与缓存值 {#workflow-journal}

**所属层：** WorkflowJournal。新 run 打开空日志；resume 先逐行校验 key / value 记录并重建 cache，再以追加方式打开。损坏记录会在执行脚本前被拒绝。

```python
def __init__(self, run_id, resume, store=None):
    store = STORE if store is None else store
    store.mkdir(parents=True, exist_ok=True)
    self.path = store / f"{run_id}.journal.jsonl"
    self.resume = resume
    self.cache = {}
    if resume:
        if not self.path.exists():
            raise WorkflowInputError(f"resume journal not found for {run_id}")
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            try:
                rec = json.loads(line)
                if (
                    not isinstance(rec, dict)
                    or not isinstance(rec.get("key"), str)
                    or "value" not in rec
                ):
                    raise ValueError("expected key/value record")
            except (json.JSONDecodeError, ValueError) as exc:
                raise WorkflowInputError(
                    f"invalid resume journal record at line {line_number}"
                ) from exc
            self.cache[rec["key"]] = rec["value"]
        self._f = self.path.open("a", encoding="utf-8")
    else:
        self._f = self.path.open("w", encoding="utf-8")             # fresh run truncates
```

```python
def key(self, kind, label, prompt, schema):
    # Deterministic semantic key, independent of concurrency order, so a
    # parallel/pipeline call gets the same key on resume.
    basis = f"{kind}|{label}|{prompt}|{json.dumps(schema, sort_keys=True)}"
    return f"{kind}-{_stable_hash(basis) % 10**10:010d}"
```

```python
def _stable_hash(s: str) -> int:
    """Process-stable hash (Python's hash() is salted per process, which would
    break resume keys across `run` and `resume`)."""
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)
```

```python
def cached(self, key):
    return self.cache.get(key, MISS)
```

```python
def record(self, key, value):
    self._f.write(json.dumps({"key": key, "value": value}) + "\n")
    self._f.flush()
    self.cache[key] = value
```

key 基于 kind、label、prompt、排序后的 schema，经 SHA-256 后取 10 位十进制表示；不使用跨进程会变化的 Python hash() 或并发完成计数器。MISS 区分“没有记录”与“值恰好是 None”。

key 不包含模型、脚本版本、phase 或全部外部环境，也不是无碰撞保证。它提供单步结果复用，不等于记录整份 Python 执行现场或保证副作用只执行一次。

### 4.3 resume：原参数一致，重新走脚本控制流 {#workflow-replay}

WorkflowTool 在恢复时先读取快照，验证 workflowName；args 省略就使用原值，显式提供则必须与原 args 相同。确认 journal 可读后，再登记此次运行状态。

**同一个脚本会重新执行。** 每次 agent 根据当前 prompt / schema / label 匹配旧结果。只有 key 不命中才运行模型；下游是否重跑取决于它实际使用的输入是否变化，不存在另外一份自动依赖失效图。

脚本里 agent 之外的代码会再次执行。改变顶层 args 不能复用原 run，需创建新运行；编辑脚本造成单步 prompt 等变化，则相关 key 不同。即使全部命中，本次仍重建 task 与进度，demo 显示 agents=0 / tokens=0 表示没有新的 runner 消耗。

### 4.4 资源边界与记录口径 {#workflow-limits}

本地初始并发上限 8，agent() 调用上限 1000，可用 args.budget 指定 token 预算。嵌套 workflow 共享这些对象。

```python
def claim_agent(self):
    self.agents += 1
    if self.agents > AGENT_CAP:
        raise WorkflowInputError(f"agent() cap reached ({AGENT_CAP})")
```

```python
def remaining(self):
    return float("inf") if self.total is None else max(0, self.total - self._spent)
```

```python
def add(self, n):
    if self.total is not None and self._spent + n > self.total:
        raise WorkflowInputError(
            f"token budget exceeded ({self._spent + n} > {self.total})"
        )
    self._spent += n
```

两个细节要看源码位置：claim_agent 与预算检查发生在缓存查询前，所以命中调用也计入上限；tokens 由 runner 返回后才扣账，成功步骤的 task.usage 才更新。

初次 runner 受 semaphore 控制，但 schema 修正调用位于该块之外；并发调用也是返回后才加预算。因此这些是教学约束，不保证所有请求永远严格限制为 8 或提前避免一切超预算消耗。

### 4.5 完整生命周期：一次启动事件，一次最终返回 {#workflow-lifecycle}

**所属层：** WorkflowTool 的持锁运行。这里完成恢复检查、task 创建、事件、脚本等待和产物写入。

```python
async def _call_locked(self, meta, script_fn, args, run_id, resuming):
    if resuming:
        snapshot = _read_snapshot(run_id)
        if snapshot.get("workflowName") != meta["name"]:
            raise WorkflowInputError("resume runId does not match workflow meta")
        saved_args = snapshot.get("args", {})
        if args is None:
            args = saved_args
        elif args != saved_args:
            raise WorkflowInputError("resume args do not match the original run")
        journal = WorkflowJournal(run_id, resume=True)
    else:
        args = args or {}
        journal = WorkflowJournal(run_id, resume=False)
    task_id = create_task_id(run_id)

    task = LocalWorkflowTask(task_id, run_id, meta)
    # Record the launch envelope before workflow execution starts.
    launched = {"status": "async_launched", "taskId": task_id,
                "taskType": "local_workflow", "runId": run_id,
                "workflowName": meta["name"]}
    task.event("async_launched", runId=run_id, taskId=task_id)
    task.event("task_started", workflow=meta["name"],
               phases=",".join(meta.get("phases", [])) or "-",
               resume=resuming)
    _write_json(STORE / f"{run_id}.json", {
        "runId": run_id,
        "workflowName": meta["name"],
        "args": args,
        "task": serialize_task(task),
    })

    try:
        ctx = ExecutionState(
            task, journal, RUNNER_FACTORY(), Budget(args.get("budget")), args
        )
        result = await script_fn(ctx, args)
        task.status = "completed"
    except Exception as e:                          # failed / stopped close the loop too
        task.status = "failed"
        result = {"error": str(e)}
    finally:
        journal.close()

    _write_json(STORE / f"{run_id}.output.json", result)
    _write_json(STORE / f"{run_id}.json", {
        "runId": run_id,
        "workflowName": meta["name"],
        "args": args,
        "task": serialize_task(task),
    })
    _save_last_run(run_id)
    task.event("task_notification", status=task.status,
               agents=task.usage["agents"], tokens=task.usage["tokens"],
               outputFile=f".runtime/{run_id}.output.json")
    return {"launched": launched, "result": result, "task": task}
```

async_launched / task_started 是内部开始事件；phase、agent、log 是本地进度。脚本结束时写输出与快照，打印 task_notification，再返回 launched / result / task。progress 列表会随最终 task 返回；中间推理、审计变量没有逐步进入主消息历史。

此处 events 主要打印到终端，不是 S15 的后台通知队列或真实 SDK 事件流。脚本异常会记录 failed 和 error 结果，再完成收尾；这与主模型 API 的通用恢复是不同层，本章不展开 S15 Error Recovery。

### 4.6 串回主循环与离线观察 {#workflow-loop}

下面是**结构伪代码**，省略校验、锁与持久化细节；没有改变 S15 的普通模型／工具循环：

```python
host = load_integrated_host()
install_workflow_tool(host)
# host.agent_loop keeps choosing and dispatching ordinary tools

# When it dispatches Workflow, the sync bridge waits for:
meta, script = WORKFLOWS[name]
with workflow_run_lock(run_id):
    journal = load_or_create_journal(run_id)
    ctx = build_execution_state(journal, runner, args)
    result = await script(ctx, args)  # parallel steps may happen inside
    persist_output_and_snapshot(result)
    return launched_result_and_task(result)
# The parent loop now runs PostToolUse and appends one paired tool_result.
```

真实入口 run_cli 安装 runner 工厂后使用宿主 API；demo / resume 默认使用 MockAgentRunner，不需要 API key。demo 与 resume 是一组观察命令，续跑默认沿用固定演示参数；若 last_run 来自不同实际输入，不能假设它会接受这份演示 args。

```sh
python s16_workflow_runtime/code.py demo
python s16_workflow_runtime/code.py resume
```

真实 CLI 还需 S15 的 anthropic、python-dotenv、PyYAML 与模型环境配置。本文验证用临时目录和 mock，不向真实课程目录写运行产物。

我的理解是：**模型负责一次局部判断，可信脚本负责重复的编排，journal 负责调用结果复用；它们通过一个 Workflow 工具边界接回原循环。**
