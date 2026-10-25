# 01 · 阅读范围：准备任务工作区

[本步入口](README.md) · [前一步任务总结](../step-006-agent-sandbox/05-task-flow.md) · [前序记忆](03-long-term-memory/overview.md) · [旧版 scope](references/scope-at-2f231865.md)

## 1. 阅读目标

- **整体目标**：理解 Coding Agent / Coding RL 的运行流程。
- **本步问题**：已有沙箱和 CLI 怎样接住题目配置，准备好任务工作区，并留下运行前的比较基准？
- **阅读范围**：沿 `scaleswe` 正常路径，看清用户与目录准备、可选初始化、题目写入，以及初始 Git 树标识 `baseline` 的返回。

## 2. 指挥官函数

- **整体位置**：Step 006 已交出就绪的 `sb`；本步准备工作区，随后同一个 `sb` 交给 `harness.run`。
- **本步指挥官**：[swe.prepare_workspace:187–209](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L187-L209)，入口是 [_generate:285](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L298)。
- **选择理由**：它组织工作区的几项准备，改变沙箱内状态，并把初始快照标识交回调用方，能接清“准备完成后交出什么”。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 3 项

沿用 `evaluation=False` 正常路径。以下为教学裁剪：省略多数参数、配置检查、追踪、日志、超时与失败包装，保留实际顺序及沙箱的使用边界。

```python
adapter.open_session(...)  # 1. Step 005：登记会话
async with boot_agent_sandbox(...) as sb:  # 2. Step 006：沙箱与 CLI 就绪
    baseline = await swe.prepare_workspace(...)  # 3. 本步：准备工作区，取得初始快照标识
    agent_exit_code = await harness.run(...)  # 4. 运行 Agent
    # CLI 运行期间，通过 HTTP 进入 Step 001 的模型请求流程
    agent_metrics = await harness.collect_metrics(...)  # Step 002：收集统计
    diff_text = await swe.git_diff(...)  # 5. 使用 baseline 提取代码补丁

reward, applied_cleanly = await swe.run_evaluation(...)  # 6. Step 003：独立评测
samples = await adapter.finish_session(...)  # 7. Step 004：导出样本
...  # 返回前的结果处理，以及最终会话清理
return samples
```

本步在 `baseline` 交回 `_generate` 时停止。后续 Agent 运行、补丁提取和环境回收在此只保留位置。

### 3.2 接住已有输入，展开局部骨架

- **`sb`**：Step 006 交出的同一个沙箱操作对象，环境与 CLI 已就绪。本轮沿默认 Sunabako 场景；代码仓库和 `workdir` 已在镜像内，镜像制作不在本步展开。
- **`workdir`**：调用方传入 `md["workdir"]`，指明本题的代码工作目录。已有例子是 `/workspace/auth0-python`。
- **`md`**：复用前序的题目信息。本步只跟踪 `protocol`、`grading.swepro`、`grading.pre_commands` 和 `problem_statement`；需要提醒时先回看 [md 字段说明](references/metadata.md)，再回到下面的调用。

<a id="prepare-workspace-local-skeleton"></a>

下面从当前 `swe.py:195–209` 裁剪，调用参数省略；两个独立的准备条件和最后的返回保留。

```python
await agent_sandbox.ensure_agent_user(...)  # 195：准备用户、目录访问与 Git 设置
if md.get("protocol") == PROTOCOL_SCALESWE:  # 196：本例进入此分支
    grading = md.get("grading") or {}
    swepro = grading.get("swepro")
    if swepro:
        await apply_before_repo_set_cmd(...)  # 200：按 swepro 配置准备
    pre_commands = grading.get("pre_commands")
    if pre_commands:
        await apply_pre_commands(...)  # 203：执行额外准备命令
await sb.write_file(...)  # 204–208：写入 PROBLEM_STATEMENT.md
return await _repository_tree(...)  # 209：返回初始 Git 树标识
```

**本次返回值是 `baseline: str`**：在工作区准备完成、Agent 开始运行之前取得的 Git 树标识。`_generate:285` 保存它，`298` 行将它传给 `git_diff`；这条比较关系可接回 [Step 002 的已有记录](../step-002-agent-results/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/git_diff.md)。工作区变化留在原来的沙箱中。

<a id="reading-path"></a>

### 3.3 阅读导航与停止位置

先对照上面的三个输入和新返回值，再沿局部骨架阅读。此前对 `ensure_agent_user` 和两种准备入口的已读事实保留；本轮只为它们定位当前调用与需要复核的边界。

| 阅读位置与入口 | 本步看清什么 | 返回或继续位置 |
| --- | --- | --- |
| `195` → [ensure_agent_user](02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)，当前定义 `409–420` | 复用用户与目录准备的用途，留意当前后端决定的目录归属处理；本步卡片已接入 Sunabako 场景 | 回到 `196`，读取本题准备配置 |
| `200` → [apply_before_repo_set_cmd](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md)，当前定义 `212–222` | `swepro` 中哪项命令被执行；配置没有命令时可直接返回 | 回到 `201`，继续检查另一项配置 |
| `203` → [apply_pre_commands](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md)，当前定义 `225–235` | 准备文本怎样变成脚本并在 `workdir` 中执行；保留 `check=False` 的结果边界 | 回到 `204`，写入题目说明 |
| [204–208：题目写入](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L204-L208) | 对应目标路径、题目字符串与 `user="agent"`，区分写入说明和执行命令；先停在 `sb.write_file` 接口 | 继续 `209`，记录准备后的初始状态 |
| `209` → [_repository_tree](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_repository_tree.md)，定义 `241–262` | 本轮确认展开临时索引、按工作区更新路径及树标识返回；保留原暂存区与 `HEAD` 的区别 | 先返回 `prepare_workspace:209`，再交给 `_generate:285` 的 `baseline` |

`swepro` 和 `pre_commands` 是先后检查的两个条件，两项都有值时都可执行。沿用 [auth0-python 真实题目的字段](references/scaleswe-auth0-example.md)时，只有 `pre_commands` 触发；`swepro` 的旧教学例子独立保留，两份例子不拼成一次运行。题目字段来自既有资料，本轮不重新展开数据集加载。

**停止条件**：能说明三个输入怎样推动工作区准备、题目文件留下什么，以及 `baseline` 怎样交回并用于后续比较。本轮经用户确认下钻 `_repository_tree`，看清临时索引与树标识；索引和对象的底层存储、SDK 传输、镜像部署与后续 Agent 启动继续后置，下钻不超过两层。

## 版本说明

- **源码基准**：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本机 checkout 为 `/home/fredkeira/projects/slime`。
- **关键变化**：入口为 `_generate:285`；`prepare_workspace` 在写题目后返回 `_repository_tree` 的结果，旧版的 `None` 返回不再适用。整体骨架同步使用当前 `adapter`、`harness` 与统计收集调用。
- **可复用与需复核处**：两个准备命令函数的 AST 与 `2f231865` 相同，但 `pre_commands` 的脚本路径常量已由 `/workspace` 改到 `/tmp`；`ensure_agent_user` 的后端条件、路径处理和命令预算也有变化。默认 Sunabako 的 `write_file` 委托 SDK，旧 E2B 内部实现仅对应其分支。
- **材料边界**：[旧版 scope](references/scope-at-2f231865.md)完整保留；父卡和三张既有辅助卡已校准，本轮新增 [_repository_tree 记录](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_repository_tree.md)。原话与认识日期保留，独立例子注明各自场景；输入参考与 `03` 继承快照仍保留旧版来源。过程见[逐卡更新](04-flow.md#prepare-workspace-short-term-refresh)与[本轮建卡](04-flow.md#repository-tree-function-card)。
