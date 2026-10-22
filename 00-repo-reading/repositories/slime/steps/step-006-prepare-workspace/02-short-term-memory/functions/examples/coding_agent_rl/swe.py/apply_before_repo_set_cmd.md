# apply_before_repo_set_cmd

- 源码定位：[examples/coding_agent_rl/swe.py:201–211](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L201-L211)，由助手核对。
- 首次接触：Step 6 的 `prepare_workspace` 局部骨架；2026-10-22 经用户确认，首次单独展开。
- 最近认识更新：2026-10-22，用户在命令来源与用途澄清后反馈“大概理解了”，概括为按题目配置执行提前准备，并类比 `pre_commands`；当前要求先看 `metadata` 与 `grading` 的结构，尚未展开 `apply_pre_commands` 内部实现。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`prepare_workspace` 已准备好 `agent` 用户和工作目录；在 `scaleswe` 场景下发现 `grading` 中有 `swepro` 配置，调用本函数补齐这道题指定的工作区准备。采用 `swepro` 评测分支时，`_grade_scaleswe` 也在应用代码补丁前，对独立的评测沙箱调用它。

2. **具体内容**：从 `swepro["before_repo_set_cmd"]` 读取已经给定的命令，补上脚本设置和进入工作目录的命令；准备脚本存放目录，把内容写到远端 `before.sh`，再以 `agent` 身份用 Bash 执行。生成的是包装这些命令的脚本；没有输入命令时直接返回。

3. **建议构建的心智模型**：

   > `apply_before_repo_set_cmd` 在已有沙箱中执行这道题预先指定的工作区准备，供 Agent 开始工作或评测应用补丁前使用。
   >
   > 命令已经保存在 `swepro` 中；函数把它封装成脚本，先写入文件，再执行。准备效果留在沙箱中，函数不返回执行结果。

4. **调用代码**（`prepare_workspace` 的 `scaleswe` 分支，187–190）：

   ```python
   grading = md.get("grading") or {}
   swepro = grading.get("swepro")
   if swepro:
       await apply_before_repo_set_cmd(sb, workdir, swepro)
   ```

## 本场景的输入与输出

沿用 [prepare_workspace](prepare_workspace.md) 的 `sb` 和 `/workspace/repo`。为观察本分支，这次将父函数原例的空 `grading` 换成带 `swepro` 的配置；原例及其跳过分支的结果仍保留。下面的命令是教学构造，不代表真实题目附带的初始化内容；输出按命令执行成功推导，未运行远端沙箱。

**输入：已有沙箱、工作目录、准备配置。**

`swepro` 来自样本的 `metadata.swepro`，经 `_metadata_scaleswe` 放进 `md["grading"]["swepro"]`。`before_repo_set_cmd` 是字典键，它对应的值就是事先提供的命令字符串；本函数读取这个值。

这层配置与 `pre_commands`、评测资料的关系，统一见 [md 输入说明中的 grading](../../../../../references/metadata.md#grading)。

```python
# sb：已就绪的 E2BSandbox；agent 用户与工作目录归属已准备好
workdir = "/workspace/repo"
swepro = {
    "before_repo_set_cmd": "mkdir -p .cache",
}
# swepro 在调用处来自 md["grading"]["swepro"]
```

**输出：远端脚本和它执行后的准备效果。**

远端 `/workspace/swepro_setup/before.sh` 中的完整内容为：

```bash
set -e
cd /workspace/repo
mkdir -p .cache
```

| 项目 | 本例的对应结果 |
| --- | --- |
| 脚本存放目录 | `/workspace/swepro_setup`，属主和属组设为 `agent:agent` |
| 写入的脚本 | `/workspace/swepro_setup/before.sh`，内容如上 |
| 执行脚本的效果 | 在 `/workspace/repo` 下确保 `.cache` 目录存在 |
| 函数返回值 | 正常结束返回 `None`；不返回脚本内容或命令结果 |
| 返回位置 | 回到 `prepare_workspace:191`，继续查看 `pre_commands` |

`.cache` 是脚本中的命令执行后产生的效果，写入 `before.sh` 本身只保存文本。脚本存放目录与命令执行时的工作目录是两个位置。

### 1. 配置中的命令 → 脚本内容（203–206）

```python
before = swepro.get("before_repo_set_cmd")
if not before:
    return
payload = f"set -e\ncd {workdir}\n{before}\n"
```

- **取出准备命令**：本例 `before` 是字符串 `"mkdir -p .cache"`。字典没有这个键或值为空时，直接返回 `None`，不准备目录、不写脚本，也不执行命令。
- **组装脚本文本**：把进入工作目录的 `cd` 和配置中的命令按行拼起来；`payload` 此时只是本地 Python 字符串。
- **设置脚本行为**：`set -e` 设置遇错退出策略；对于本例顺序执行的简单命令，`cd` 或 `mkdir` 失败时会结束脚本。完整适用条件见折叠来源。

### 2. 脚本内容 → 远端文件 → 执行效果（207–211）

```python
await sb.exec(
    "mkdir -p /workspace/swepro_setup && chown agent:agent /workspace/swepro_setup", user="root", check=True
)
await sb.write_file("/workspace/swepro_setup/before.sh", payload, user="agent")
await sb.exec("bash /workspace/swepro_setup/before.sh", user="agent", check=False, timeout=600)
```

- **第一次 `exec` 准备存放位置**：以 `root` 身份确保 `/workspace/swepro_setup` 存在，并把这个目录的归属设给 `agent`。它准备的是脚本目录，工作目录已经在前面准备好。
- **`write_file` 保存命令**：以 `agent` 身份将 `payload` 写入远端 `before.sh`；此时脚本中的 `mkdir -p .cache` 还没有执行。
- **第二次 `exec` 执行脚本**：以 `agent` 身份运行 `bash /workspace/swepro_setup/before.sh`。Bash 先执行 `cd /workspace/repo`，再运行准备命令；命令超时参数为 600 秒。
- **返回值的边界**：最后一次执行使用 `check=False`。在本例 E2B 实现中，脚本非零退出会作为命令结果返回，但这里没有保存或检查该结果；因此本函数返回 `None` 本身不能证明准备命令成功。文件操作或通信仍可能抛出异常。

这里沿用 [E2BSandbox 的操作接口](../../../../../03-long-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)：本地调用 `sb.exec`、`sb.write_file`，对应操作发生在同一个远端沙箱中；SDK 内部实现本轮不深入。

## 我的直接表述（原话）

在上一轮推荐本函数后，用户确认继续：

> 好的那么请看一下这里 你想要读的这个function吧

随后用户提出理解并追问目的：

> 好的 我可以简单理解为这里是根据这个
> swepro的这个格式
> 来生成一个before_repo_set_cmd 需要执行的指令吗
>
> 不过这个apply before repo set cmd具体是为了做什么呢？

助手将“生成指令”校正为“读取已有命令、封装脚本并执行”，并根据两处调用解释题目前置准备的用途；这些澄清当时尚待用户反馈。

随后用户反馈并要求先看配置结构：

> 好的 我大概理解了 反正就是按照这个swe 单独配置一下需要提前执行的一系列操作对吗
> 我可以这么理解吗？
> 下面的pre commond也是类似的
> 那么这里的重点应该就是这里的grading也就是这个metadata中的信息
> 是否应该先处理一下这一部分呢？

本次记录为对按题目配置执行准备操作的大致理解；`pre_commands` 的共同用途和配置层次另行核对，不将类比视为已掌握另一个函数的实现。

## 尚不清楚

- 当前真实样本的 `before_repo_set_cmd` 具体包含什么、会产生哪些状态变化，仍需结合样本查看；本轮的 `.cache` 只是教学命令。
- 脚本失败后的完整处理，以及 SDK 的文件写入、执行与重试机制，尚未展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：函数见 `swe.py:201–211`，当前调用与返回位置见 `swe.py:185–194`；`E2BSandbox.exec` 与 `write_file` 见 `sandbox.py:309–376`。
- 命令来源见 `swe.py:83–110`：从样本 metadata 取出 `swepro` 并放入 `grading`；评测复用见 `swe.py:269–282`：在独立沙箱内执行准备命令，再应用补丁、运行评测。两处复用相同配置，说明此入口用于重复落实该题的前置准备；这里只核对调用用途，不据此推断每道题的具体脚本内容。
- 本机 `swe.py` 仍只有评测分支的一处空白字符差异，不影响本函数。未修改 Slime 源码。
- 教学输入为 `before_repo_set_cmd="mkdir -p .cache"`；脚本文本及目录效果按源码和正常命令语义静态推导。未运行初始化命令或申请远端沙箱。
- [Bash 官方手册：set -e](https://www.gnu.org/s/bash/manual/html_node/The-Set-Builtin.html)列出遇错退出的适用条件，以及 `if`、部分 `&&` / `||` 等上下文的例外；本例只用顺序简单命令。脚本退出策略与 Python 侧是否检查退出码是两个层次。
- 形成过程：[Step 6 · 将配置命令写成脚本并执行](../../../../../../step-006-prepare-workspace/04-flow.md#apply-before-repo-set-cmd-entry)。
- 后续问题：[Step 6 · 命令来源与题目前置准备的用途](../../../../../../step-006-prepare-workspace/04-flow.md#before-repo-set-purpose)。
- 后续反馈与输入背景：[Step 6 · 先看 metadata 与 grading 的配置结构](../../../../../../step-006-prepare-workspace/04-flow.md#grading-input-context)。

</details>
