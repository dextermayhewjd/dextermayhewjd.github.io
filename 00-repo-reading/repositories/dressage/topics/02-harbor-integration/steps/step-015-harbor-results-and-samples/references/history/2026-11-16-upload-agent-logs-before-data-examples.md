# Trial._upload_agent_logs

- 源码：[Harbor trial.py · _upload_agent_logs](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L834)，v0.25.0 发布提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独阅读：2026-11-16，Step 015。
- 认识状态：用户明确要分清 Proxy 数据、Agent 日志和任务产物，尚无本函数实现的个人复述。
- 证据：2026-11-16 已从本地 `/home/hongshi/projects/harbor` 复核完整函数与上传辅助方法；HEAD 等于 v0.25.0 发布提交，工作区干净。函数位于 [本地 trial.py:834](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:834)，与本卡代码一致；未运行真实文件传输。

[本步 scope](../../01-scope.md) · [返回 SingleStepTrial._run](../../02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Agent 已执行结束，外层已尝试取回日志并补充 AgentContext。准备收集任务产物、执行评测前，需要让运行环境也能访问本地生成或补充的 Agent 日志。
2. **具体内容**：将本地 agent 日志目录委派给 _upload_role_logs 同步到环境；有 user_agent 时再处理它的日志目录。已挂载同一目录则跳过传输。
3. **建议构建的心智模型**：

   > 把宿主机这边已有的 Agent 日志同步回运行环境。它搬运目录内容，不生成模型概率，也不在这里解析日志或计算评分。

4. **调用代码**（SingleStepTrial._run 节选）：

   ```python
   await self._run_agent()
   await self._upload_agent_logs()  # 当前：本地日志 → 运行环境
   await self._collect_artifacts(
       stop_main_before_sidecars=(mode == VerifierEnvironmentMode.SEPARATE)
   )
   # 后面按评测模式处理环境停止，再调用 _run_verifier。
   ```

## 本场景的输入与输出

### 1. 上传什么：先区分三类资料

| 资料 | 回答什么问题 | 本函数是否负责生成 |
| --- | --- | --- |
| Proxy 的模型交互资料 | 模型收到了什么，生成了哪些 token、概率等 | 否，属于 Dressage 模型请求链路 |
| Agent 日志及本地整理的轨迹 | Agent 执行中发生了什么，怎样组织为可查看的执行记录 | 否，本函数同步已有目录 |
| 任务 artifacts | 任务留下哪些要保留的文件 | 否，后续 _collect_artifacts 负责收集 |

这些是职责区分，内容可能重叠；并不是三种永远互斥的文件格式。

当前 Claude Code 场景的例子：

| 文件或目录 | 来自哪里、表示什么 |
| --- | --- |
| claude-code.txt | CLI 的 stream-json 输出及重定向的标准错误，先写在运行环境中；不是 SGLang 原始 API 响应 |
| sessions/ | Claude Code 使用的会话目录，具体文件由 CLI 产生 |
| trajectory.json | Harbor 可在本地根据日志转换出的执行轨迹；转换成功时才有，不保证每次存在，也不是 Proxy 的 token/logprob 存储 |

**本函数没有固定文件白名单**：它接收整个本地 agent 目录。实际包含什么取决于前面产生、取回和整理了什么，不能说每次必有以上全部文件。

<a id="agent-output-example"></a>

#### 具体例子：按需展开

**先记住：日志记录发生了什么，Agent 轨迹把这些经历组织成步骤，artifacts 保存按约定收集的文件；_sync_agent_output 收回并整理记录，_upload_agent_logs 将本地日志同步回环境。**

下面三个例子使用同一个“修复 calc.py”场景。它们是教学构造，不是真实任务的运行结果。

<details>
<summary>例子 1：展开任务过程，对照 Proxy 记录、Agent 轨迹与文件产物</summary>

下面是教学构造，说明数据关系；不是一次实际运行的输出。任务为“修复 calc.py 的 add，让测试通过”。

```text
Agent 的执行过程
  1. 让模型决定下一步 → 模型提出读取 calc.py
  2. Agent 执行 Read → 得到：return a - b
  3. 再请求模型 → 模型提出替换为 return a + b
  4. Agent 执行 Edit → 得到：修改成功
  5. 再请求模型 → 模型提出运行 pytest
  6. Agent 执行 Bash → 得到：1 passed
  7. 再请求模型 → 回复任务已完成
```

**同一个过程留下三种视角的资料：**

| 观察位置 | 这个例子具体留下什么 | 用来回答什么 |
| --- | --- | --- |
| Proxy 模型交互记录 | 每次送入模型的消息/token、模型生成的文本/token、可用的 logprob 等 | 模型在什么上下文中生成了什么？ |
| Agent 日志/轨迹 | 提出 Read、实际读到的内容；提出 Edit、修改结果；提出 Bash、测试输出；最终回复 | Agent 怎样一步步完成任务，工具返回了什么？ |
| 任务 artifacts | 若收集配置包含 calc.py，就保存修改后的文件；若包含测试报告，也可保存报告 | 最后留下了哪些可检查、交付的文件？ |

Proxy 也可能在下一轮请求消息中看到工具结果，所以不是两份记录内容完全互斥；区别在观察边界和组织方式。Proxy 不亲自执行 Read/Edit/Bash；Agent 的执行记录将工具调用与其返回组织在一起。当前生成路径不要求每个输入 token 都有概率，也不是保存词表中所有候选 token 的完整概率分布。

</details>

<details>
<summary>例子 2：展开一条 Agent 轨迹，看看工具调用与返回结果怎样对应</summary>

**Agent 轨迹不是只记录一句“已完成”，也不是另一份 token 概率表。** 在当前 Harbor Claude Code 转换中，一个步骤可以同时包含 message、tool_calls 和 observation。下面节选模拟“运行测试”这一项，使用转换器的真实字段，省略其他步骤和可选字段；不是完整可验证的轨迹文件：

```json
{
  "step_id": 4,
  "source": "agent",
  "message": "运行测试确认修改。",
  "tool_calls": [
    {
      "tool_call_id": "call-test-1",
      "function_name": "Bash",
      "arguments": {"command": "pytest -q"}
    }
  ],
  "observation": {
    "results": [
      {"source_call_id": "call-test-1", "content": "1 passed"}
    ]
  }
}
```

这里 tool_call_id 与 source_call_id 对上，表示“这个测试输出属于刚才这次 Bash 调用”。上面 1–7 是为读者拆开的执行动作，不表示转换后恰好有七个 Step；转换器可把一轮模型消息及其工具交互归到同一步。

</details>

**再回到你问的 _run_agent 收尾 output：** `_sync_agent_output` 将已经发生的执行整理为 Harbor 可使用的记录。普通路径的职责是：

```text
已有日志在环境里
  → _download_agent_logs：取回或通过挂载共享访问
  → _populate_agent_context：AgentContext 为空时，委派 Agent 整理日志
      → Claude Code 转换成功：写本地 trajectory.json
      → 将 token 用量、费用等摘要补到 AgentContext
  → model_usage 尚缺时，尝试从 trajectory.json 补充
```

这不会再执行 Read/Edit/Bash，也不会重新向模型生成一遍答案。日志是原材料，trajectory.json 是结构化的过程记录，AgentContext 保存本次执行摘要；不能把整个轨迹文件当成已全部塞入 AgentContext。

**随后 _upload_agent_logs 才把本地已有/补充的文件同步回环境。** 所以“收尾 output”与“upload logs”是相邻而不同的职责。

最后，`_collect_artifacts` 可以收集修改后的 calc.py，但不能理解为自动查找并保存所有改动文件：实际收哪些文件取决于约定目录、任务配置与实现。Agent 自己跑出 `1 passed` 也不等于 Harbor Verifier 已完成正式评分。

### 2. 为什么先取回，又上传

沿本轮无 user_agent、非挂载环境的正常路径看职责（同步/转换可能因已有记录而跳过）：

```text
运行环境：Claude Code 执行，写出日志与会话文件
    │
    │ _run_agent 收尾的 _sync_agent_output 尝试取回日志
    ▼
宿主机：本次试次的 agent/ 目录
    │ 可解析日志、补充 AgentContext、生成 trajectory.json
    │
    │ ╔════════════════════════════════════════════╗
    └─║ _upload_agent_logs：把本地日志目录同步回环境 ║
      ╚════════════════════════════════════════════╝
                            │
                            ▼
运行环境：/logs/agent/ 可获得本地补充的文件
    → 回 SingleStepTrial._run，继续产物收集与评测
```

这样运行环境中的后续处理可以访问本地补充的记录；是否有评测脚本实际读取某个日志文件取决于任务。本函数不保证所有 Verifier 都依赖日志。

### 3. 真实函数：选择目录，委派上传

以下完整函数保留实际接口：

```python
async def _upload_agent_logs(self) -> None:
    """Upload locally-generated agent logs back to non-mounted environments."""
    await self._upload_role_logs(
        source_dir=self.paths.agent_dir,
        target_dir=self.agent_env_paths.agent_dir,
    )
    if self.user_agent is not None:
        await self._upload_role_logs(
            source_dir=self.paths.user_agent_dir,
            target_dir=self.agent_env_paths.user_agent_dir,
        )
```

无显式入参，目录来自 self。Linux 场景下的对应关系：

| 路径 | 意义 |
| --- | --- |
| self.paths.agent_dir | 宿主机的 `<trial_dir>/agent/` |
| self.agent_env_paths.agent_dir | 运行环境的 `/logs/agent/` |
| self.paths.user_agent_dir | 若启用模拟用户 Agent，宿主机的 `<trial_dir>/user-agent/` |
| self.agent_env_paths.user_agent_dir | 对应环境的 `/logs/user-agent/` |

user_agent 是另一个可选角色，不表示给每位真实用户上传一份日志。本轮 user_agent 为 None，只走第一个调用。

辅助方法仅需知道：

- 目录已经挂载共享：直接返回，无需重复复制。
- 未挂载共享：调用环境的 upload_dir。
- 上传抛出普通 Exception：辅助方法记录错误，并未在此重新抛出。因此正常返回不能单独证明上传成功。

### 4. 调用前后：一个具体目录例子

<details>
<summary>例子 3：展开上传前后目录，观察 trajectory.json 出现在哪里</summary>

教学构造：假设日志已成功下载、轨迹也已成功转换，Linux 环境且未挂载；文件名来自当前 Agent 用法，目录状态不是实测结果。

```text
调用前
  宿主机 <trial_dir>/agent/       环境 /logs/agent/
    claude-code.txt                claude-code.txt
    sessions/                     sessions/
    trajectory.json               尚无本地补充的 trajectory.json

调用成功后
  宿主机目录仍保留               环境目录也可访问
    claude-code.txt                claude-code.txt
    sessions/                     sessions/
    trajectory.json               trajectory.json
```

</details>

返回值为 None；可观察结果是文件同步副作用，不是日志列表、reward 或 Sample。目录合并/覆盖的细节由具体环境后端实现，本轮不展开。

读完返回 _run，下一处 _collect_artifacts 再回答“任务产物具体收集哪些文件”。

## 我的直接表述（原话）

本轮问题节选：

> 但是目前我们在这里又有一个upload agent logs还有collect artifacts的内容
> 我就比较想要知道这里的这个upload agent logs的部分真的不需要单独拆开看吗？
> 是否需要理解到底每次到底采集收集的内容logs和artifacts到底收集和采集的内容是什么我觉得是比较重要信息？

确认建卡：

> 好的 那么请构建一下这个upload agent logs 这个函数的部分吧

本轮困惑（节选）：

> 那么agent层面执行的轨迹是什么呢？
> 然后最后这里的collect artifact
> 我的理解是这里给出的是具体改动的文件
> 主要是中间的内容

用户明确要求具体 examples；以上修复代码场景为助手教学构造，尚未得到用户理解确认。对 artifacts 的校准是“按配置/约定收集的文件，可以包含改动文件，但不等于自动收集所有改动”。

展示要求（2026-11-16，节选）：

> 然后在那个下面给出可以缩放的例子吧

本轮将“缩放”按 Markdown 的展开/收起组织，保留核心说明与源码默认可见；未改变技术内容或标记掌握。

## 尚不清楚

- 已提供构造例子区分模型交互、工具执行轨迹与文件结果，理解反馈待继续；尚无实际运行样本。
- _collect_artifacts 的配置、目录与产物用途，下一处再看。
- 具体环境后端怎样复制目录、处理同名文件，本轮保留为黑箱。

<details>
<summary>源码、来源与验证边界</summary>

- [固定版 trial.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)：本轮核对 _upload_agent_logs、_upload_role_logs、_download_agent_logs、_sync_agent_output，后两者只作为来源背景。
- [固定版路径定义](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/paths.py)：TrialPaths 与 EnvironmentPaths；上文路径采用 Linux 场景。
- [既有 ClaudeCode.run 记录](../../03-long-term-memory/functions/harbor/agents/installed/claude_code.py/ClaudeCode.run.md)：CLI 文件来源、日志取回与条件式轨迹转换，保留其版本证据与未知。
- [固定版 Claude Code 实现](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/claude_code.py)。
- [本步理解形成过程](../../04-flow.md#upload-agent-logs)。
- 仅静态源码核对；无容器、文件传输、模型或评测运行。当前卡不证明 Harbor 0.25 与 Dressage 锁定的 0.18 运行兼容。

</details>
