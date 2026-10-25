# 05 · 任务链路：准备、交付与回收执行沙箱

> `boot_agent_sandbox` 接住任务镜像和当前 Harness，创建执行环境并准备 CLI，再把同一个沙箱操作对象交给调用方。调用方使用期间环境继续保留；离开上下文时，按配置保存产物并请求回收。

[本步 scope](01-scope.md) · [步骤入口](README.md) · [函数记录](02-short-term-memory/overview.md) · [本次收束](04-flow.md#agent-sandbox-closure-18868a79) · [旧版完整总结](references/task-flow-at-2f231865.md)

## 1. 本步在任务中的位置

- **前序准备**：Step 005 已登记本次会话；题目信息提供 `image` 与 `instance_id`，调用方已有当前 `harness`，另传 `trace=base_sample` 记录执行过程。
- **当前入口**：`_generate:283` 进入 `async with boot_agent_sandbox(...) as sb`。本页沿 Sunabako 默认后端、Claude Code 的 npm 安装路径，假设首次准备成功。
- **交付与结束**：环境和 CLI 准备好后交出 `sb`；执行环境的使用期覆盖工作区准备、Agent 运行、统计与补丁收集，离开上下文后才回收。

`instance_id` 用于失败日志；实际 `sandbox_id` 来自创建后的 SDK 对象。模型会话配置仍属于 Adapter，与沙箱的执行环境分别管理。

## 2. 已读部分怎样完成准备、交付和回收

以下按 `18868a79` 的真实调用归属排列，省略限流、追踪和失败重试。第 4 项交出对象后，本函数暂停；第 5 项在调用方离开上下文时才执行。

```text
_generate:283 进入 async with boot_agent_sandbox(...)
└─ boot_agent_sandbox [generate.py:111–164]
   ├─ 1. cand = create_sandbox(image) [121]
   │  └─ SunabakoSandbox.__init__ [sunabako_sandbox.py:21–27]
   │     → 创建本地操作对象，初始化包含镜像在内的六个字段
   ├─ 2. await cand.__aenter__() [132]
   │  └─ SunabakoSandbox.__aenter__ [35–82]
   │     → 查节点和镜像配置，调用 SDK 创建环境
   │     → 保存 _sandbox、sandbox_id 与运行方式，返回同一个对象
   ├─ 3. await harness.install_cli(cand) [135，本例已传入 harness]
   │  └─ ClaudeCodeHarness.install_cli [claude_code.py:50–55，npm 分支]
   │     └─ install_npm_cli [harness/common.py:129–155]
   │        ├─ install_node22 → 准备 Node 运行环境
   │        ├─ sb.write_file → 上传 CLI 包
   │        └─ exec_and_wait → 在环境中安装并检查 CLI
   │     → 返回 None，安装效果留在同一个环境中
   ├─ 4. sb = cand；yield sb [143、161]
   │  → _generate:283 的 as sb 接住对象，执行调用方的使用代码
   └─ 5. 调用方离开上下文，进入 finally [162–164]
      └─ SunabakoSandbox.__aexit__ [84–103]
         → 启用时保存指定产物，再通过 SDK 请求回收
         → 正常退出后回到 _generate:301 的独立评测
```

各处记录：[外层编排](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md) · [初始字段](02-short-term-memory/functions/examples/coding_agent_rl/sunabako_sandbox.py/SunabakoSandbox.__init__.md) · [环境进入](02-short-term-memory/functions/examples/coding_agent_rl/sunabako_sandbox.py/SunabakoSandbox.__aenter__.md) · [CLI 参数入口](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md) · [公共安装主记录](02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md) · [退出回收](02-short-term-memory/functions/examples/coding_agent_rl/sunabako_sandbox.py/SunabakoSandbox.__aexit__.md)。

安装主线此前已读；本轮核对 `install_npm_cli`、`install_node22` 和 Claude Code 的 npm 委托均与旧版相同。安装卡保留原 E2B 完整例子，并注明本步当前的 Sunabako 接口场景；旧后端的内部实现不作为新后端的证据。

## 3. 交出的是什么，使用到什么时候

交给 `as sb` 的是原来的 `cand`：本地 Sunabako 操作对象，持有 SDK 入口和沙箱编号，对应环境中已有可用 CLI。它会继续供以下调用共同使用。

```python
# 教学裁剪：省略多数参数、追踪、外层超时与失败处理。
async with boot_agent_sandbox(...) as sb:              # 283：接住已就绪的对象
    baseline = await swe.prepare_workspace(...)       # 285：准备任务工作区
    agent_exit_code = await harness.run(...)          # 287：运行 Agent
    agent_metrics = await harness.collect_metrics(...)  # 296：收集统计
    diff_text = await swe.git_diff(...)               # 298：取得补丁
# 离开上下文，回到 boot_agent_sandbox:164 请求回收。
reward, applied_cleanly = await swe.run_evaluation(...)  # 301：独立评测
```

- **取得对象与使用结束是两个时刻**：`yield` 交付后环境仍在使用；提取补丁后才离开这个上下文。上述调用只定位使用期，本页不展开它们的内部。
- **保存产物有条件**：只有启用 `SUNABAKO_ARTIFACTS` 才保存指定的运行记录与日志，不是保存整个环境。普通保存错误之后仍尝试回收；回收本身可能失败。
- **结果可以继续交接**：正常路径下，统计与 `diff_text` 已被调用方取回，退出后可继续使用；本地对象的字段不会因退出自动清空。环境是否仍可用不能仅凭字段是否存在判断。

## 4. 本步的收束与后续衔接

按本步 scope，已经接清“镜像输入 → 环境与 CLI 就绪 → 交出 sb → 调用方使用 → 退出回收”，可以收束当前主线。用户已复述外层职责及 Sunabako 的三个阶段；此前的 npm 安装理解继续保留。保存条件、部分异常与具体状态交接仍以卡片中的实际反馈为准，不扩大为全部实现已掌握。

以下问题留待需要时展开：SDK 的通信和节点部署、native 安装分支、命令等待、完整限流／重试／取消交错，以及真实环境的安装与回收验证。它们不改变本轮已经接清的正常交接。

下一候选是接回已有 **Step 007 的 `swe.prepare_workspace`**：入口为 `_generate:285`，要回答“已有可执行命令的沙箱，怎样准备成这道题的工作区”。这里仅标出候选，本轮没有开始 Step 007 的新版阅读或继承更新。

<details>
<summary>源码、历史与验证范围</summary>

- 当前固定提交：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。
- [准备、交付与退出：generate.py:110–164](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L110-L164)；[调用方使用期：283–306](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L306)。
- [工厂：sandbox.py:8–16](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16)；[Sunabako 初始化、进入和退出：21–103](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L21-L103)。
- [CLI 安装分支：claude_code.py:38–55](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L38-L55)；[公共安装：common.py:129–182](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L129-L182)。
- 旧 `2f231865` 总结完整保存在[历史稿](references/task-flow-at-2f231865.md)。E2B、安装旧例和进入本步时的长期记忆保留各自来源，本次不重写历史快照。
- 本轮用 AST 比较确认两个公共安装函数及 npm 委托未变；此前父函数的四条替身路径和三张 Sunabako 方法卡的静态核对仍归属原记录。本轮没有新增真实沙箱、CLI、模型或评测运行。
- 形成依据：[外层职责复述](04-flow.md#boot-lifecycle-restatement)、[三个方法的复述与澄清](04-flow.md#sunabako-lifecycle-restatement)、[本次收束](04-flow.md#agent-sandbox-closure-18868a79)。

</details>
