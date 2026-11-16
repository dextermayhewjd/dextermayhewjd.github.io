# ClaudeCode.run

- 源码：[claude_code.py:2120–2233](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/claude_code.py#L2120)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独展开：Step 014，2026-11-13。
- 最近认识更新：2026-11-13，用户已概括通过 Claude CLI 组织执行，并控制输出格式与保存位置；具体执行后端和日志解析仍未展开。

[Trial._run_agent_phase](../../../trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-mainline) → **当前 ClaudeCode.run** → exec_as_agent（在环境内执行命令）→ 返回执行阶段。

这里的 `self` 是 Harbor 的 `ClaudeCode` 实例，由 Harbor Trial 创建；与 Topic 01 的 `ClaudeCodeAdapter` 属于两条执行路线。[两种 Agent 接入的分工](../../../../../../../../README.md#agent-execution-ownership)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：上层已选中 ClaudeCode，传入题目、可用环境和执行记录。
2. **具体内容**：准备配置与目录，把题目送入 Claude CLI，等待执行并将输出写入环境日志。
3. **建议构建的心智模型**：

   > Python 组织启动命令，环境执行 Claude CLI；先留下日志，后续再从日志补充执行记录。

4. **调用代码**（_run_agent_phase:769–776 中的实际委派，外层等待包装略）：

   ```python
   await run(  # 普通分支中，run 绑定到当前 ClaudeCode 实例的 run。
       instruction=instruction,
       environment=self.agent_environment,
       context=target.agent_result,
   )
   ```

## 本场景的输入与输出

输入仍是同一份题目、环境与 AgentContext；本轮普通执行，`self._resume=False`、`self._load=False`。装饰器先调用 render_instruction 处理题目模板，当前不展开模板机制。

<a id="claude-run-mainline"></a>

### 1. 启动前已有的配置

源码 2125–2192 准备 `env`（认证、模型、会话目录）、`setup_command`（建目录并按需注册 skills/memory/MCP）和 CLI flags，再在环境中执行准备命令。下面只保留交接；具体拼接见折叠源码。

```python
await self.exec_as_agent(environment, command=setup_command, env=env)
await self._upload_base_settings(environment)  # 接着上传本次需要的基础设置。
```

<a id="claude-request-routing"></a>

### 请求目的地从哪里来 · 当前回查

在更早的 [运行 Job 之前](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#run-job)，plugin.on_job_start 调用 _inject_agent_routing 修改每份 Agent 配置。Anthropic 分支节选如下，模型覆盖等细节暂略：

```python
env.update({
    "ANTHROPIC_API_KEY": token_template,    # Gateway 用这个路由身份区分不同尝试。
    "ANTHROPIC_AUTH_TOKEN": token_template,
    "ANTHROPIC_BASE_URL": advertise_url,   # 把模型请求的目的地设为 Gateway 地址。
})
agent.env = env  # 这里改的是 Agent 配置；随后由 Harbor 的 Agent 用于 CLI 执行。
```

```text
Claude CLI --HTTP--> Gateway --进程内分派--> 对应的 RolloutLLMProxy.app
```

Gateway 从请求头取路由 token，找到预先登记的 binding，再调用 binding.proxy.app。这个 proxy 在尝试开始时注册、在 AGENT_START 时激活；HTTP 是通信方式，目的地和分派由上述配置与代码决定。这里不是 Gateway 再通过 HTTP 请求另一个 RolloutLLMProxy 服务。

已进入 [_inject_agent_routing 函数卡](../../../../dressage/integrations/harbor/plugin.py/_inject_agent_routing.md#inject-routing-mainline)，接清地址/token 写入配置，以及 Harbor 创建 Agent 时怎样解析；Gateway 的接收与分派仍待后续。

### 2. 题目进入 CLI，输出写入日志

源码 2201–2220，保留实际命令拼接，只补关键注释。

```python
# 题目先放入一个临时命名的环境变量，shell 再通过 stdin 交给 Claude。
instruction_shell_var = f"claude_code_instruction_{uuid.uuid4().hex}"
instruction_env_var = instruction_shell_var.upper()
run_env = {**env, instruction_env_var: instruction}

await self.exec_as_agent(
    environment,
    command=(
        'export PATH="$HOME/.local/bin:$PATH"; '
        f'{instruction_shell_var}="${instruction_env_var}"; '
        f"unset {instruction_env_var}; "
        f'printf "%s" "${instruction_shell_var}" | '
        f"claude --verbose --output-format=stream-json "
        f"{settings_flag}"
        f"{extra_flags}"
        f"{resume_flag}"  # 本轮普通执行，不带 continue/resume。
        f"--print 2>&1 | tee "  # 合并标准错误；保存文件并保留标准输出流。
        f"{(self.environment_logs_dir / 'claude-code.txt').as_posix()}"
    ),
    env=run_env,
)
```

`--print` 采用非交互执行，`--output-format=stream-json` 让 CLI 输出流式 JSON；日志文件在目标环境中。是否把输出继续展示到本地控制台，由环境执行层决定。

### 3. 正常返回与执行记录

本函数正常返回 None，输出先保存在环境里的 `claude-code.txt` 及会话目录中；这里的函数体没有直接写入 `context`。后续[外层 _run_agent 的输出同步](../../../trial/single_step.py/SingleStepTrial._run_agent.md#run-agent-mainline)在记录为空时，会尝试解析日志、构建轨迹并补充 AgentContext。不能把“接口收到了 context”理解为本方法已经填好它。

可选自定义 settings 的清理在本函数 finally 中；当前只认收尾用途。正常结束后回到[执行阶段](../../../trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-mainline)，再走结束记录与回调。

<details>
<summary>完整函数：认证与模型、目录与扩展注册、CLI flags、恢复分支和设置清理</summary>

```python
@override
@with_prompt_template
async def run(
    self, instruction: str, environment: BaseEnvironment, context: AgentContext
) -> None:
    env = self._resolve_auth_env()
    max_output_tokens = os.environ.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS")
    if max_output_tokens:
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = max_output_tokens

    # Handle model name based on whether using custom API base or Bedrock
    resolved_model = self._resolved_model_name()
    if resolved_model:
        env["ANTHROPIC_MODEL"] = resolved_model

    # Default custom-endpoint model aliases while preserving user overrides.
    if "ANTHROPIC_BASE_URL" in env and "ANTHROPIC_MODEL" in env:
        env.update(self._model_alias_env(env["ANTHROPIC_MODEL"], all_aliases=True))

    # Disable adaptive thinking if requested
    if os.environ.get("CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING", "").strip() == "1":
        env["CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING"] = "1"

    # Disable non-essential traffic (telemetry, etc.)
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"

    # Allow bypassPermissions mode when running as root inside containers
    env["IS_SANDBOX"] = "1"

    # Merge declarative env vars (e.g. MAX_THINKING_TOKENS)
    env.update(self._resolved_env_vars)

    env["CLAUDE_CONFIG_DIR"] = (self.environment_logs_dir / "sessions").as_posix()

    setup_command = (
        "mkdir -p $CLAUDE_CONFIG_DIR/debug $CLAUDE_CONFIG_DIR/projects/-app "
        "$CLAUDE_CONFIG_DIR/shell-snapshots $CLAUDE_CONFIG_DIR/statsig "
        "$CLAUDE_CONFIG_DIR/todos $CLAUDE_CONFIG_DIR/skills && "
        "if [ -d ~/.claude/skills ]; then "
        "cp -r ~/.claude/skills/. $CLAUDE_CONFIG_DIR/skills/ 2>/dev/null || true; "
        "fi"
    )
    if self.config_source is not None:
        setup_command += (
            f" && mkdir -p {shlex.quote(self._REMOTE_SETTINGS_DIR.as_posix())}"
        )

    skills_command = self._build_register_skills_command()
    if skills_command:
        setup_command += f" && {skills_command}"

    memory_command = self._build_register_memory_command()
    if memory_command:
        setup_command += f" && {memory_command}"

    mcp_command = self._build_register_mcp_servers_command()
    if mcp_command:
        setup_command += f" && {mcp_command}"

    cli_flags = self.build_cli_flags()
    extra_flags = (cli_flags + " ") if cli_flags else ""
    settings_flag = (
        f"--settings {shlex.quote(self._REMOTE_SETTINGS_PATH.as_posix())} "
        if self.config_source is not None
        else ""
    )
    resume_flag = "--continue " if self._resume else ""

    await self.exec_as_agent(
        environment,
        command=setup_command,
        env=env,
    )

    if self._load:
        load_session_id = await self._seed_load_trajectory(environment)
        resume_flag = f"--resume {load_session_id} "

    try:
        await self._upload_base_settings(environment)

        instruction_shell_var = f"claude_code_instruction_{uuid.uuid4().hex}"
        instruction_env_var = instruction_shell_var.upper()
        run_env = {**env, instruction_env_var: instruction}

        await self.exec_as_agent(
            environment,
            command=(
                'export PATH="$HOME/.local/bin:$PATH"; '
                f'{instruction_shell_var}="${instruction_env_var}"; '
                f"unset {instruction_env_var}; "
                f'printf "%s" "${instruction_shell_var}" | '
                f"claude --verbose --output-format=stream-json "
                f"{settings_flag}"
                f"{extra_flags}"
                f"{resume_flag}"
                f"--print 2>&1 | tee "
                f"{(self.environment_logs_dir / 'claude-code.txt').as_posix()}"
            ),
            env=run_env,
        )
    finally:
        if self.config_source is not None:
            try:
                await self.exec_as_agent(
                    environment,
                    command=(
                        f"rm -rf "
                        f"{shlex.quote(self._REMOTE_SETTINGS_DIR.as_posix())}"
                    ),
                    env=env,
                )
            except Exception:
                pass
```

</details>

## 我的直接表述（原话）

> 好的 那么我们来看一下这里的这个claude code run吧

本轮职责复述：

> 好的 我的理解就是基于这里的这个claude cli来实现很多具体的这个command
> 包括不限于输出到哪里啊
> 或者这里的这个输出的格式啊一系列的内容
> 好的 我觉得我对于这里的这个内容了解了

助手核对：本函数组装准备命令与 CLI 启动命令，指定执行配置、输出格式和日志位置，再交给环境执行。任务过程中具体如何调用工具由运行起来的 Claude Code 负责。

本轮继续追问请求路由：

> 好的 那么我们继续吧
> 看一下下一步我们需要做什么呢?
> 这里发送的请求会自动从http到gateway 到rolloutllmproxy吗?
> 我不是特别理解

本轮进一步询问组件归属：

> harbor这里的这个agent 是dressage里面的agent吗?
> 我的意思是如果harbor和dressage都有一个agent 那么不就是两个不同的系统了呢?
> 都是agent

## 尚不清楚

- exec_as_agent 怎样把命令交给具体环境执行，按需继续；本轮不下潜具体沙箱后端。
- 模型请求目的地怎样由 env、路由与 Proxy 配置共同决定，后续按本步范围追一条请求。
- CLI 日志、会话轨迹及 Proxy 采集如何对应，具体解析与回调内部仍待回查。

<details>
<summary>来源与验证</summary>

- 本地 `git show v0.25.0:src/harbor/agents/installed/claude_code.py` 核对完整方法；上层是 trial.py:769–776 的调用。
- installed/base.py:178 的 with_prompt_template 先 render_instruction，再调用被包装方法；不会在该包装中填充 context。
- trial.py:1167 的 _sync_agent_output 先取回日志，再由 _populate_agent_context 在记录为空时委派 Agent.populate_context_post_run。ClaudeCode 的该方法位于 1860–1889，尝试转换轨迹、写 trajectory.json 并从 final_metrics 补用量/费用；解析失败时可能不填写，本轮只核对职责。
- 直接依赖 exec_as_agent 位于 installed/base.py:1072；只作下游入口定位，尚未单独建卡。
- CLI 的 stream-json 日志不等于模型服务的原始 API 请求/响应；后者沿路由与 Proxy 另行追踪。
- 路由证据来自 Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`：plugin.py:384–385 调用注入并写回 trial_config.agent；_inject_agent_routing:1031–1074 写入地址/token；gateway.py:594–633 注册 binding，705–708 默认创建 RolloutLLMProxy，864–949 接收 HTTP 并进程内调用 proxy.app。这是源码路径核对，不是 Harbor 0.25 与 Dressage 0.18 约束下的实测连通结果。
- 所有命令仅作为源码展示，没有运行 CLI、安装、删除设置目录或请求模型。[本轮记录](../../../../../../04-flow.md#claude-code-run-entry)。

</details>
