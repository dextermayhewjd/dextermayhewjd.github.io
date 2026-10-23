# ClaudeCodeHarness.write_config

- 源码定位：[slime/agent/harness/claude_code.py:57–84](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L57-L84)，由助手核对。
- 首次接触：Step 7 的 `BaseHarness.run:103`；2026-10-22 首次单独展开。
- 最近认识更新：2026-10-23，用户已概括配置同时包含原有确认状态与 PreCompact/PostCompact，两个事件指向提前放好的同一脚本；安装与运行前配置的阶段区分、事件输入的区别经本轮补充后尚待反馈。
- 本步调取：2026-10-23，从[此前累计的完整记录](../../../../../../../step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md)调入 Step 002。旧记录完整保留在页末折叠中；本页上半部按新版核对，实际认识更新见本页原话。

## LLM 整理：使用场合、具体内容与心智模型

以下按当前 `18868a79` 整理整个函数；本轮重点是脚本放置与 hook 注册。

1. **使用场合**：CLI 已安装；`BaseHarness.run` 已准备用户和 `ctx`，本次 CLI 尚未启动，先调用本方法准备 Claude Code 的配置。

2. **具体内容**：保留原有的两项自动运行确认状态；新增读取压缩次数上限、把 `compaction.py` 复制到沙箱、为 `PreCompact` 与 `PostCompact` 配置脚本命令。最后把完整 JSON 写入沙箱中的两个配置文件并设置归属，正常返回 `None`。新版会读取 `ctx.workdir`。

3. **建议构建的心智模型**：

   > - 先把事件处理脚本放进沙箱，再告诉 CLI：压缩前、压缩后两个事件都执行这条脚本命令。
   > - 命令带上本次统计目录和次数上限；两项自动运行确认状态也一起写入配置。
   > - 本函数交付脚本和配置文件。启动 CLI 与初始化统计文件在后面的启动步骤完成。

4. **调用代码**（`harness/common.py:103–104`）：

   ```python
   await self.write_config(sb, ctx)
   return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)
   ```

## 本场景的输入与输出

教学场景沿用本步 `run_hook` 的 `/workspace/repo` 与上限 `2`。`self` 是 `ClaudeCodeHarness`，`sb` 连接已经准备好的沙箱；`ctx` 是本次 `HarnessContext`，此函数只读取其 `workdir`。

### 输入

```python
ctx.workdir  # "/workspace/repo"
os.environ["SLIME_AGENT_CC_MAX_COMPACTIONS"]  # "2"，本例设置
```

环境变量未设置时上限为 `-1`，表示不启用次数限制；小于 `-1` 时在写入之前抛出 `ValueError`。

### 输出与副作用

正常返回 `None`。以下是提交的文件操作与预期结果，已验证生成的参数，没有实际写入远端：

| 沙箱里的文件 | 内容 |
| --- | --- |
| `/tmp/slime-claude-compaction.py` | 本地同目录 `compaction.py` 的源码副本 |
| `/home/agent/.claude.json` | 下方完整配置 JSON |
| `/home/agent/.claude/settings.json` | 同一份 JSON；这两个配置文件及 `.claude` 目录设置为 `agent:agent` |

```json
{
  "hasCompletedOnboarding": true,
  "bypassPermissionsModeAccepted": true,
  "hooks": {
    "PreCompact": [{"hooks": [{"type": "command", "command": "python3 /tmp/slime-claude-compaction.py /workspace/repo/.harness 2", "timeout": 10}]}],
    "PostCompact": [{"hooks": [{"type": "command", "command": "python3 /tmp/slime-claude-compaction.py /workspace/repo/.harness 2", "timeout": 10}]}]
  }
}
```

配置写入会覆盖这两个 JSON 文件，不与旧配置合并。此时还没有由本方法创建 `.harness/compaction.json`，也没有执行 `run_hook`。

### 这一步怎样完成准备（59–84）

下面是函数体的连续源码，省略说明字符串：

```python
limit = int(os.environ.get(self.max_compactions_env, "-1"))
if limit < -1:
    raise ValueError(f"{self.max_compactions_env} must be -1 or nonnegative")
directory = f"{ctx.workdir}/.harness"
hook_path = "/tmp/slime-claude-compaction.py"
await sb.write_file(hook_path, Path(__file__).with_name("compaction.py"))
command = f"python3 {hook_path} {shlex.quote(directory)} {limit}"
settings = json.dumps(
    {
        "hasCompletedOnboarding": True,
        "bypassPermissionsModeAccepted": True,
        "hooks": {
            event: [{"hooks": [{"type": "command", "command": command, "timeout": 10}]}]
            for event in ("PreCompact", "PostCompact")
        },
    }
)
await sb.exec(
    "mkdir -p /home/agent/.claude && "
    f"echo {shlex.quote(settings)} "
    "| tee /home/agent/.claude.json /home/agent/.claude/settings.json > /dev/null && "
    "chown -R agent:agent /home/agent/.claude /home/agent/.claude.json",
    user="root",
    check=True,
    timeout=60,
)
```

- **确定输入**：读取上限；`ctx.workdir` 决定统计目录是 `/workspace/repo/.harness`。
- **放置脚本**：`Path(__file__).with_name("compaction.py")` 指向宿主机上与 `claude_code.py` 同目录的文件；`sb.write_file` 将其内容写到沙箱的 `hook_path`。这里复制脚本，没有执行脚本。
- **注册命令**：`hooks` 以两个事件名称为键，分别放入同一个命令。命令传目录和上限；具体事件名由 CLI 的 hook 输入提供，脚本入口从 stdin 读取后传给 [run_hook](../compaction.py/run_hook.md)。因此共用脚本和命令，传入的事件名仍不同。
- **写好配置**：`settings` 先是宿主机内存中的字符串，`sb.exec` 再让沙箱执行 `echo … | tee …`，写入两个文件。随后 `chown` 设置归属；`check=True` 要求检查执行结果，失败会传播异常。
- **返回主线**：正常返回 `None`，`BaseHarness.run` 接着调用 [launch_and_wait](ClaudeCodeHarness.launch_and_wait.md#compaction-initialization)，在那里组装初始化统计并启动 CLI 的命令。

三步之间的联系见[机制参考](../../../../../../references/compaction-metrics-lifecycle.md#function-coverage)；当前卡片只展开配置准备。

## 我的直接表述（原话）

本轮最初明确要看前两步：

> 好的
> 那么当前只是在run hook中保留这个函数做的事情
> 但是需要看一下
> 这里的1和2

此前关于配置、沙箱写入和自动运行的原话、助手校准与认识时间，完整保留在页末旧记录中。

随后对新版配置与共用脚本作出复述：

> 这个我其实大概了解
> 这里的write config是在安装的时候其实就接触到了
> 也就是在安装的时候
> 这里不单纯只是写一个has completedOnboarding的claude配置以及这里人工同意这件事情
> 第二个是precompact还有post compact
> 然后这里的precompact和post compact都是在做同样的一件事情
> 也就是会运行什么文件
> 但是这个文件其实就是这里的提前写好的
> 我是这么理解的

## 尚不清楚

- 沿用旧记录：用户已概括配置准备与 `sb` 传输；两项确认状态的准确作用、远端写入与真正启动的边界仍待反馈。
- 用户已复述两个事件指向提前放好的同一脚本；安装与运行前配置的时机、同一命令接收不同事件名的区分经助手补充后尚待反馈。统计目录与上限的参数传递也未单独复述。
- CLI 内部读取配置和实际触发 hook 的过程未运行验证；沙箱传输的底层实现不在本轮展开。

<details>
<summary>来源、验证与完整例子</summary>

- 当前源码：`slime/agent/harness/claude_code.py:57–84`，固定版本 `18868a79`；父调用在 `harness/common.py:103–104`。脚本的 stdin 入口见 `harness/compaction.py:71–80`。
- [本轮局部验证](../../../../../../references/hook-preparation-example-18868a79.json)：从当前源码提取原方法，以记录器替代 `sb`，检查脚本源路径、目的路径、完整 JSON、执行参数与 `None` 返回。没有执行 shell、写远端文件或启动 CLI。
- 旧版 `2f231865` 只有两项确认状态且不读取 `ctx`；相关旧结论仅适用于页末旧记录，不能替代本页新版输入输出。
- [本轮形成过程](../../../../../../../step-002-agent-results/04-flow.md#hook-upstream-preparation)；旧版全部来源随下方完整记录保留。
- [共用脚本的复述与阶段澄清](../../../../../../../step-002-agent-results/04-flow.md#write-config-shared-script)。

</details>

<details>
<summary>此前完整函数记录（2f231865；旧图、原话与来源）</summary>

# ClaudeCodeHarness.write_config

- 本次继承：2026-10-23，[Step 7 · 02 完整记录](../../../../../../../step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/harness/claude_code.py:44–55](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L44-L55)，由助手核对。
- 首次接触：Step 7 的 `BaseHarness.run:103`；2026-10-22 首次单独展开。
- 最近认识更新：2026-10-23，用户复述为准备 CLI 配置以便自动运行；仍将写入位置称为“本地”并说“修改 CLI”。助手校准为远端沙箱中的两个 JSON 配置文件，配合启动选项使用，尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：沙箱中的 Claude Code 已安装，`agent` 用户已准备，`run` 刚创建好 `ctx`；启动 CLI 之前，先写入它需要的初始化配置。

2. **具体内容**：把“已完成首次引导”和“已接受绕过权限确认模式”两项状态转成 JSON，嵌入一条 shell 命令，通过 `sb.exec` 写进远端的两个配置文件，并设置归属为 `agent`。正常返回 `None`；当前实现没有读取 `ctx`。

3. **建议构建的心智模型**：

   > `write_config` 为随后启动 Claude Code 准备配置文件，预先记录两项确认状态，避免启动过程等待这些人工确认。
   >
   > 配置在本地组织，写入命令通过已有的 `sb` 在远端执行；完成后返回 `run`，再进入启动步骤。

4. **调用代码**（`BaseHarness.run:103–104`）：

   ```python
   await self.write_config(sb, ctx)
   return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)
   ```

## 本场景的输入与输出

**输入：已有沙箱 `sb` 和本次运行上下文 `ctx`。**

```python
# self：ClaudeCodeHarness
# sb：已安装 CLI、完成用户准备的 E2BSandbox 本地操作对象
# ctx：上一段创建的 HarnessContext；此实现接收它，但不读取字段
await self.write_config(sb, ctx)
```

`ctx` 沿用[上一张类卡片的实例](../../../../../../../step-009-adapter-request-entry/03-long-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)。这次写入的配置是函数内固定的两项，不从 `ctx` 的地址、编号或目录生成。

**输出：正常返回 `None`，配置写入效果留在远端沙箱。**

下面展示正常执行后的预期内容，JSON 为便于阅读换行；没有实际写入远端：

```json
{
  "hasCompletedOnboarding": true,
  "bypassPermissionsModeAccepted": true
}
```

- 相同 JSON 写入 `/home/agent/.claude.json` 和 `/home/agent/.claude/settings.json`；命令直接写入这些文件，不合并旧 JSON。
- 按源码的配置意图，第一项记录首次引导已完成，第二项记录已接受绕过权限确认模式。
- `/home/agent/.claude` 及其内容、`/home/agent/.claude.json` 的属主和属组设为 `agent:agent`，供随后以 `agent` 身份运行的 CLI 使用。

### 本地配置 → 远端文件（44–55）

以下保留完整执行语句，仅省略函数的说明字符串：

```python
async def write_config(self, sb: Sandbox, ctx: HarnessContext) -> None:
    settings = json.dumps({"hasCompletedOnboarding": True, "bypassPermissionsModeAccepted": True})
    await sb.exec(
        "mkdir -p /home/agent/.claude && "
        f"echo {shlex.quote(settings)} "
        "| tee /home/agent/.claude.json /home/agent/.claude/settings.json > /dev/null && "
        "chown -R agent:agent /home/agent/.claude /home/agent/.claude.json",
        user="root",
        check=True,
        timeout=60,
    )
```

- **组织内容**：`json.dumps` 在 Slime 一侧生成 JSON 字符串；`shlex.quote` 将它作为一个完整的 shell 参数嵌入命令。
- **提交命令**：`sb.exec` 将包含 JSON 的命令提交到已有沙箱，以 `root` 身份执行。这里传的是写入命令及其中的配置文本，未把整个 `ctx` 对象发送给 CLI。
- **写入文件**：先创建 `.claude` 目录，再由 `echo ... | tee ...` 将相同文本写进两个文件；`> /dev/null` 丢弃 `tee` 额外输出到标准输出的内容，不影响文件写入。
- **准备归属**：随后 `chown` 设置文件归属。`check=True` 要求检查执行结果，`timeout=60` 是命令的超时参数；失败会向调用方传播异常。
- **返回主线**：本函数没有保存 `exec` 的返回结果，正常结束返回 `None`；回到 `run:104`，随后才调用 `launch_and_wait`。

“无需人工确认”在这里指预先写入这两项状态。后续启动命令另外带有 `-p`、任务 `prompt` 和 `--permission-mode bypassPermissions`；任务提示仍由程序提供。因此，本函数只是自动运行所需的配置准备，不能单凭它推断整次任务无需其他条件即可完成。

## 我的直接表述（原话）

2026-10-22，对本函数的理解（节选）：

> 我的简单理解是把这里关于是否会会自动化的运行什么的设置了
> 然后这里同时在通过sb 传输一系列的配置内容
>
> 这是我的理解
> 写一下cli配置 设置不需要人为给提示 直接全自动执行
> 这是我对于这里的理解
>
> 这里对于harness的write config的理解

2026-10-23，整条启动链的复述节选（完整原话见[本次讨论](../../../../../../../step-008-harness-communication/04-flow.md#launch-restatement-and-http-entry)）：

> 然后是这里的write config
> 这里的write config的内容更多的是吧这里的claude code harness 的cli部分写清楚这里的配置
> 修改本身的cli的部分
> 这里修改的claude本身这里不需要再询问能够自动执行
> 修改本地的一系列配置到这里的settings里面

助手校准：`settings` 字符串在 Slime 一侧构造，`sb.exec` 在远端沙箱写入 `/home/agent/.claude.json` 与 `/home/agent/.claude/settings.json`。这里写配置，不修改 CLI 程序代码；两项状态配合后续 `--permission-mode bypassPermissions` 等启动选项使用。

## 尚不清楚

- 用户已概括配置准备与 `sb` 传输；两项状态的准确作用、远端文件写入与真正启动的边界，本轮补充后尚待反馈。
- 已接上 `run:104` 的 `launch_and_wait`；CLI 内部如何读取这些文件及实际启动表现仍未运行验证。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。方法定义见页首；共同入口见 `harness/common.py:68–70、103–104`。该共同入口声明写配置的职责，具体 JSON 和路径属于 Claude Code 实现；Codex 的配置实现不同，本卡不将两者合并。
- 启动选项与任务提示的来源见 `harness/claude_code.py:24–27、57–58`；本页只用于区分配置和启动，不展开后续执行机制。
- 2026-10-22 提取原始方法，以本地操作记录器代替 `sb.exec`，确认只提交一条命令、包含上述两项 JSON 与两个文件路径，参数为 `user="root"`、`check=True`、`timeout=60`，并正常返回 `None`。传入无字段的占位 `ctx` 仍可完成方法，配合源码确认没有读取它。
- 验证没有执行 shell、写入远端文件或启动 CLI；文件效果按源码命令推导。
- 形成过程：[Step 7 · 配置准备与启动的边界](../../../../../../../step-008-harness-communication/04-flow.md#write-cli-config)。

</details>

</details>
