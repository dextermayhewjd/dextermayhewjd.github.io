---
title: "S13.2 Team Protocols：用结构化请求协调行动"
weight: 20
ShowToc: false
compactDiagramLegends: true
hideMeta: true
ShowPostNavLinks: false
---

{{< chapter-outline id="s13-protocol-outline" title="本节目录" >}}

普通消息只表达意思；**协作协议还要匹配请求、改变状态，并限制实际执行。**

[返回 S13 总览与三图对照](../#team-architecture)。源码基准为本地 `ce8f9f1` 的 [s13_agent_teams/code.py](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s13_agent_teams/code.py)。代码按真实函数摘录，类方法保留 `self`；本页片段用于分步阅读，不是可独立运行的完整程序。按 [MIT 许可](/examples/s13-repo/NOTICE.txt)使用。


## 1. 协议不是把“批准了”写进聊天 {#protocol-position}

### 1.1 request_id 与执行闸门 {#protocol-state}

`ProtocolState` 保存 request_id、type、sender、target、status、payload，并可记录 work_version / task_id。`pending_requests` 是本进程内字典；不会自动存入 `.tasks`。

| 状态容器 | 解决的问题 |
|---|---|
| pending_requests | 哪个请求由谁向谁发出，是否已处理 |
| plan_request_ids[name] | 该队友当前等待的计划是哪一份 |
| plan_gates[name] | required / pending / approved / rejected / not_required |
| assignment_versions[name] | 请求是否还属于当前工作归属 |

required 要求先提交；pending 等待审核；rejected 必须修改后重新提交；approved 或 not_required 才放行修改型工具。

### 1.2 计划协议的局部流程 {#protocol-diagram}

{{< architecture from="/projects/learn-claude-code/s13" width="1000" src="images/team-protocol.svg" legend="evolution" label="提交计划，Lead 审查，队友校验回复后开放工具执行" caption="上方走一次计划审批，下方是 Harness 对实际工具调用的闸门；消息匹配和权限检查都不能省略。 点击函数名定位下方代码。" >}}


## 2. 计划：请求、审批、应用分别由谁做 {#protocol-plan}

### 2.1 队友提交时保存当前工作身份 {#protocol-submit}

**所属层：** 队友 submit_plan 工具调用的内部实现。输入 plan，生成 request_id，保存工作版本与任务 ID，把闸门设为 pending，并向 Lead 投递 plan_approval_request；已有 pending 则拒绝重复提交。

```python
def current_work_identity(owner: str) -> tuple[int, str | None]:
    with task_lock:
        assignment = teammate_assignments.get(owner)
        task_id = str(assignment["task_id"]) if assignment else None
        return assignment_versions.get(owner, 0), task_id
```

```python
def _teammate_submit_plan(from_name: str, plan: str) -> str:
    with task_lock:
        assignment = teammate_assignments.get(from_name)
        task_id = str(assignment["task_id"]) if assignment else None
        work_version = assignment_versions.get(from_name, 0)
        with team_lock:
            if plan_gates.get(from_name) == "pending":
                return "A plan is already waiting for review."
            request_id = new_request_id()
            pending_requests[request_id] = ProtocolState(
                request_id=request_id,
                type="plan_approval",
                sender=from_name,
                target="lead",
                status="pending",
                payload=plan,
                work_version=work_version,
                task_id=task_id,
            )
            plan_gates[from_name] = "pending"
            plan_request_ids[from_name] = request_id
            active_teammates[from_name] = "waiting_approval"
    BUS.send(from_name, "lead", plan, "plan_approval_request",
             {"request_id": request_id})
    return f"Plan submitted ({request_id}). Wait for Lead's decision."
```

### 2.2 Lead review_plan 处理请求 {#protocol-review}

**所属层：** Lead 具体工具入口，内部直接完成状态校验和修改。输入 request_id、approve、feedback；检查请求仍 pending、任务与版本仍一致、仍是当前计划。更新请求状态后发送 plan_approval_response。

```python
def run_review_plan(request_id: str, approve: bool,
                    feedback: str = "") -> str:
    state = pending_requests.get(request_id)
    if not state:
        return f"Request {request_id} not found"
    work_version, task_id = current_work_identity(state.sender)
    with team_lock:
        state = pending_requests.get(request_id)
        if not state:
            return f"Request {request_id} not found"
        if state.type != "plan_approval":
            return f"Request {request_id} is not a plan"
        if state.status != "pending":
            return f"Request {request_id} already {state.status}"
        if (state.work_version != work_version or state.task_id != task_id):
            return f"Request {request_id} belongs to an earlier assignment"
        if plan_request_ids.get(state.sender) != request_id:
            return f"Request {request_id} is not the current plan"
        state.status = "approved" if approve else "rejected"
    content = feedback or ("Plan approved." if approve
                           else "Revise the plan and submit it again.")
    BUS.send("lead", state.sender, content, "plan_approval_response",
             {"request_id": request_id, "approve": approve})
    return f"Plan {state.status} ({request_id})"
```

这里不是任意输入名字然后“放行这个队友”；批准对应的是一份具体计划。原计划已处理或属于之前的任务时会拒绝。

### 2.3 队友校验回复才更新本地闸门 {#protocol-apply}

**所属层：** 收信时的内部协议处理。除了 request_id，还核对 from / to、请求类型、发送双方、任务与版本，以及 metadata.approve 与保存状态是否一致。

```python
def apply_plan_response(name: str, msg: dict) -> tuple[bool, str]:
    """Apply only the Lead response for this teammate's current plan."""
    metadata = msg.get("metadata", {})
    request_id = metadata.get("request_id", "")
    work_version, task_id = current_work_identity(name)
    with team_lock:
        state = pending_requests.get(request_id)
        expected_id = plan_request_ids.get(name)
        valid = (
            msg.get("from") == "lead"
            and msg.get("to") == name
            and request_id == expected_id
            and state is not None
            and state.type == "plan_approval"
            and state.sender == name
            and state.target == "lead"
            and state.work_version == work_version
            and state.task_id == task_id
            and state.status in {"approved", "rejected"}
            and metadata.get("approve", False)
            == (state.status == "approved")
        )
        if not valid:
            return False, "[Ignored plan response: request mismatch]"
        plan_gates[name] = state.status
        active_teammates[name] = "working"
        plan_request_ids.pop(name, None)
        outcome = state.status
    return True, f"[Plan {outcome}] {msg['content']}"
```

换任务或释放归属会推进版本，旧审批不能给新任务授权。源码的版本更新还会清理当前 plan_request_id，并在仍要求审批时恢复 required：

```python
def advance_assignment_version(owner: str):
    """Invalidate old approvals without clearing an explicit plan requirement."""
    with task_lock:
        assignment_versions[owner] = assignment_versions.get(owner, 0) + 1
        gates = globals().get("plan_gates")
        request_ids = globals().get("plan_request_ids")
        team = globals().get("team_lock")
        if team is not None:
            team.acquire()
        try:
            if (isinstance(gates, dict) and owner in gates
                    and gates[owner] != "not_required"):
                gates[owner] = "required"
            if isinstance(request_ids, dict):
                request_ids.pop(owner, None)
        finally:
            if team is not None:
                team.release()
```

### 2.4 真正限制执行的位置 {#protocol-gate}

主章的 [_run_teammate_tool](../#team-gate) 在调用 handler 前检查闸门：Bash、write_file、edit_file 必须 approved 或 not_required。读／glob 可用于准备计划，但仍须有效 assignment；`complete_task` 也拒绝 required、pending、rejected 的任务完成请求。

`check_permission(block, prompt_user=False)` 是另一道边界。以下是**源码原函数**，不是所有 Bash 都要用户确认：deny list 直接拒绝，源码判定的破坏性命令或越界路径要求确认；队友非交互执行时返回需要 Lead 处理的说明。

```python
def check_permission(block, prompt_user: bool = True) -> str | None:
    if block.name == "bash":
        command = block.input.get("command", "")
        for pattern in DENY_LIST:
            if pattern in command:
                return f"Permission denied by deny list: {pattern}"
        if contains_destructive_command(command) or any(
            keyword in command for keyword in DESTRUCTIVE
        ):
            if not prompt_user:
                return "Permission required: ask Lead to run this command."
            print(f"\n[permission] {block.name}({block.input})")
            if input("Allow? [y/N] ").strip().lower() not in {"y", "yes"}:
                return "Permission denied by user"

    if block.name in {"read_file", "write_file", "edit_file"}:
        raw_path = block.input.get("path", "")
        if not (WORKDIR / raw_path).resolve().is_relative_to(WORKDIR.resolve()):
            if not prompt_user:
                return "Permission required: path is outside the workspace."
            print(f"\n[permission] {block.name}({block.input})")
            if input("Allow? [y/N] ").strip().lower() not in {"y", "yes"}:
                return "Permission denied by user"
    return None
```

`require_plan=True` 在启动线程前就设置 required，避免队友先执行再补审批。Lead 自己提出团队并等待用户确认，是 SYSTEM 的策略约定；当前源码没有同样的硬编码团队启动审批闸门。

## 3. 关机：另一条请求与响应协议 {#protocol-shutdown}

### 3.1 Lead 请求，队友在收信边界确认 {#protocol-stop-request}

**所属层：** Lead request_shutdown 工具入口。登记 pending 的 shutdown 请求，向目标队友投递 shutdown_request。

```python
def run_request_shutdown(teammate: str) -> str:
    if teammate not in active_teammates:
        return f"Teammate '{teammate}' is not active"
    with team_lock:
        request_id = new_request_id()
        pending_requests[request_id] = ProtocolState(
            request_id=request_id,
            type="shutdown",
            sender="lead",
            target=teammate,
            status="pending",
            payload="",
        )
    BUS.send("lead", teammate, "Finish the current step and shut down.",
             "shutdown_request", {"request_id": request_id})
    return f"Shutdown requested from {teammate} ({request_id})"
```

队友只接受来自 Lead、发给自己、匹配一个 pending shutdown 请求的消息。校验通过后标记 stopping；handle_inbox 发 shutdown_response 并返回停止信号。

```python
def apply_shutdown_request(name: str, msg: dict) -> tuple[bool, str]:
    """Accept only a pending shutdown request sent by Lead to this teammate."""
    request_id = msg.get("metadata", {}).get("request_id", "")
    with team_lock:
        state = pending_requests.get(request_id)
        valid = (
            msg.get("from") == "lead"
            and msg.get("to") == name
            and state is not None
            and state.type == "shutdown"
            and state.sender == "lead"
            and state.target == name
            and state.status == "pending"
            and active_teammates.get(name) != "stopping"
        )
        if not valid:
            return False, "[Ignored shutdown request: request mismatch]"
        active_teammates[name] = "stopping"
    return True, request_id
```

这会等当前模型请求／工具批次走到收信边界，不会立即杀死正在运行的 Bash。线程 finally 释放未完成任务并清理注册；输入 q 退出主进程则是 daemon 线程退出的另一条边界，CLI 没有自动逐个请求关机并 join。

### 3.2 Lead 消费响应并结束请求状态 {#protocol-stop-response}

**所属层：** 内部请求匹配。检查响应类型、请求 ID、反向 sender / target 和 pending 状态，成功后写 approved / rejected。消费位置在 consume_lead_inbox。

```python
def match_response(response_type: str, request_id: str, approve: bool,
                   from_agent: str, to_agent: str) -> bool:
    """Match one protocol response to one pending request."""
    with team_lock:
        state = pending_requests.get(request_id)
        if not state:
            print(f"  [protocol] unknown request_id: {request_id}")
            return False
        expected = {
            "shutdown": "shutdown_response",
            "plan_approval": "plan_approval_response",
        }[state.type]
        if response_type != expected:
            print(f"  [protocol] expected {expected}, got {response_type}")
            return False
        if from_agent != state.target or to_agent != state.sender:
            print(f"  [protocol] {request_id} responder mismatch")
            return False
        if state.status != "pending":
            print(f"  [protocol] {request_id} already {state.status}")
            return False
        state.status = "approved" if approve else "rejected"
    print(f"  [protocol] {request_id} -> {state.status}")
    return True
```

计划与关机的状态写入路径不同：计划由 Lead 的 review_plan 先改状态，再发给队友应用；关机由队友回响应，再由 Lead 消费时 match_response 改状态。不能把两条路径都理解成“收件箱里看见 approve 就通过”。
