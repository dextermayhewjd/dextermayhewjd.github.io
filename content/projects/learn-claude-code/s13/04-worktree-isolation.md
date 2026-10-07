---
title: "S13.4 Worktree Isolation：用独立工作目录隔离改动"
weight: 40
ShowToc: false
compactDiagramLegends: true
hideMeta: true
ShowPostNavLinks: false
aliases: ["/projects/learn-claude-code/s18/"]
---

{{< chapter-outline id="s13-worktree-outline" title="本节目录" >}}

独立 Agent 上下文隔离了推理历史；**可选 worktree 再把不同任务的文件修改放到不同 Git 工作目录。**

[返回 S13 总览与三图对照](../#team-architecture)。源码基准为本地 `ce8f9f1` 的 [s13_agent_teams/code.py](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s13_agent_teams/code.py)。代码按真实函数摘录，类方法保留 `self`；本页片段用于分步阅读，不是可独立运行的完整程序。按 [MIT 许可](/examples/s13-repo/NOTICE.txt)使用。


## 1. Worktree 属于任务，不是另一个 Agent {#worktree-position}

### 1.1 目录、分支与任务之间的关系 {#worktree-layout}

```text
workspace/
  .tasks/task_1234abcd.json
  .worktrees/config/
  .mailboxes/config.jsonl
```

`create_worktree("config", task_id)` 创建 `wt/config` 分支和 `.worktrees/config` 工作树，再保存 Task.worktree="config"。claim_task 将目录绑定给 owner 的 assignment，文件与 Shell 工具每次解析该 cwd。

### 1.2 正确的调用顺序 {#worktree-order}

必须在任务 **pending、未认领、未绑定其他 worktree** 时创建。需要隔离就先建目录再 spawn；spawn(task_id=...) 会先认领，认领后已不满足创建条件。

```python
# 教学源码函数的调用示意；检查成功返回后才继续
job = create_task("重构配置加载")
result = create_worktree("config", job.id)
# 确认 result 表示创建和绑定成功，再启动队友
spawn_teammate_thread("config", "配置开发", "完成任务并报告", task_id=job.id)
```

没有绑定 worktree 的任务仍用 WORKDIR；无任务的队友不能使用工作区工具。目录隔离是可选的，不是 spawn 的默认效果。

### 1.3 从任务绑定到工具 cwd 的局部流程 {#worktree-diagram}

{{< architecture from="/projects/learn-claude-code/s13" width="1000" src="images/team-worktree.svg" legend="evolution" label="创建并绑定任务，认领保存 assignment，工具解析 cwd，回合结束后才可清理" caption="worktree 改变默认工作目录；文件路径检查和 Shell 能力各有不同边界。移除目录不会自动删除分支或合并改动。 点击函数名定位下方代码。" >}}


## 2. 创建、解析与具体工具入口 {#worktree-functions}

### 2.1 create_worktree：验证后创建，再绑定 {#worktree-create}

**所属层：** Harness 内部 Git／任务绑定逻辑。验证名称、任务状态、重复绑定、目录、仓库根目录、分支名称与 Git 注册信息，运行 `git worktree add -b ... HEAD`，成功后保存 Task.worktree。

```python
def create_worktree(name: str, task_id: str) -> str:
    """Create and bind a dedicated worktree after all inputs validate."""
    error = validate_worktree_name(name)
    if error:
        return f"Error: {error}"
    try:
        path = _worktree_path(name)
        task_path = _task_path(task_id)
    except ValueError as exc:
        return f"Error: {exc}"
    branch = _worktree_branch(name)

    with task_lock:
        if not task_path.exists():
            return f"Error: Task {task_id} not found"
        task = load_task(task_id)
        if task.status != "pending" or task.owner is not None:
            return f"Error: Task {task_id} must be pending and unowned"
        if task.worktree:
            return f"Error: Task {task_id} already uses worktree '{task.worktree}'"
        if any(t.worktree == name for t in list_tasks() if t.id != task_id):
            return f"Error: Worktree '{name}' is already bound to another task"
        if path.exists():
            return f"Error: Worktree path already exists: {path}"

        ok, root = run_git(["rev-parse", "--show-toplevel"])
        if not ok or Path(root).resolve() != WORKDIR.resolve():
            return "Error: Working directory must be the root of a Git repository"
        ok, branch_check = run_git(["check-ref-format", "--branch", branch])
        if not ok:
            return f"Error: Invalid worktree branch '{branch}': {branch_check}"
        exists, _ = run_git(["show-ref", "--verify", "--quiet",
                             f"refs/heads/{branch}"])
        if exists:
            return f"Error: Branch '{branch}' already exists"
        entries, registry_error = _registered_worktrees()
        if registry_error:
            return f"Error: {registry_error}"
        if path in entries:
            return f"Error: Worktree path is already registered: {path}"

        WORKTREES_DIR.mkdir(parents=True, exist_ok=True)
        ok, result = run_git(["worktree", "add", "-b", branch,
                              str(path), "HEAD"])
        if not ok:
            entries, registry_error = _registered_worktrees()
            branch_exists, _ = run_git(
                ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"]
            )
            artifacts = []
            if path.exists():
                artifacts.append(f"checkout path '{path}'")
            if registry_error is None and path in entries:
                artifacts.append("registered Git worktree")
            if branch_exists:
                artifacts.append(f"branch '{branch}'")
            if artifacts:
                return (
                    "Partial operation: git worktree add reported an error "
                    f"after leaving {', '.join(artifacts)}. Task {task_id} "
                    "remains unbound and no Git data was deleted. Run "
                    f"`git worktree list`, inspect '{path}' and '{branch}', "
                    "then keep or remove those artifacts manually after "
                    f"preserving any work. Git error: {result}"
                )
            return f"Git error: {result}"

        try:
            task.worktree = name
            save_task(task)
        except Exception as exc:
            return (f"Partial success: Worktree '{name}' was created at "
                    f"{path} on branch '{branch}', but task binding failed: "
                    f"{exc}. Git data was retained for manual recovery.")

    print(f"  \033[33m[worktree] created: {name} at {path}\033[0m")
    return f"Worktree '{name}' created at {path} for task {task_id}"
```

Git 创建与 JSON 绑定不是一个事务。Git 返回错误但已留下部分目录／分支，或者目录创建成功但保存绑定失败时，函数报告部分成功并保留数据，要求人工检查；不会自动删掉可能已有工作的目录。

### 2.2 task_worktree_cwd：校验绑定仍真实有效 {#worktree-resolve}

**输入：** Task。**输出：** cwd 和可选错误。检查路径仍在 .worktrees、Git 注册中存在、目录存在、分支与预期 `wt/<name>` 一致。

```python
def _registered_worktree(name: str) -> tuple[Path | None, str | None]:
    try:
        path = _worktree_path(name)
    except ValueError as exc:
        return None, str(exc)
    entries, error = _registered_worktrees()
    if error:
        return None, error
    if path not in entries:
        return None, f"worktree '{name}' is not registered with Git"
    if not path.is_dir():
        return None, f"worktree '{name}' is missing at {path}"
    expected_branch = f"refs/heads/{_worktree_branch(name)}"
    if entries[path].get("branch") != expected_branch:
        return None, (f"worktree '{name}' is not registered on expected "
                      f"branch '{_worktree_branch(name)}'")
    return path, None
```

```python
def task_worktree_cwd(task: Task) -> tuple[Path, str | None]:
    """Resolve a task cwd, failing closed for broken worktree bindings."""
    if not task.worktree:
        return WORKDIR, None
    path, error = _registered_worktree(task.worktree)
    return (path or WORKDIR), error
```

`_registered_worktrees` 用 `git worktree list --porcelain` 的机器格式读取完整注册信息，不能从截断的展示字符串推断目录。解析失败不会把该绑定当成普通任务。

### 2.3 assignment_cwd：归属与目录必须一致 {#worktree-assignment}

**所属层：** assignment 内部解析。必要时从持久任务 owner / worktree 恢复 cwd；已有归属时重新核对状态、owner 与目录一致，失效就抛错。

```python
def assignment_cwd(owner: str) -> Path:
    with task_lock:
        assignment = teammate_assignments.get(owner)
        task = _owner_in_progress(owner)
        if task and (not assignment or assignment.get("task_id") != task.id):
            cwd, error = task_worktree_cwd(task)
            if error:
                raise ValueError(error)
            assignment = {"task_id": task.id, "cwd": cwd}
            teammate_assignments[owner] = assignment
        elif not assignment:
            return WORKDIR
        task = load_task(str(assignment["task_id"]))
        if task.status not in {"in_progress", "completed"} or task.owner != owner:
            raise ValueError(f"Assignment for {owner} is no longer active")
        cwd, error = task_worktree_cwd(task)
        if error:
            raise ValueError(error)
        if cwd.resolve() != Path(assignment["cwd"]).resolve():
            raise ValueError(f"Assignment cwd changed for task {task.id}")
        return cwd
```

completed 任务暂时仍允许这轮后续工具使用原 cwd；回合结束后 release_completed_assignment 才移除租约。重启后可恢复正在进行的任务目录，不代表旧队友的 messages 或全部协议状态自动恢复。

### 2.4 队友文件工具是具体包装，不是全局 chdir {#worktree-tool}

**所属层：** TeammateRuntime 的具体工具入口。current_cwd 先要求队友已认领任务；write 将解析到的 cwd 显式传给基础实现。

```python
def current_cwd(self) -> tuple[Path | None, str | None]:
    if self.name not in teammate_assignments:
        return None, "Error: Claim a Task before using workspace tools."
    try:
        return assignment_cwd(self.name), None
    except (FileNotFoundError, ValueError) as exc:
        return None, f"Error: Invalid task assignment: {exc}"
```

```python
def write(self, path: str, content: str) -> str:
    cwd, error = self.current_cwd()
    return error or run_write(path, content, cwd=cwd)
```

```python
def safe_path(p: str, cwd: Path | None = None) -> Path:
    base = (cwd or WORKDIR).resolve()
    path = (base / p).resolve()
    if not path.is_relative_to(base):
        raise ValueError(f"Path escapes workspace: {p}")
    return path
```

各线程使用参数 cwd，不共享进程级 os.chdir。`safe_path` 将文件路径 resolve 并限制在该任务 cwd 下，处理 `..` 和符号链接；Bash 使用工作目录启动 Shell，但命令仍可访问系统其他资源，**worktree 不是安全沙箱**。

## 3. 什么时候能移除 {#worktree-lifecycle}

### 3.1 remove_worktree 是宿主操作 {#worktree-remove}

此函数不在 Lead 或队友的 TOOLS / handlers 里。检查绑定任务都已 completed、没有活动 assignment 租约，再检查 `git status --porcelain --ignored`。有未提交、未跟踪或忽略文件时，默认拒绝；宿主明确传 discard_changes=True 才使用 --force。

```python
def remove_worktree(name: str, discard_changes: bool = False) -> str:
    """Remove a registered checkout while always retaining its branch."""
    error = validate_worktree_name(name)
    if error:
        return f"Error: {error}"

    with task_lock:
        path, error = _registered_worktree(name)
        if error:
            return f"Error: {error}"
        bound = [task for task in list_tasks() if task.worktree == name]
        if not bound:
            return f"Error: Worktree '{name}' is not bound to a task"
        active = [task for task in bound if task.status != "completed"]
        if active:
            return (f"Error: Worktree '{name}' is bound to active task "
                    f"{active[0].id}; complete it before removal")
        leased = [owner for owner, assignment in teammate_assignments.items()
                  if Path(assignment["cwd"]).resolve() == path.resolve()]
        if leased:
            return (f"Error: Worktree '{name}' is still in use by "
                    f"{', '.join(sorted(leased))}; wait for the turn to end")
        ok, status = run_git(
            ["status", "--porcelain", "--ignored"], cwd=path
        )
        if not ok:
            return f"Error: Cannot verify worktree '{name}' status: {status}"
        if status != "(no output)" and not discard_changes:
            changed = len([line for line in status.splitlines() if line.strip()])
            return (f"Error: Worktree '{name}' has {changed} uncommitted "
                    "change(s); preserve or discard them manually")

        args = ["worktree", "remove"]
        if discard_changes:
            args.append("--force")
        args.append(str(path))
        ok, result = run_git(args)
        if not ok:
            return f"Git error: {result}"

        try:
            for task in bound:
                task.worktree = None
                save_task(task)
        except Exception as exc:
            return (f"Partial success: Worktree '{name}' was removed and "
                    f"branch '{_worktree_branch(name)}' retained, but task "
                    f"unbinding failed: {exc}. Manual recovery is required.")

    print(f"  [worktree] removed: {name}; branch retained")
    return f"Worktree '{name}' removed; branch '{_worktree_branch(name)}' retained"
```

移除 checkout 后解除任务绑定，但始终保留 `wt/<name>` 分支；不自动合并、不删除分支。若移除成功但解绑保存失败，会报告部分成功以便恢复。

### 3.2 完成任务、结束回合、清理目录是三件事 {#worktree-summary}

| 时刻 | 变化 |
|---|---|
| complete_task | 任务写 completed，原目录租约仍在 |
| 模型回合结束 | release_completed_assignment 清理租约 |
| 宿主移除 worktree | 确认无活动归属与未保留数据后移除 checkout，分支保留 |

不同工作目录减少同一文件上的即时修改冲突，但最终分支合并仍需处理冲突和测试；目录隔离也不隔离共享端口、数据库、系统资源或费用。
