# ensure_agent_user

- 源码定位：[slime/agent/sandbox.py:409–420](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L409-L420)，由助手核对。
- 首次接触：Step 2，2026-10-21，从 `_grade_scaleswe` 中 `ev` 的第一次使用处进入。
- 最近认识更新：2026-10-21，用户已复述“沙箱创建后调用 exec 执行准备内容”的顺序；具体命令、协议关系与本地/远端运行位置仍在核对。
- 本轮源码校准：2026-10-23，更新后端条件、调用场景与命令预算；[旧版完整卡片](../../../../../references/ensure-agent-user-at-2f231865.md)保留，源码更新不计为个人新增认识。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`_grade_scaleswe` 已取得评测环境对象 `ev`，在应用补丁、执行测试前，先准备执行用户和工作目录权限。

2. **具体内容**：将用户准备、按后端条件调整目录归属、Git 安全目录配置拼成一条命令，通过传入对象的 `exec` 以 `root` 执行。后端模拟 root 时跳过 `chown`；工作目录经过 shell 引用，命令时间预算为 600 秒。成功后返回 `None`。

3. **建议构建的心智模型**：

   > `ensure_agent_user` 使用已经创建好的沙箱，准备后续操作需要的用户、目录权限和 Git 设置。
   >
   > 它决定执行什么准备命令；命令怎样在远端运行，由传入对象的 `exec` 方法完成。

4. **调用代码**（`swe.py:320–322`，节选）：

   ```python
   async with _evaluation_sandbox(image, trace) as ev:
       with trace_span(trace or [], "evaluation_prepare", record_error=False):
           await agent_sandbox.ensure_agent_user(ev, workdir)
   ```

## 本场景的输入与输出

承接 [_evaluation_sandbox](../../../examples/coding_agent_rl/swe.py/_evaluation_sandbox.md) 交出的 `ev`，假定镜像中的 `/workspace/repo` 已存在。以下环境变化按成功路径推导，未在真实沙箱执行；后端条件决定是否执行目录归属调整。

**输入：已有沙箱对象与工作目录。**

```python
# ev：_evaluation_sandbox 交付的已就绪后端对象；传入后由形参 sb 引用。
workdir = "/workspace/repo"
```

<a id="sandbox-protocol"></a>

**参数 `sb: Sandbox` 中的协议关系：**

| 名称 | 在本次调用中的含义 |
| --- | --- |
| `Sandbox` | 约定沙箱应提供的接口，包括 `exec`、文件读写、进入和退出等；本函数使用 `exec`，另读取可选的 `emulates_root` 标记 |
| `sb` | 引用传入的同一个 `ev`；类型取决于上一层选中的后端 |
| `sb.exec(...)` | 调用所选后端的实际执行方法，例如 `SunabakoSandbox.exec` 或 `E2BSandbox.exec` |

- `sb: Sandbox` 表达对参数能力的要求；进入本函数时直接使用已有对象。`Sandbox.exec` 的协议声明用于说明接口，具体执行体由后端提供。
- 调用处的 `agent_sandbox` 是 `sandbox.py` 模块的别名，用于定位这里的 `ensure_agent_user` 函数。

**成功后的输出与环境变化：**

| 项目 | 结果 |
| --- | --- |
| 当前函数的返回值 | `None`；后续继续使用原来的 `ev` |
| 沙箱用户 | 已存在 `agent` 用户；缺少时创建 |
| 目录归属 | `emulates_root` 为假或不存在时，递归设置 `/home/agent` 和工作目录为 `agent:agent`；为真时跳过这项 `chown` |
| Git 配置 | 系统级 `safe.directory` 增加 `*`，允许 Git 操作不同归属的仓库 |

**本函数怎样使用 `exec`（第 409–420 行）：**

```python
async def ensure_agent_user(sb: Sandbox, workdir: str) -> None:
    """Provision the agent account, filesystem access, and Git configuration."""
    command = "id agent >/dev/null 2>&1 || useradd -m -s /bin/bash agent"
    if not getattr(sb, "emulates_root", False):
        command += f" && chown -R agent:agent /home/agent {shlex.quote(workdir)}"
    command += " && git config --system --add safe.directory '*' && id agent"
    await sb.exec(
        command,
        user="root",
        check=True,
        timeout=600,
    )
```

- **用户准备**：先用 `id agent` 检查用户；检查失败时尝试 `useradd`，创建主目录并指定 bash。
- **目录准备**：没有模拟 root 时，用 `chown -R` 调整工作目录和 `/home/agent` 的归属；模拟 root 时省略这段命令。标记不存在按 `False` 处理。`shlex.quote(workdir)` 让目录路径作为一个 shell 参数传入。
- **Git 准备**：设置 `safe.directory '*'`，最后再执行 `id agent`。这些操作被拼成一条命令字符串，通过一次 `exec` 提交。
- **执行位置**：`ensure_agent_user` 在调用方进程中组织命令，再交给后端；命令字符串描述的 shell 操作在选中的沙箱环境中执行。
- **执行条件**：以 `root` 执行上述准备，命令时间预算由旧版 60 秒改为 600 秒；`check=True` 要求底层在命令失败时报告异常。
- **返回主线**：`exec` 返回的退出码、标准输出和标准错误在这里没有保存；本函数正常结束时返回 `None`，随后回到 `_grade_scaleswe`。异常则向外传播，不在这里转为评分。

本例没有 `swepro` 或 `pre_commands`，因此返回后继续到 `_grade_scaleswe:329` 的 `_apply_diff(ev, workdir, diff_text)`，使用同一个环境应用补丁。

## 我的直接表述（原话）

2026-10-21，对当前调用关系的理解（节选，保留问句）：

> 然后这里的ensure agent user 是执行这个exec 并且是某一条特定的指令？

随后对整体顺序的复述：

> 简单来说就是创建好的了之后 在远端的这个sandbox需要执行这个sandbox的exec的操作
> 具体的含义是下面的一系列内容

## 尚不清楚

- 具体 shell 语法尚未逐项讨论；当前先建立这组命令的目的与结果。
- 具体后端的 `exec` 怎样执行命令、处理结果和故障，仍作为下一层实现保留；模拟 root 的内部实现不在本轮展开。
- 用户已表达创建后执行准备内容的顺序；协议与实际对象的对应、本地调用与远端执行的位置区别仍待进一步确认。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码同页首；配套定位：`swe.py:38、320–329`，`sandbox.py:33、55、326`。Sunabako 的标记来源见 [emulates_root](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L29-L33)：`proot` 运行时返回真，具体实现暂不展开。
- 本轮局部验证从新版源码提取本函数，用替身记录 `exec` 调用；检查标记为真、假和缺失时的命令差别，以及一次调用、`user="root"`、`check=True`、`timeout=600` 和返回 `None`。没有执行 shell 或申请真实沙箱；旧版 60 秒的验证记录保留在页首链接的完整快照。
- [协议含义与语言依据](../../../../../../step-003-swe-evaluation/references/sandbox-entry.md#protocol-contract)保存《Fluent Python》的双语原文及本仓库的对应关系。
- 原始 Step 2：[名称与阅读层次](../../../../../../step-003-swe-evaluation/04-flow.md#module-function-exec-boundary) · [本次卡片与协议背景](../../../../../../step-003-swe-evaluation/04-flow.md#ensure-agent-user-card)。
- 本次复述与位置澄清：[创建完成后执行准备命令](../../../../../../step-003-swe-evaluation/04-flow.md#sandbox-ready-then-command)。
- 新版接续：[Step 003 · 从环境交付回到用户准备](../../../../../04-flow.md#ensure-agent-user-refresh)。
- 用户原话及记录边界见[当时的讨论](../../../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#sandbox-memory-entry-boundary)。

</details>
