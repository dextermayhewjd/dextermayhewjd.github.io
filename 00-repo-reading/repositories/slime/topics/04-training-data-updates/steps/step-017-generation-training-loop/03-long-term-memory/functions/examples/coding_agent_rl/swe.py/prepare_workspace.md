# prepare_workspace

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../../02-rollout-reward/steps/step-011-generate-and-rm-group/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[examples/coding_agent_rl/swe.py:177–198](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L177-L198)，由助手核对。
- 首次接触：Step 5 总结中定位为下一处；Step 6，2026-10-22 开始函数记录。
- 最近认识更新：2026-10-22，用户在两个准备入口的讲解后反馈“大概明白了”，并追问是否将 SWE 逻辑写入沙箱后交给下游；本次补充准备命令、远端效果与同一 `sb` 的交接区别，尚未将整个父函数标为读完。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`generate` 已从 `boot_agent_sandbox` 取得安装好 CLI 的 `sb`，准备在启动 Agent 之前整理任务工作区。

2. **具体内容**：准备 `agent` 用户、目录归属与 Git 设置；按 `md` 的协议和配置执行可选初始化；最后以 `agent` 身份把题目写入工作目录的 `PROBLEM_STATEMENT.md`。

3. **建议构建的心智模型**：

   > `prepare_workspace` 接住已有沙箱与题目信息，整理谁来操作工作区、运行前需要做哪些准备，并把要解决的问题放成文件。
   >
   > 正常返回 `None`，准备效果留在远端工作区；调用方随后用同一个 `sb` 启动 Agent。
   >
   > 本函数从配置中取准备命令；`eval_cmd` 与 `f2p_script` 留给后续独立评测，本函数不执行它们。

4. **调用代码**（`generate.py:203–205`，最后一行省略 Agent 启动参数）：

   ```python
   async with boot_agent_sandbox(md["image"], instance_id) as sb:
       await swe.prepare_workspace(sb, md["workdir"], md)
       agent_exit_code = await HARNESS_CLS().run(sb, ...)
   ```

## 本场景的输入与输出

先看 [md 的本步输入说明](../../../../../../../../01-coding-agent-rl/steps/step-007-prepare-workspace/references/metadata.md)，接清 `grading.swepro`、`grading.pre_commands` 和 `problem_statement` 分别是什么，再对照下面的真实题目与处理阶段。

采用真实 Scale-SWE 题目 `auth0_auth0-python_pr671`：修复 `auth0-python` 的请求格式，使其发送表单编码的请求。`row` 表示[原始字段节选](../../../../../../../../01-coding-agent-rl/steps/step-007-prepare-workspace/references/scaleswe-auth0-example.json)中的 `row`；下方为按 Slime 接口重组后的 `md`，字段值来自该题目，省略本函数不使用的协议检查标记。这个映射用于阅读，没有实际启动镜像或运行测试；[完整来源和接入边界](../../../../../../../../01-coding-agent-rl/steps/step-007-prepare-workspace/references/scaleswe-auth0-example.md)单独保留。

**输入：`sb`、`workdir`、`md` 三项。**

```python
# sb：前一步已进入、已安装 CLI 的 E2BSandbox 对象
md = {
    "protocol": "scaleswe",
    "instance_id": "auth0_auth0-python_pr671",
    "image": row["image_url"],
    "workdir": "/workspace/auth0-python",
    "problem_statement": row["problem_statement"],  # 描述请求格式问题的文字
    "grading": {
        "swepro": None,
        "eval_cmd": None,
        "f2p_script": row["f2p_script"],           # 测试源码，留给后续评测
        "pre_commands": row["pre_commands"],       # 准备命令，本函数会使用
    },
}
workdir = md["workdir"]
```

`instance_id` 和 `image` 留在同一份 `md` 中供其他阶段使用，本函数主要读取协议、初始化配置和题目内容。`sb` 的对象关系可回查 [E2BSandbox](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)。

本例的 `pre_commands` 包含 `git checkout 5564a75cd2a85c0a919be6c17883e4c418a7960c -f`，将仓库切到这道题指定的基础版本；完整命令还包括清理和 Git 状态整理。`f2p_script` 包含检查请求格式的测试代码，但不在此处使用。来源与字段分工见 [md 输入说明中的 grading](../../../../../../../../01-coding-agent-rl/steps/step-007-prepare-workspace/references/metadata.md#grading)。

**输出：返回值为 `None`；以下是相关命令成功执行时，同一远端工作区应有的变化。** 可选准备命令使用 `check=False`，仅凭函数返回不能证明它们执行成功。

| 内容 | 本例结果 |
| --- | --- |
| 使用者与目录 | `agent` 用户存在，`/home/agent` 与 `/workspace/auth0-python` 的归属已设置，Git 安全目录配置已处理 |
| 额外初始化 | 跳过 `swepro` 入口；执行 `pre_commands`，仓库回到题目指定的基础版本 |
| 题目文件 | `/workspace/auth0-python/PROBLEM_STATEMENT.md` |
| 文件内容 | 同一条题目的 `problem_statement` 原文，告诉 Agent 要修复哪种请求行为 |
| 评测资料 | 本次不写入或执行 `f2p_script`，不计算 reward |
| 后续交接 | 返回 `generate.py:205`，原来的 `sb` 继续传给 `HARNESS_CLS().run` |

### 1. 已有沙箱 → 可由 agent 使用的目录（185）

```python
await agent_sandbox.ensure_agent_user(sb, workdir)
```

- **输入不换对象**：继续操作刚才的 `sb` 和已有的工作目录。
- **准备使用者与归属**：复用已读的用户准备函数，让后面的文件写入和 Agent 进程使用 `agent` 身份。
- **回到本函数**：子函数正常返回 `None`，接着处理任务配置。`workdir` 需要已存在，此处的命令会修改归属，不负责创建缺失的工作目录。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [ensure_agent_user](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)：展开当前执行沙箱中的用户、目录和 Git 准备 | 返回 `None` 后，同一个 `sb` 与 `workdir` 继续进入 186 行查看任务配置 |

### 2. 任务配置 → 可选的运行前初始化（186–193）

```python
if md.get("protocol") == PROTOCOL_SCALESWE:
    grading = md.get("grading") or {}
    swepro = grading.get("swepro")
    if swepro:
        await apply_before_repo_set_cmd(sb, workdir, swepro)
    pre_commands = grading.get("pre_commands")
    if pre_commands:
        await apply_pre_commands(sb, workdir, pre_commands)
```

- **先选协议**：只有 `protocol == "scaleswe"` 才进入这一段。其他协议仍会走前面的用户准备和后面的题目写入。
- **再看是否给了配置**：`swepro` 有值时交给第一个入口；`pre_commands` 有值时交给第二个入口。两项都给出时按代码顺序处理。
- **本例的实际路径**：`swepro` 是 `None`，第一项跳过；`pre_commands` 非空，交给第二个入口执行。返回后继续写入题目。
- **留在远端的是准备效果**：这两个入口把题目配置中的命令写成脚本并执行，改变远端工作区；选择步骤、调用函数的 SWE Python 编排仍在本地运行。
- **评测字段没有参与**：这段代码未读取 `eval_cmd` 或 `f2p_script`。它们与准备命令放在同一个字典，并不表示要在同一阶段执行。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [apply_before_repo_set_cmd，201–211](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md)：处理 `swepro` 中可选的 `before_repo_set_cmd`；子卡保留另一条教学配置，展示脚本写入与执行 | 回到 191 行，再查看是否有 `pre_commands`；本页真实题目例子跳过该调用 |
| [apply_pre_commands，214–224](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md)：沿用本例的完整准备命令，展开文字整理、脚本写入与执行 | 回到 194 行，在同一工作区写入题目 |

### 3. 题目字符串 → 远端题目文件（194–198）

```python
await sb.write_file(
    f"{workdir}/PROBLEM_STATEMENT.md",
    md.get("problem_statement") or "",
    user="agent",
)
```

- **路径来自 `workdir`**：本例写入远端 `/workspace/auth0-python/PROBLEM_STATEMENT.md`。
- **内容来自 `md`**：取 `problem_statement` 字符串；缺失或为空时写入空字符串。这次交给 `write_file` 的是文字内容，前一步安装 CLI 时交给它的则是本机包文件的 `Path`。
- **题目文件的用途**：后面的默认 `SWE_PROMPT` 会要求 Agent 读取当前目录中的这个文件，获得要解决的问题。
- **写完后交还主线**：本函数正常结束，返回 `None`；`generate` 仍持有原来的 `sb`，随后在 205 行将它传给 `HARNESS_CLS().run`。这里传递的是操作同一远端沙箱的本地对象，具体启动过程留给后续调用。

## 我的直接表述（原话）

本轮确认阅读对象：

> 好的那么现在是否适合展开了呢？
> 也就是开始处理这里的swe.prepare_workspace吧

后续反馈与本次问题：

> 这里的eval cmd和f2p script是哪里来的呢？
> 我不是特别理解
> 主要是是否能够哪一个真实的例子
> 否则我梳理不清楚这里到底在做什么
> 感觉这里的这个prepare workspace function 我根本不清楚到底是在做什么

两个准备入口讲解后的反馈：

> 好的 我大概明白了
> 那么按照当前的这两个步骤的话都解决了的话
> 那么目前应该看哪一块呢？
> 我可以理解为这里其实就是把swe的一系列逻辑全部写到这里的agent sandbox里面了
> 然后吧这样子sandbox将给下面呢？

用户已反馈对前述讲解“大概明白了”，并尝试连接下游。上文“题目提供的命令在远端执行、Python 编排仍在本地、调用方继续使用同一个 `sb`”是本次助手补充的澄清，不记为用户已逐项确认。

## 尚不清楚

- 用户已反馈前述准备入口“大概明白了”；本次对本地编排、远端效果与同一沙箱交接的区别，尚待后续反馈。
- 下一处建议看 194–198 行题目写入的输入与结果；本次定位不算已展开其实现。另一条 `swepro` 真实题目配置尚未选例。
- `write_file` 的 SDK 内部实现与具体命令失败的处理细节，本轮未展开。
- 本例没有取得真实沙箱的运行结果；原数据的评测脚本退出码与镜像接入还需适配，不能把字段映射当作已跑通评测。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：调用见 `generate.py:203–205`，本函数及两个初始化入口见 `swe.py:177–224`，默认题目读取提示见 `swe.py:61–67`，用户准备见 `sandbox.py:390–399`。
- 边界：两个可选初始化入口使用 `check=False` 执行命令，本函数没有进一步检查其退出码；因此可选命令的正常返回不等于其执行结果已被验收。异常传播与完整失败处理留待按需阅读。
- 本次确认本地 `swe.py` 的已有差异位于评测段落的空白字符，不影响本函数；未改动 Slime 源码。原始字段、固定数据版本、映射说明与局部调用核对见[真实例子](../../../../../../../../01-coding-agent-rl/steps/step-007-prepare-workspace/references/scaleswe-auth0-example.md)。输出中的远端状态仍是正常路径推导，没有实际执行远端命令。
- 形成过程：[Step 6 · 从已就绪的沙箱进入工作区准备](../../../../../../../../01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#prepare-workspace-entry)。
- 本次追问与修正：[Step 6 · 用真实题目补回准备函数的输入与输出](../../../../../../../../01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#real-task-preparation-example)。
- 后续反馈与交接澄清：[Step 6 · 准备效果留在哪里，接下来读什么](../../../../../../../../01-coding-agent-rl/steps/step-007-prepare-workspace/04-flow.md#preparation-effects-and-sandbox-handoff)。

原先沿用 Step 4 的空配置教学例子保留在这里，避免与真实题目混用：

```python
md = {
    "protocol": "scaleswe",
    "instance_id": "issue-123",
    "image": "example-image",
    "workdir": "/workspace/repo",
    "problem_statement": "修复仓库中导致测试失败的问题。",
    "grading": {},
}
```

这个旧例子跳过两种可选初始化，写出 `/workspace/repo/PROBLEM_STATEMENT.md`；它的所有值均为教学构造，未运行真实沙箱。

</details>
