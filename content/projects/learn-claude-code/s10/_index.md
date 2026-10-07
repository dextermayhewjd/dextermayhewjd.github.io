---
title: "S10 Task System：持久化任务并管理依赖"
weight: 100
summary: "先创建任务取得真实 ID，再添加依赖，查看、认领并记录完成结果，接回原来的工具循环。"
ShowToc: false
compactDiagramLegends: true
---

{{< chapter-outline id="s10-chapter-outline" title="S10 本章目录" >}}

目录按“系统位置 → 任务记录与依赖 → 认领与完成 → 接回循环”分层。编号与正文标题一致，点击即可跳转。

## 1. 定位：任务系统接在哪里 {#task-position}



### 1.1 要解决什么问题 {#task-question}

一个目标需要搭数据库、写 API、补测试和文档时，除了列出步骤，还需要知道：哪些已经完成，哪些正在做，哪些必须等前面的任务完成？换一个会话后，又怎样继续这些工作？

我的理解是：**Task System 把目标拆成有独立 ID、描述、状态和依赖的工作项，让 Agent 查看剩余工作，认领当前可做的任务，再记录完成结果。**

`description` 可以写目标、实现提示和完成标准，但任务记录本身不会执行实现步骤。真正修改代码、运行命令与验证结果，仍由模型通过工作工具完成。

本篇已从旧版博客 S12 迁到新版 S10，按更新后的本地 `s10_task_system/code.py` 重核代码。源码基准为 [ce8f9f1](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s10_task_system/code.py)。函数摘录保留实际行为，方法块属于 `TaskStore`；导入、客户端初始化与其他包装见原文件，伪代码另外注明。源码按 [MIT 许可](/examples/s10-repo/NOTICE.txt)使用。

### 1.2 与 TodoWrite、Memory、Compact 的区别 {#task-comparison}

| 机制 | 当前新版保存什么 | 主要用途 |
|------|------------------|----------|
| S05 TodoWrite | `TodoManager` 中的步骤与状态 | 对照当前任务的执行清单 |
| S10 Task System | 每项任务的 ID、描述、状态、负责人和依赖 | 判断剩余工作及可开始的任务 |
| S09 Memory | 值得以后复用的偏好、反馈和背景 | 跨会话保留重要信息 |
| S08 Compact | 继续当前任务需要的对话摘要 | 减少活跃上下文占用 |

旧版 S05 曾把清单写入 `.tasks/current_todos.json`，已有笔记仍记录那份原型；新版 S05 使用进程内 `TodoManager`。本节按新版比较：任务系统增加的是独立记录、依赖和认领契约，不能只看名称或状态枚举判断两者相同。

### 1.3 整体过程：从 S09 到 S10 {#task-architecture}

#### 先分清：模型说明、工具入口与内部实现 {#task-function-layers}

模型提出工具调用，Harness 接住调用并运行本地代码。本章读代码时，可以先按下面五类定位：

| 所属层 | 本章例子 | 负责什么 | 是否发送给模型 |
|---|---|---|---|
| 工具说明 | `TOOLS` 中的 `name`、`description`、`input_schema` | 告诉模型可调用什么、参数怎样填写 | 是，作为模型请求的 `tools` 参数 |
| Harness 统一执行入口 | `execute_tool`、`TOOL_HANDLERS` | 执行前检查，按工具名找到入口函数，执行后回传结果 | 留在本地 |
| 某个工具的执行入口 | `run_create_task`、`run_list_tasks` 等 `run_*` | 接收工具参数，调用内部逻辑，准备工具回复 | 留在本地，由分发表调用 |
| Harness 内部任务逻辑 | `create_task`、`claim_task`、`load_task` 等 | 创建、检查状态与依赖，或提供读取包装 | 留在本地，供其他函数调用 |
| Harness 内部存储实现 | `TaskStore.create/load/save/list` 等方法 | 分配 ID、校验记录、读写任务文件 | 留在本地 |

**`TOOLS` 里注册的是工具说明，不是 Python 函数对象或源码。** 模型会请求名字为 `create_task` 的工具；Harness 根据 `TOOL_HANDLERS["create_task"]` 找到 `run_create_task`，再由它调用内部 `create_task`。工具名与某个内部函数同名，不意味着程序会自动调用那个函数。

`run_` 在这里是命名惯例；一个函数是否是工具入口，要看它是否被绑定到 `TOOL_HANDLERS`。入口函数也不一定都做结果转换：`run_create_task` 把对象转成字符串，`run_claim_task` 则固定 owner 后转交内部函数，直接返回已有字符串。

#### 图 1：回顾 S09 的默认总览

{{< architecture from="/projects/learn-claude-code/s09" width="1200" src="images/memory-agent-integration.svg" mode="baseline" modified="tools,system,handler" folded="memory-extract,memory-save,memory-consolidate" label="图 1：保留 S09 原结构，标出任务工具注册和使用规则的改造位置" caption="图 1：沿用 S09 的节点、位置与连线。橙色是本轮要扩展的工具定义、分发和使用约定；灰色虚线的记忆提取、保存、整理在图 2 合并为 S09 保存接口，入口、文件和退出保留。" >}}

这里不需要回到上一章找图：用户回合入口召回背景，原工具循环执行，退出前检查长期信息。本轮增加的是工具执行分支中的任务管理。

#### 图 2：任务层接进原来的工具回路

{{< architecture-explorer id="s10-task-explorer" modules="explorer.json" roles="function-roles.json" width="1200" src="images/task-agent-integration.svg" legend="evolution" label="图 2：任务操作通过已有 PreToolUse 和分发入口，检查和文件读写后接回 PostToolUse 与工具结果" caption="图 2：紫色展开任务工具和 TaskStore 检查，灰色保存任务文件。任务分支经过原执行前事件，操作结果或拒绝原因接回 PostToolUse 和 tool_result；回传循环仍在下方。Memory 的内部保存细节合并到带 S09 索引的接口，Compact 和 Skills 的已有接口保留。" >}}

**本轮插入点：`TOOLS` 注册六个 schema，`TOOL_HANDLERS` 增加六个 handler；handler 读写 `TaskStore`，再经原结果通道回到模型。** `SYSTEM` 只增加使用约定，任务正文不会自动全部放进去。

**比较范围：** 总图沿用已学骨架，解释机制的接入位置；独立 S10 脚本实际保留 S04 的五个基础工具、Permission 和 Hooks，没有实际复制 S05–S09 的全部组件。图中的旧接口是复习索引，不表示这些脚本已经累计合并。

悬停节点可以看输入、输出和引用的箭头；点击本章节点可对照局部图与函数。任务工具记录工作，Bash 与文件工具完成实际产物。单次权限拒绝会跳过 handler 和 PostToolUse，直接回传说明。

#### 图 3：一项任务的最小核心

{{< architecture figureId="s10-task-core" functionExplorer="s10-task-explorer" width="1000" src="images/task-core.svg" legend="evolution" label="图 3：创建、依赖、查看、认领、实际执行与完成，以及文件读写和拒绝分支" caption="图 3：只标出任务内部逻辑与 TaskStore 方法，点击函数名即可在附近查看对应代码。框间是典型操作顺序，拒绝分支不改记录；蓝色实际工作保留原工具执行环境。" >}}

图内只保留内部任务函数和存储方法。点击 `create_task()`、`TaskStore.load()` 等名称，会在附近打开实现并高亮所选函数，不必跳到文章后面找代码。辅助方法也可从下方索引点击查看；`run_*` 的工具入口绑定继续在 2.2、4.1–4.2 解释。

{{< task-function-index >}}

认领是 `pending → in_progress`，完成是 `in_progress → completed`。可开始的任务仍需模型决定去做；后续任务不会因为依赖满足而自行运行。

## 2. 任务记录与依赖：先建节点，再连关系 {#task-records}



### 2.1 一份任务与 TaskStore {#task-store}

```python
@dataclass
class Task:
    id: str
    subject: str
    description: str
    status: str
    owner: str | None
    blockedBy: list[str]
```

`subject` 是标题；`description` 交代目标、背景和完成标准；`status` 记录进度；`owner` 记录负责人；`blockedBy` 保存前置任务 ID。

每项任务单独保存为 `.tasks/{id}.json`。`TaskStore` 负责路径、记录和依赖校验；`TASKS = TaskStore(TASKS_DIR)` 是本节使用的存储对象。

例如 API 任务文件可以包含：

```json
{
  "id": "task_e5f6a7b8",
  "subject": "实现 API",
  "description": "实现接口并验证数据读写",
  "status": "pending",
  "owner": null,
  "blockedBy": ["task_a1b2c3d4"]
}
```

这里的 ID 只是示意。实际连依赖时必须用工具返回的 ID；`blockedBy` 保存的是前置任务的 ID，是否仍受阻塞要再读取那些任务的状态。

这里的五个函数都属于 **Harness 内部实现**：前三个是 `TaskStore` 存储方法，后两个是使用同一个 `TASKS` 对象的内部读取包装。它们没有各自维护一份任务表。模型工具的执行入口由 `TOOL_HANDLERS` 绑定到 `run_*`，见 [4.1](#task-registration)。

2.1 内部导航：

- [2.1.1 `TaskStore.save`：保存任务对象](#task-store-save)
- [2.1.2 `TaskStore.load`：按 ID 读取一项任务](#task-store-load)
- [2.1.3 `TaskStore.list`：读取全部任务记录](#task-store-list)
- [2.1.4 `load_task`：单项读取的内部包装](#task-load-wrapper)
- [2.1.5 `list_tasks`：全部读取的内部包装](#task-list-wrapper)

#### 2.1.1 `TaskStore.save`：保存任务对象 {#task-store-save}

**所属层：** Harness 内部存储方法。

**作用：** 把内存里的 `Task` 对象写入对应 JSON 文件。认领、完成或修改依赖后，调用它才能把变化保存下来。

**输入／输出：** 输入完整的 `Task`，写入 `.tasks/{task.id}.json`；返回 `None`，会修改磁盘文件。

```python
def save(self, task: Task) -> None:
        self._path(task.id, create_root=True).write_text(
            json.dumps(asdict(task), indent=2),
            encoding="utf-8",
        )
```

它使用对象已有的 ID，不生成新 ID，也不推断依赖。是否允许认领或完成，由上层操作先检查；这里负责保存记录。

#### 2.1.2 `TaskStore.load`：按 ID 读取一项任务 {#task-store-load}

**所属层：** Harness 内部存储方法。

**作用：** 找到任务文件，把 JSON 还原为 `Task`，并检查文件内 ID 是否匹配、状态是否有效。

**输入／输出：** 输入任务 ID，返回一个 `Task` 对象；只读文件，不认领任务，也不改变状态。

```python
def load(self, task_id: str) -> Task:
        data = json.loads(self._path(task_id).read_text(encoding="utf-8"))
        task = Task(**data)
        if task.id != task_id:
            raise ValueError(f"Task file ID does not match {task_id}")
        if task.status not in ("pending", "in_progress", "completed"):
            raise ValueError(f"Invalid task status: {task.status}")
        return task
```

返回的是本次读出的对象。修改它的 `status` 或 `blockedBy` 不会自动更新文件，还需要调用 `save`；读取或校验失败则抛出异常，由执行入口返回错误说明。

#### 2.1.3 `TaskStore.list`：读取全部任务记录 {#task-store-list}

**所属层：** Harness 内部存储方法。

**作用：** 扫描任务目录中的 `task_*.json`，逐项调用 `load`，收集所有任务记录。

**输入／输出：** 不需要传入任务 ID，返回 `list[Task]`；目录不存在时返回空列表，不创建目录。

```python
def list(self) -> list[Task]:
        if not self.directory.exists():
            return []
        root = self._root()
        return [self.load(path.stem)
                for path in sorted(root.glob("task_*.json"))]
```

它列出各种状态的任务，不自动筛选“可认领任务”。文件按名称排序，也不是按依赖关系安排执行顺序；是否可开始还要检查状态和前置任务。

#### 2.1.4 `load_task`：单项读取的内部包装 {#task-load-wrapper}

**所属层：** Harness 内部读取包装，供依赖检查、认领等 Python 函数调用。

**作用：** 让其他函数通过 `load_task(task_id)` 使用本节统一的存储对象，内部直接转交给 `TASKS.load`。

**输入／输出：** 输入任务 ID，返回同一个读取结果 `Task`；没有额外存储或状态更新。

```python
def load_task(task_id: str) -> Task:
    return TASKS.load(task_id)
```

例如依赖检查、认领和完成函数都通过它取得当前记录。ID 和状态的校验仍由 `TaskStore.load` 完成。

#### 2.1.5 `list_tasks`：全部读取的内部包装 {#task-list-wrapper}

**所属层：** Harness 内部读取包装。模型请求 `list_tasks` 工具时，分发表先调用的是 `run_list_tasks`。

**作用：** 让其他函数通过 `list_tasks()` 读取全部任务，内部直接调用 `TASKS.list`。

**输入／输出：** 不需要参数，返回 `list[Task]`；这是只读操作，不开始或完成任何任务。

```python
def list_tasks() -> list[Task]:
    return TASKS.list()
```

完成函数用这份列表比较完成前后的可开始任务。模型收到的列表文本则由工具包装 `run_list_tasks` 格式化；这里返回的是 Python 任务对象列表。

所以，这五个入口可以概括为：**保存一项、读取一项、读取全部，以及两个复用读取能力的包装函数。** 存储方法复用 `_path` 校验 ID 和路径；创建用排他写入，普通保存直接写文件，本章没有跨进程锁。创建与依赖更新的实现分别在 2.2、2.3 展开。

### 2.2 创建任务，取得真实 ID {#task-tools}

这一次创建涉及三个函数。先认清调用方向：

```text
tool_use(name="create_task", input={...})
  -> execute_tool(block)
  -> TOOL_HANDLERS["create_task"]
  -> run_create_task(subject, description)
  -> create_task(subject, description)
  -> TASKS.create(subject, description)
```

上面是调用关系示意。工具请求来自模型，后续函数均在 Harness 本地运行。这里的 `TASKS` 是 `TaskStore` 实例。

2.2 内部导航：

- [2.2.1 `create_task`：内部创建包装](#task-create-helper)
- [2.2.2 `TaskStore.create`：实际分配 ID 并写文件](#task-create-storage)
- [2.2.3 `run_create_task`：创建工具的执行入口](#task-create-entry)

#### 2.2.1 `create_task`：内部创建包装 {#task-create-helper}

**所属层：** Harness 内部任务逻辑。输入标题和描述，转交给 `TASKS.create`，返回 Python `Task` 对象。

```python
def create_task(subject: str, description: str = "") -> Task:
    return TASKS.create(subject, description)
```

#### 2.2.2 `TaskStore.create`：实际分配 ID 并写文件 {#task-create-storage}

**所属层：** Harness 内部存储实现。检查标题非空，使用 `task_` 加八位随机十六进制字符分配 ID，并将初始状态设为 `pending`、owner 设为 `None`、依赖设为空列表；写入文件后返回 `Task`。

创建用排他写入；若随机 ID 已存在就重试。`TaskStore.create` 的完整方法如下：

```python
def create(self, subject: str, description: str = "") -> Task:
        subject = subject.strip()
        if not subject:
            raise ValueError("Task subject cannot be empty")

        self._root(create=True)
        for _ in range(100):
            task = Task(
                id=f"task_{secrets.token_hex(4)}",
                subject=subject,
                description=description,
                status="pending",
                owner=None,
                blockedBy=[],
            )
            try:
                with self._path(task.id, create_root=True).open(
                    "x", encoding="utf-8"
                ) as handle:
                    json.dump(asdict(task), handle, indent=2)
                return task
            except FileExistsError:
                continue
        raise RuntimeError("Could not allocate a unique task ID")
```

新版本的 `create_task` **不接收 `blockedBy`**。模型先拿到创建结果里的真实 ID，再进行下一步。

#### 2.2.3 `run_create_task`：创建工具的执行入口 {#task-create-entry}

**所属层：** `create_task` 工具在 Harness 中的执行入口。它接收工具参数，调用内部 `create_task`，把返回的 `Task` 对象整理成字符串；这个入口由 `TOOL_HANDLERS` 注册。

```python
def run_create_task(subject: str, description: str = "") -> str:
    task = create_task(subject, description)
    print(f"  [create] {task.subject}")
    return f"Created {task.id}: {task.subject}"
```

例如对象中的 `id` 是 `task_e5f6a7b8`、标题是 `实现 API`，入口返回 `Created task_e5f6a7b8: 实现 API`。`execute_tool` 接收这段字符串，Agent Loop 再按本次调用的 `block.id` 构造 `tool_result` 交给模型。任务 ID 和工具调用 ID 分别标识任务记录与这次调用。

### 2.3 用真实 ID 添加依赖 {#task-dependencies}

**所属层：** `update_task` 是 Harness 内部的依赖更新包装；模型的 `update_task` 工具由 `run_update_task` 接收，再调用这里的函数。

```python
def update_task(task_id: str, addBlockedBy: list[str]) -> Task:
    return TASKS.update_dependencies(task_id, addBlockedBy)
```

为什么分两步？模型在一条响应中提出多个工具调用时，这些参数在任何工具结果返回前就已经确定。它不能提前知道另一个 `create_task` 将生成哪个随机 ID。

所以先创建所有节点，收到结果，再用真实 ID 添加边。`update_dependencies` 在保存前检查：

- 目标任务存在，且仍为 `pending`、没有 owner。
- 新增依赖是 ID 列表，每个依赖都存在。
- 没有自依赖，也不会产生循环依赖。
- 重复依赖不重复追加。

整次新增依赖先校验，再统一修改和保存。下面两个方法属于 Harness 内部的 `TaskStore`：`update_dependencies` 负责校验并保存新增依赖，`_depends_on` 是它用于判断间接依赖的内部辅助方法。

```python
def update_dependencies(self, task_id: str,
                            add_blocked_by: list[str]) -> Task:
        if not isinstance(add_blocked_by, list):
            raise ValueError("addBlockedBy must be a list of task IDs")

        task = self.load(task_id)
        if task.status != "pending" or task.owner is not None:
            raise ValueError(
                f"Task {task_id} dependencies can only be updated while "
                "pending and unowned"
            )

        dependencies = list(dict.fromkeys(add_blocked_by))
        for dependency in dependencies:
            if dependency == task_id:
                raise ValueError("Task cannot depend on itself")
            if not self.exists(dependency):
                raise ValueError(f"Dependency not found: {dependency}")
            if dependency not in task.blockedBy and self._depends_on(
                dependency, task_id
            ):
                raise ValueError(
                    f"Dependency cycle detected: {task_id} -> {dependency}"
                )

        task.blockedBy.extend(
            dependency for dependency in dependencies
            if dependency not in task.blockedBy
        )
        self.save(task)
        return task
```

```python
def _depends_on(self, task_id: str, target_id: str) -> bool:
        """Return whether task_id transitively depends on target_id."""
        pending = [task_id]
        visited = set()
        while pending:
            current = pending.pop()
            if current == target_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            pending.extend(self.load(current).blockedBy)
        return False
```

检测环问的是：新依赖是否已经间接依赖当前任务？已有 B 依赖 A 的链时，再让 A 依赖 B 就会形成环，因此拒绝。重复依赖去重；一次校验失败不会先写入其中一部分边。

#### 工具入口：`run_update_task` {#task-update-entry}

**所属层：** 具体工具入口。调用内部 `update_task`，把返回对象中的 ID 与依赖整理为工具回复；具体依赖校验仍在 `TaskStore` 内部。

```python
def run_update_task(task_id: str, addBlockedBy: list[str]) -> str:
    task = update_task(task_id, addBlockedBy)
    dependencies = ", ".join(task.blockedBy) or "(none)"
    print(f"  [update] {task.subject} blockedBy: {dependencies}")
    return f"Updated {task.id} blockedBy: {dependencies}"
```

#### 依赖图示例

假设数据库结构已经完成，API 已被认领，文档尚未开始：

{{< architecture legend="status" src="images/task-dependencies.svg" label="数据库、API、测试、文档和部署的任务依赖示例" caption="箭头从前置任务指向后续任务，表示后者的 blockedBy 包含前者。文档可认领；测试要等 API，部署要等测试和文档都完成。" >}}

`deploy.blockedBy = [tests.id, docs.id]` 要求两个依赖都完成。依赖满足的任务不会自动开始，还需要认领并实际执行。

这张图也说明它可以是非线性的：schema 完成后，API 与文档都满足前置条件；部署处又把测试、文档两条路径汇合起来。箭头表达“先完成什么”，不规定唯一的执行次序。

#### 动态依赖与并行的边界

| 理解 | 本节的具体行为 |
|------|----------------|
| 一开始把所有依赖一步写好 | 先创建节点取得真实 ID，再调用 `update_task` 加边，可以分批完成 |
| 依赖可以动态补充 | 可以追加边，但目标必须仍为 pending、无人认领，并通过无环检查 |
| `update_task` 是任意修改任务 | 当前接口只添加依赖，没有删除依赖、重开任务等通用编辑操作 |
| 有两个任务可做，就会并行运行 | 它们在依赖上互不阻塞；S10 仍在 `for` 循环中顺序执行工具调用 |

一次模型响应可以提出多个 `tool_use`，但“多个调用组成一批”和“多个工作者同时执行”是两件事。后台执行在 S11、团队协作与并发认领在 S13、固定流程的并行编排在 S16 继续展开。

### 2.4 查看列表与任务详情 {#task-inspect}

**所属层：** 本节的 `list_tasks`、`get_task`、`can_start`、`incomplete_dependencies` 都是 Harness 内部函数。模型请求列表或详情工具时，入口分别是 `run_list_tasks`、`run_get_task`；依赖判断函数供认领和完成逻辑使用。

`list_tasks()` 扫描任务文件，`get_task()` 返回某项任务的完整 JSON：

```python
def get_task(task_id: str) -> str:
    return json.dumps(asdict(load_task(task_id)), indent=2)
```

列表回答“还有哪些工作”，详情回答“具体怎样做”。依赖检查则回答“前置条件满足了吗”：

```python
def can_start(task_id: str) -> bool:
    return not incomplete_dependencies(load_task(task_id))
```

```python
def incomplete_dependencies(task: Task) -> list[str]:
    incomplete = []
    for dependency in task.blockedBy:
        try:
            if load_task(dependency).status != "completed":
                incomplete.append(dependency)
        except (FileNotFoundError, ValueError):
            incomplete.append(dependency)
    return incomplete
```

`incomplete_dependencies` 将未完成、缺失或无效的依赖视为阻塞。它检查的是所有前置任务，不是其中一个完成就放行。

基于这些函数，可以查看未完成和可认领的工作：

```python
unfinished = [t for t in list_tasks() if t.status != "completed"]
available = [t for t in unfinished
             if t.status == "pending" and can_start(t.id)]
```

这段是查看示例，不是原循环自动运行的调度器。模型要调用列表和详情工具，状态才会通过工具结果进入对话。

#### 查询工具入口：`run_list_tasks` 与 `run_get_task` {#task-inspect-entries}

这两个函数在分发表中接收模型的列表、详情请求。`run_list_tasks` 将内部对象列表格式化为逐行摘要；`run_get_task` 直接返回 `get_task` 已生成的 JSON 文本。

```python
def run_list_tasks() -> str:
    tasks = list_tasks()
    if not tasks:
        return "No tasks. Use create_task to add some."
    lines = []
    for task in tasks:
        marker = {
            "pending": "[ ]",
            "in_progress": "[>]",
            "completed": "[x]",
        }.get(task.status, "[?]")
        dependencies = (
            f" (blockedBy: {', '.join(task.blockedBy)})"
            if task.blockedBy else ""
        )
        owner = f" [{task.owner}]" if task.owner else ""
        lines.append(
            f"{marker} {task.id}: {task.subject} "
            f"[{task.status}]{owner}{dependencies}"
        )
    return "\n".join(lines)
```

```python
def run_get_task(task_id: str) -> str:
    return get_task(task_id)
```

## 3. 认领与完成：记录谁在做、是否做完 {#task-lifecycle}



### 3.1 检查依赖，再认领任务 {#task-claim}

**所属层：** Harness 内部认领逻辑，负责状态、依赖与记录更新。工具请求由 `run_claim_task` 接收，它固定 `owner="agent"` 后调用这里的函数。

```python
def claim_task(task_id: str, owner: str = "agent") -> str:
    task = load_task(task_id)
    if task.status != "pending":
        return f"Task {task_id} is {task.status}, cannot claim"
    dependencies = incomplete_dependencies(task)
    if dependencies:
        return f"Blocked by: {dependencies}"
    task.owner = owner
    task.status = "in_progress"
    TASKS.save(task)
    print(f"  [claim] {task.subject} -> in_progress (owner: {owner})")
    return f"Claimed {task.id} ({task.subject})"
```

认领在这个教学实现中同时表示开始工作。单 Agent 的工具包装固定使用 `owner="agent"`。

`can_start` 只检查依赖，任务自身的状态由认领函数检查。状态检查能避免顺序执行时重复认领；本节还没有跨进程锁，团队中的原子认领在 S13 展开。

### 3.2 实际执行仍由工作工具完成 {#task-work}

认领只把任务记为 `in_progress` 并记录 owner。API 代码、数据库迁移和测试结果仍要由模型通过文件工具、Bash 等实际完成。

因此，查看任务、认领任务、执行工作是三件不同的事：查看不改状态；认领登记负责人；执行才产生文件和验证结果。完成实际工作并核对结果后，再调用 `complete_task` 登记完成。

### 3.3 检查 owner，完成并报告新解锁 {#task-complete}

**所属层：** Harness 内部完成逻辑。模型请求 `complete_task` 工具时，本地入口 `run_complete_task` 固定 owner 后调用这里的实现；检查与保存都在此函数及其辅助函数中进行。

先确认任务正在进行且调用者是 owner，再比较完成前后的可开始任务，只报告本次新解锁的项：

```python
def complete_task(task_id: str, owner: str = "agent") -> str:
    task = load_task(task_id)
    if task.status != "in_progress":
        return f"Task {task_id} is {task.status}, cannot complete"
    if task.owner != owner:
        return f"Task {task_id} is owned by {task.owner}, not {owner}"
    ready_before = {
        candidate.id
        for candidate in list_tasks()
        if candidate.status == "pending"
        and candidate.blockedBy
        and can_start(candidate.id)
    }
    task.status = "completed"
    TASKS.save(task)
    unblocked = [candidate.subject for candidate in list_tasks()
                 if candidate.status == "pending"
                 and candidate.blockedBy
                 and candidate.id not in ready_before
                 and can_start(candidate.id)]
    print(f"  [complete] {task.subject}")
    message = f"Completed {task.id} ({task.subject})"
    if unblocked:
        message += f"\nUnblocked: {', '.join(unblocked)}"
        print(f"  [unblocked] {', '.join(unblocked)}")
    return message
```

依赖 ID 不需要删除，后续检查读取其新状态即可。标记完成不会自动跑测试或执行后续任务，完成标准仍需要实际验证。

### 3.4 用一个任务图串起来 {#task-example}

下面是 Harness 内部函数的顺序调用示例，返回的 `schema`、`api` 等变量是 Python `Task` 对象。模型实际使用这些能力时，会发出工具调用，由对应的 `run_*` 入口转交；不会直接持有这些 Python 变量。

```python
schema = create_task("建立数据库结构", "完成表结构与迁移验证")
api = create_task("实现 API", "实现接口并验证数据读写")
tests = create_task("补充测试", "验证 API 的成功与失败路径")
docs = create_task("编写文档", "记录数据结构与使用方式")
deploy = create_task("准备部署", "检查测试结果与交付资料")

update_task(api.id, [schema.id])
update_task(tests.id, [api.id])
update_task(docs.id, [schema.id])
update_task(deploy.id, [tests.id, docs.id])

claim_task(schema.id)
# Execute and verify the schema work here.
complete_task(schema.id)
claim_task(api.id)
```

最后一行之后就是图中的状态：API 正在进行，文档可认领，测试与部署仍受阻塞。这里演示任务记录的变化，数据库与 API 的实际工作仍由执行工具完成。

## 4. 接回 Agent Loop 与实现边界 {#task-integration}



### 4.1 注册六个任务工具 {#task-registration}

六个工具名出现在 `TOOLS` 的说明中；真正执行它们的本地入口由 `TOOL_HANDLERS` 指定。对应关系是：

| 模型请求的工具名 | 输入 | 本地工具入口 | Harness 内部实现 |
|---|---|---|---|
| `create_task` | `subject`，可选 `description` | `run_create_task` | `create_task` → `TaskStore.create`，创建并返回 ID |
| `update_task` | `task_id`、`addBlockedBy` | `run_update_task` | `update_task` → `TaskStore.update_dependencies`，校验并添加依赖 |
| `list_tasks` | 无 | `run_list_tasks` | `list_tasks` → `TaskStore.list`，读取列表再格式化为文本 |
| `get_task` | `task_id` | `run_get_task` | `get_task` → `load_task` → `TaskStore.load`，返回完整 JSON 文本 |
| `claim_task` | `task_id` | `run_claim_task` | `claim_task`，检查依赖、设置 owner 与状态，再保存 |
| `complete_task` | `task_id` | `run_complete_task` | `complete_task`，检查状态、owner，保存并报告新解锁 |

其中，`run_create_task` 和 `run_update_task` 把 `Task` 对象整理成文本，`run_list_tasks` 把对象列表整理成摘要；`run_get_task` 直接转发内部函数已生成的 JSON 字符串。工具入口的职责是适配调用和回复，具体规则由内部实现承担。

创建工具的 schema 只接收标题和可选描述，ID 不由模型传入：

```python
{'name': 'create_task',
 'description': 'Create a task and return its runtime-generated ID.',
 'input_schema': {'type': 'object',
                  'properties': {'subject': {'type': 'string'},
                                 'description': {'type': 'string'}},
                  'required': ['subject'],
                  'additionalProperties': False}}
```

新增依赖的 schema 明确要求两个参数：

```python
{
    "name": "update_task",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "pattern": "^task_[0-9a-f]{8}$"},
            "addBlockedBy": {
                "type": "array",
                "items": {"type": "string", "pattern": "^task_[0-9a-f]{8}$"},
                "minItems": 1,
            },
        },
        "required": ["task_id", "addBlockedBy"],
        "additionalProperties": False,
    },
}
```

下面两个函数属于**具体工具的执行入口**。它们固定使用当前教学 Agent 的 owner；模型的工具参数只需要任务 ID，内部 `claim_task`、`complete_task` 已经返回字符串，所以这里直接转发：

```python
def run_claim_task(task_id: str) -> str:
    return claim_task(task_id, owner="agent")
```

```python
def run_complete_task(task_id: str) -> str:
    return complete_task(task_id, owner="agent")
```

Schema 描述输入形状，`TaskStore` 和状态函数实施具体检查。五个基础工具及 Permission、Hooks 仍来自 S04；统一的 `execute_tool` 会把 handler 异常转换成错误说明交回模型。

### 4.2 接入已有工具执行入口 {#task-execution}

**所属层：** `execute_tool` 是各工具共用的 Harness 执行入口；`run_*` 是它分发到的具体工具入口。模型只提供工具名和参数，选择哪个 Python 函数运行由本地分发表决定。

| 位置 | 已有部分 | S10 新增什么 |
|------|----------|--------------|
| 请求模型时 | `SYSTEM`、`messages`、基础工具 schema | 六个任务工具 schema，以及先创建、后连依赖的使用指导 |
| 执行调用时 | `execute_tool` 触发权限与 Hooks，再按名称分发 | 在同一张 `TOOL_HANDLERS` 中注册任务 handler |
| handler 内部 | Bash、文件 handler 操作实际环境 | 任务 handler 读写 `TaskStore`，检查依赖、状态与 owner |
| 回传结果时 | 按 `tool_use_id` 配对，追加 `tool_result` | 创建得到的 ID、状态变化或拒绝原因通过相同路径交回模型 |

按职责把注册部分拆开，可以写成下面的示意。源码直接列出工具与分发表；这里的 `BASE_*`、`TASK_*` 名称用于展示新增位置：

```python
TOOLS = [*BASE_TOOLS, *TASK_TOOLS]
TOOL_HANDLERS = {
    **BASE_HANDLERS,
    "create_task": run_create_task,
    "update_task": run_update_task,
    "list_tasks": run_list_tasks,
    "get_task": run_get_task,
    "claim_task": run_claim_task,
    "complete_task": run_complete_task,
}
```

`TOOLS` 中的 schema 随请求交给模型，`TOOL_HANDLERS` 中的函数对象留在本地。以创建为例，键 `"create_task"` 对应的值是 `run_create_task`；这条绑定才决定调用入口，不能只根据内部函数的名字推断。

原来的 `execute_tool` 不需要为 Task System 新开一个循环：

```python
def execute_tool(block) -> str:
    blocked = trigger_hooks("PreToolUse", block)
    if blocked:
        return str(blocked)

    handler = TOOL_HANDLERS.get(block.name)
    try:
        output = handler(**block.input) if handler else f"Unknown: {block.name}"
    except Exception as error:
        output = f"Error: {error}"

    trigger_hooks("PostToolUse", block, output)
    return str(output)
```

因此，模型选择 `read_file` 时运行文件工具，选择 `claim_task` 时运行依赖与状态检查；两者都经过同一个执行入口，结果也都进入同一份消息历史。

**本章示例选择 S04 的五个基础工具、Permission 和 Hooks 作为 Kernel。** 它没有把 S05–S09 的所有机制累计复制进来；记忆、Skills、压缩等会在 S15 综合 Harness 中与任务层组合。课程概念可以接续学习，单章源码保留哪些运行组件则要按实现核对。[依据：上游解决方案](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s10_task_system/README.zh.md)。

### 4.3 接回原来的 Agent Loop {#task-loop}

**所属层：** Harness 的循环编排。它把 `SYSTEM`、消息和 `TOOLS` 交给模型，收到 `tool_use` 后调用本地 `execute_tool`，再把工具结果加入消息继续请求。`run_*` 和任务内部函数的源码不通过 `TOOLS` 字段发送。

先看实际循环：它按响应中的 `tool_use` 分块，顺序执行当前批次，再一次追加所有结果。

```python
def agent_loop(messages: list):
    while True:
        response = client.messages.create(
            model=MODEL,
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
            max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        tool_calls = [
            block for block in response.content if block.type == "tool_use"
        ]
        if not tool_calls:
            force = trigger_hooks("Stop", messages)
            if force:
                messages.append({"role": "user", "content": force})
                continue
            return

        results = []
        for block in tool_calls:
            output = execute_tool(block)
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            })
        messages.append({"role": "user", "content": results})
```

下面是控制流程伪代码，消息构造与 SDK 适配使用简写。模型发出任务或工作工具请求，Harness 按原循环处理：

```python
messages = [user(query)]
while True:
    response = call_model(system=SYSTEM, tools=TOOLS, messages=messages)
    messages.append(assistant(response.content))
    calls = get_tool_use_blocks(response.content)
    if not calls:
        follow_up = trigger_stop_hooks(messages)
        if follow_up:
            messages.append(user(follow_up))
            continue
        break

    results = []
    for call in calls:
        # Existing entry: PreToolUse -> selected handler -> PostToolUse.
        # A task handler additionally uses TaskStore and state checks.
        output = execute_tool(call)
        results.append(tool_result(call.id, output))
    messages.append(user(results))
```

新版按实际的 `tool_use` 内容块判断是否执行工具。每次任务操作仍然是“模型请求 → 原执行入口 → 任务 handler → 结果回传 → 再问模型”中的一轮；任务层没有另一个自动调度循环。自主认领与团队协调见 [S13.3]({{< relref "/projects/learn-claude-code/s13/03-task-claiming.md" >}})。

换会话时使用同一任务目录，先读取列表、详情与依赖，再核对实际文件和验证结果。任务正文不会自动全部加入 system。

### 4.4 实现边界与自己的理解 {#task-boundaries}

| 方面 | 本节新版的行为 |
|------|----------------|
| ID 与路径 | 校验 ID 格式、目录范围和记录 ID；创建遇到碰撞重试 |
| 依赖 | 拒绝未知、自依赖与环，去重，整次校验后保存 |
| 完成 | 检查负责人，只报告本次新解锁的任务 |
| 失败反馈 | handler 异常经 `execute_tool` 返回错误说明 |
| 并发 | 单 Agent 版本没有跨进程锁；S13 团队版本继续完善 |
| 可靠更新 | 普通保存直接写文件，尚非带锁的原子更新 |
| 恢复与验证 | 没有通用释放、重开工具，也不自动验证产物 |

这些说明针对当前教学源码。现代 Claude Code 的任务接口与本例不同，其团队认领使用文件锁；程序性完成检查可通过 `TaskCompleted` Hook 实现。[依据：任务认领](https://code.claude.com/docs/en/agent-teams#assign-and-claim-tasks)、[完成检查](https://code.claude.com/docs/en/hooks#taskcompleted)。

#### 当前的一句话理解

**Task System 用独立记录保存工作，用真实 ID 建立依赖，用状态与负责人检查约束认领和完成，再把可做与剩余工作的结果交给模型继续安排。**

本篇按 `ce8f9f1` 重核。原迁移日期：**2026-10-04**；三图对照、悬停连线与函数联动更新：**2026-10-05**。
