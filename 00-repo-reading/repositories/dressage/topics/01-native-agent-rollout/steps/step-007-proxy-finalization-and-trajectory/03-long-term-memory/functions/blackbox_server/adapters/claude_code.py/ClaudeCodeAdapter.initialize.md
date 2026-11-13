# ClaudeCodeAdapter.initialize

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../step-006-agent-execution/03-long-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.initialize.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 02-short-term-memory 记录](../../../../../../step-005-agent-registration/02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.initialize.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

[BlackboxServer.register](../../core/server.py/BlackboxServer.register.md) → **本函数** → 返回 register 继续处理。

> 为本次 Claude Code 运行准备配置、目录和本地模型请求代理。

<details>
<summary>函数定位、心智模型与调用处</summary>

- 源码：[claude_code.py:291–321](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L291)。
- 首次单独展开：Step 005，2026-11-07；此前只定位其职责。
- 最近认识更新：用户已将 BindingContext 理解为交给适配器初始化的一组资料；本函数机制尚待本轮反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：BlackboxServer 选中 Claude Code，传入已构造的 BindingContext。
2. **具体内容**：读取配置，准备目录和提示文件，启动本地代理，写配置并检查程序。
3. **建议构建的心智模型**：

   > 输入资料在具体语句中被使用；初始化结果留在对象、文件和代理服务中，正常返回值是 None。

4. **调用代码**：

   ```python
   self._adapter = adapter
   await self._adapter.initialize(new_binding_context)
   self._binding_context = new_binding_context
   ```

调用处 self 是 BlackboxServer；下面函数中的 self 是 ClaudeCodeAdapter。

</details>

## 沿代码看输入怎样被使用、准备结果留在哪里

保留完整函数，只增加阅读注释。先看首次成功初始化的路径：服务已启动，Claude 程序已安装，输入是 BindingContext；不需要先记住示例 ID 或具体目录值。

```python
async def initialize(self, binding_context: BindingContext) -> None:
    # 保留服务端传来的本次运行资料，后续操作还会使用。
    self._binding_context = binding_context
    # 从输入资料中取出后端选项，解析成 Claude Code 配置。
    options = self._parse_options(binding_context.binding.backend_options)
    _validate_claude_code_runtime_options(options)  # 不允许的配置在这里报错。
    self._options = options  # 保存给后续写配置、启动 Claude 时使用。

    # 从输入资料中取得本次文件的根目录；Path 本身不创建目录。
    runtime_dir = Path(binding_context.binding.runtime_dir)
    self._prepare_runtime_dirs(runtime_dir)  # 实际准备配置、日志、临时文件等子目录。
    # 有系统提示配置时准备相应文件；没有时得到 None。
    system_prompt_path = self._prepare_system_prompt(binding_context, options)

    # 使用 context 的上游地址、会话标识等启动沙箱内代理，并等待它可访问。
    # 启动的是本地 RolloutLLMProxy；外部 Dressage Proxy 需已由部署提供。
    await self._start_proxy(binding_context, options)
    assert self._proxy_port is not None  # 辅助方法已保存实际监听端口。

    # 确定本次 Claude 配置文件的路径，再建立配置转换器。
    settings_path = runtime_dir / "home" / ".claude" / "settings.json"
    self._compiler = ClaudeCodeConfigCompiler(
        options=options,
        settings_path=settings_path,
        system_prompt_path=system_prompt_path,
    )
    # 真正把权限、压缩等配置写入磁盘；不是安装 Agent 程序。
    settings_path.write_text(
        json.dumps(self._compiler.build_settings(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 另写一个路径记录文件，内容是 settings.json 的文件路径。
    run_dir = runtime_dir / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "claude_code.settings").write_text(
        str(settings_path), encoding="utf-8"
    )

    # 找到本次使用的 Claude 程序；找不到就清理并报错，不会自动安装。
    executable = options.resolved_executable()
    if self._resolve_executable(executable) is None:
        await self.shutdown()
        raise BackendProcessError(
            f"claude code binary not found. Set CLAUDE_CODE_BIN or install Claude Code. ({executable})"
        )

    # 正常走到这里，隐式返回 None；结果已保存在对象、文件和代理服务中。
    # 返回 BlackboxServer.register，继续保存绑定、建立会话并设置 READY。
```

**读完返回**：[BlackboxServer.register](../../core/server.py/BlackboxServer.register.md) 中 await initialize 之后的语句。此时尚未提交题目消息，也尚未完成整个注册流程。

<details>
<summary>按需回查：输入字段与产物的详细对照</summary>

**输入**：一个 BindingContext。继续使用会话 run-a、任务 question-1 的首次注册场景，Claude 程序已经可用，不提供额外系统提示。下面是用到的字段节选，不是完整构造语句：

| 输入字段 | 本例与实际用途 |
| --- | --- |
| binding.backend_options | 例如 max_turns=8；解析并校验，保存为 self._options，供配置及后续运行使用 |
| binding.runtime_dir | 假设为 /workspace_sandbox/blackbox_server_runtime/run-a；本次子目录和文件以此为根 |
| binding.system_prompt | 本例为 None，_prepare_system_prompt 返回 None；有配置时才处理提示文件 |
| binding.router_base_url、router_api_path | 假设指向 http://proxy.example:8800 和 /v1，供本地代理配置上游 |
| binding.bound_session_id、bound_instance_id、bound_sandbox_id | 本次绑定标识，交给本地代理用于后续请求关联 |
| effective_config | Context 的另一顶层字段；本方法没有直接读取它，不能假设所有字段都在此被消费 |

**返回值是 None**。正常结束说明这一段初始化成功；出错则抛异常。实际产物是：

| 产物 | 在哪里 |
| --- | --- |
| 保存的运行资料与配置解析器 | 当前适配器的 _binding_context、_options、_compiler 等字段 |
| 运行目录 | runtime_dir 下的 home/.claude、workspace、logs、run、tmp、prompts |
| Claude 配置 | home/.claude/settings.json；配置内容由 build_settings 产生 |
| 配置路径记录 | run/claude_code.settings，内容是上述 settings.json 的路径 |
| 本地代理及其端口记录 | _start_proxy 启动监听 127.0.0.1 的后台服务任务，并写入 run/proxy.port |

上述路径是固定源码与教学输入的静态推导，没有实际创建文件或启动服务。这里启动的是沙箱内 RolloutLLMProxy，不是外部 Dressage Proxy；未来的模型请求由前者转发给后者。

settings.json 只包含部分配置。比如 max_turns 保存在 options 中，供后续构建 Claude 命令参数使用，不是全部原样写进 settings.json。

</details>

<details>
<summary>按需回查：辅助函数入口与返回位置</summary>

| 入口 | 当前先理解到哪里 | 返回位置 |
| --- | --- | --- |
| [_parse_options](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L486) | 字典转成 ClaudeCodeBackendOptions；无效配置会报错 | 校验并保存 options |
| [_prepare_runtime_dirs / _prepare_system_prompt](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L496) | 准备子目录；按配置处理提示文件 | 进入本地代理启动 |
| [_start_proxy](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L609) | 读取上游地址和绑定标识，启动本地监听并等到健康响应 | 构造 settings_path |
| [ClaudeCodeConfigCompiler.build_settings](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L166) | 生成要写入 settings.json 的字典 | settings_path.write_text |

先沿本函数把输入与产物对上，不因出现这些名字就全部建卡。

</details>

<details>
<summary>原话、尚不清楚的内容与源码依据</summary>

## 我的直接表述（原话）

此前对输入的理解：

> 这里我可以理解为了building context就是需要哦交给adapter用来initialize的一系列东西?

本轮请求：

> 好的那么我们通过构建这个claudecodeadapter initialize的short term memory来完成对于这里的理解吧?

这是对输入关系的初步理解与建卡请求，不表示已经掌握本函数内部。

## 尚不清楚

- Context 中的字段怎样映射到具体代理选项和 Claude 配置，当前仅按用处定位。
- 本地代理的完整请求转发、重试和失败清理，尚未展开。
- Claude 接到题目后怎样启动并产生结果，属于后续执行路径。

<details>
<summary>来源与验证</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 输入结构：core/models.py 的 BindingContext/BindingInfo；产物：adapters/claude_code.py 的 initialize 及表内辅助方法。
- 安装属于运行前的部署前置：仓库 Docker 路径由 [docker/build.sh](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docker/build.sh#L24) 执行构建，[Dockerfile:39](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docker/Dockerfile#L39) 下载并执行 Claude 安装脚本，程序随构建结果进入运行镜像。它不是 initialize 中的一次调用；其他 provider 的模板准备不能自动等同于这条 Docker 路径。
- [本步过程](../../../../../../step-005-agent-registration/04-flow.md)。仅静态核对，没有调用初始化、安装程序或启动网络服务。

</details>

</details>
