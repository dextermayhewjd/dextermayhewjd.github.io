> 2026-10-24 单场景重排前的完整卡片，源码基准为 `18868a79`。正文保留，仅调整相对链接。

# boot_agent_sandbox

- 源码定位：[examples/coding_agent_rl/generate.py:110–164](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L110-L164)。
- 首次接触：此前在 Coding Agent 整体骨架中定位；Step 5，2026-10-22 开始独立记录，旧编号保留历史语境。
- 最近认识更新：2026-10-22，用户在旧版 E2B 场景下表示基本理解准备、交付与回收；底层等待、并发和故障恢复仍有未知。
- 本轮源码校准：2026-10-24，更新工厂、Harness、追踪、限流与退出调用；[旧版完整卡片](boot-agent-sandbox-at-2f231865.md)保留。版本核对不改变个人认识日期。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_generate` 已登记会话，接下来准备供工作区、Agent 运行和结果收集使用的执行沙箱。
2. **具体内容**：按镜像与后端配置创建沙箱对象，进入环境并安装当前 Harness 的 CLI；成功后交出同一个对象，调用方退出上下文时请求回收。准备阶段有可选的并发限制、追踪和有限重试。
3. **建议构建的心智模型**：

   > 管理一次执行环境的使用期：准备好沙箱与 CLI → 交给调用方使用 → 使用结束后回收。

4. **调用代码**（`_generate:283–298`，省略追踪包装与后续调用）：

   ```python
   async with boot_agent_sandbox(md["image"], instance_id, harness=harness, trace=base_sample) as sb:
       baseline = await swe.prepare_workspace(sb, md["workdir"], md)
       ...  # 继续运行 Agent、收集统计和补丁，完成后离开这个块
   ```

## 本场景的输入与输出

沿用 [md 参考](../../step-005-agent-preparation/references/metadata.md) 的 `image="example-image"`、`instance_id="issue-123"`。两者都是构造值；这里假设镜像、后端及安装材料已配置好，第一次准备就成功，没有创建真实沙箱。

| 输入或条件 | 本例怎样使用 |
| --- | --- |
| `image` | 传给 `create_sandbox`，由后端用于准备执行环境 |
| `instance_id` | 用于本函数的失败日志，标识题目；不生成沙箱 ID |
| `harness` | 调用方已选择的 ClaudeCodeHarness 对象；本例未指定 native 安装包，沿 npm 路径 |
| `trace` | 调用方传来的 `base_sample`，作为追踪上下文；内部追踪实现暂不展开 |
| 后端与启动配置 | 未指定提供方时默认 Sunabako；准备并发默认不限制，总尝试次数默认 2，本例首次成功 |

**交付与状态变化：分清调用、进入和退出。**

| 时机 | 得到什么或发生什么 |
| --- | --- |
| 调用 `boot_agent_sandbox(...)` | `@asynccontextmanager` 提供异步上下文管理器；函数体尚未开始准备沙箱 |
| 成功进入 `async with ... as sb` | 接到准备好的沙箱对象，本例为 SunabakoSandbox；它可以操作执行环境，CLI 已安装。`sb` 与成功的 `cand` 是同一个对象 |
| 调用方离开 `async with` | 等待 `sb.__aexit__(*sys.exc_info())` 处理退出；正常退出后继续后面的评测 |

`sb` 是本地的操作对象，沙箱 ID 与内部客户端由后端建立；这里没有取得真实 ID。E2B 是可选分支，其旧版 `_sb` 字段不能直接套到 Sunabako 对象上。

### 1. 按配置选择沙箱对象（121）

```python
cand = create_sandbox(image)  # 把镜像交给工厂，取得本次候选沙箱对象
```

- `create_sandbox` 读取 `SWE_SANDBOX_PROVIDER`：默认构造 SunabakoSandbox，值为 `e2b` 时构造 E2BSandbox。
- 这里先得到本地对象。让对应执行环境就绪的动作在下一段 `__aenter__` 中完成。

| 需要时进入 | 返回后继续 |
| --- | --- |
| [create_sandbox:8–16](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16) | 接住 `cand`，继续 `boot_agent_sandbox:132` 的进入操作 |

### 2. 进入环境并准备 CLI（132–143）

以下为一次成功路径的教学裁剪：省略追踪、限流和失败包装，保留真实调用及同一对象的交接。

```python
await cand.__aenter__()  # 在这个对象中建立可操作的执行环境
await (harness or HARNESS_CLS()).install_cli(cand)  # 使用调用方传入的 Harness，缺省时采用默认实现
sb = cand  # 保留成功的同一个对象，准备交出
```

- 本处不接收 `__aenter__` 的返回值，后续继续使用已经就绪的 `cand`。
- `install_cli` 的效果留在执行环境中。Claude Code 的当前实现可走 native 包或 npm 安装路径；本例沿用 npm 路径。
- 配置了并发限制时，名额覆盖环境进入与 CLI 安装，交出 `sb` 前已释放。具体控制和失败分支见下方说明。

| 需要时进入 | 返回后继续 |
| --- | --- |
| [SunabakoSandbox.__aenter__](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L35-L82)；E2B 分支可回顾[已有进入卡片](../03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md) | `132` 完成后，将同一个 `cand` 交给 `135` 的安装方法 |
| [ClaudeCodeHarness.install_cli](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L38-L55)；npm 路径复用[公共安装记录](../02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md) | 安装完成后执行 `sb = cand`，再到 `161` 交付 |

### 3. 交给调用方使用，退出时回收（160–164）

```python
try:
    yield sb  # 交到调用处的 as sb，随后暂停本函数
finally:
    with trace_span(trace, "sandbox_cleanup", record_error=False) if trace else nullcontext():
        await sb.__aexit__(*sys.exc_info())  # 离开上下文时，把当前异常信息交给后端
```

- `yield sb` 把对象交给 `_generate:283` 的 `as sb`；本函数暂停，调用方在 `285–298` 行使用它准备工作区、运行 Agent 并收集结果。
- 调用方离开上下文后，才继续 `finally`。正常离开时 `sys.exc_info()` 为三个 `None`；异常离开时包含异常类型、对象和 traceback。
- 回收动作由具体后端完成。正常退出后回到 `_generate:301` 的评测；后端若抛出或转换异常，则按其实际行为向外传播，不能仅凭调用了退出方法认定远端回收成功。

| 需要时进入 | 返回后继续 |
| --- | --- |
| [SunabakoSandbox.__aexit__](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L84-L103)；E2B 分支可回顾[已有退出卡片](../03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md) | 等待退出处理，回到调用方后续代码或异常传播 |

<details>
<summary>准备阶段的限流、追踪与失败边界（118–159）</summary>

- `CONFIG.boot_retries` 控制总尝试次数，当前默认 2。每次先构造新的 `cand`；成功后保存到 `sb` 并跳出循环。
- `create_sandbox(image)` 在本轮尝试的 `try` 外。工厂构造本身抛出的错误，不属于后面的 `except Exception` 重试范围。
- `SWE_BOOT_CONCURRENCY` 默认 0，此时 `_BOOT_SEM=None`；配置正数时，在进入环境前取得名额，并在进入／安装段的 `finally` 中释放。它不限制调用方持有沙箱的整个使用期。
- CLI 安装抛出 `BaseException` 时，先等待当前候选的退出处理，再抛出。外层只捕获 `Exception`，因此不能把取消一概当作可重试的普通失败。
- 捕获到普通异常后记录题目编号并等待下一次尝试；始终未成功时抛出最后异常，调用方的 `async with` 正文不会开始。进入阶段部分失败的资源处理仍要按具体后端核对。
- `trace_span` 包装等待、创建、安装、退避与回收阶段；`trace=None` 时采用空上下文。本轮只保留追踪位置，内部机制不展开。

</details>

## 我的直接表述（原话）

以下是原 E2B 场景中的阅读记录，继续保留其版本语境；本轮代码校准不代替新的理解反馈。

建卡时的要求：

> 好的那么这里把这个boot agent sandbox 给分析一下吧
> 单独创建一个function 的short term memroy吧

这次要求确认了阅读对象与记录方式。随后对本地对象与远端创建的复述节选：

> 我可以理解这里对应的创建一个e2b的本地对象
> 我也了解在aenter的时候这里在对象就绪的情况下aenter
> 通过rpc call 在远端创建了一个沙箱对象

随后追问节选：

> 但是一个问题是
> 这里的沙箱对象的远端的地址是在哪里配置好的吗？
> 以及这里直接把这个外部的sandbox直接保存在了本地的_sb里面的话
>
> 后续是对这个sandbox直接操作了？ 把动作直接传输到这里的sandbox？
> 因为已经通过rpc建立好了通信？

完整原话与助手对客户端、地址和连接的澄清见[本轮展开](../04-flow.md#sandbox-client-and-address)；后续反馈按实际表达追加在下面。

读过 CLI 安装后，用户对本函数整体理解的反馈：

> 好的 我觉得我这里基本上完成了这里对于boot agent sandbox的理解了
> 你觉得目前这里还有什么需要具体考虑的吗？
> 还是可以完成对于这一步的task flow总结了呢？

本次反馈与按 scope 收束的依据见 [Step 5 · 准备、交付与回收总结](../04-flow.md#agent-sandbox-flow-closure)。

## 尚不清楚

- 新版工厂选择与 Sunabako 的内部对象、部署配置、镜像映射和进入／退出细节，尚未独立展开。
- 安装材料与远端安装的旧认识保留；新增 native 分支、命令等待和完整失败恢复仍需按问题回查。
- 并发、重试、取消交错与部分创建失败的完整清理行为尚未验证。
- 没有本次真实沙箱 ID、服务地址或安装结果；旧 E2B SDK 版本与地址的疑问继续保存在原记录中。

<details>
<summary>源码、历史与验证范围</summary>

- 当前固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[完整函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L110-L164)、[调用与使用期](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L306)。
- [工厂与默认后端](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16)、[启动配置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L97-L106)。
- E2B 进入／退出与公共 npm 安装实现已在本轮版本比较中核对 AST 未变；旧卡保留原版本行号。当前 npm 函数位置为 [common.py:129–155](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L129-L155)。
- 本轮提取当前原始函数，以真实 `asynccontextmanager` 和信号量配合沙箱、安装、追踪及等待替身，核对正常使用、调用方异常、安装失败后重试成功、尝试耗尽四种路径：进入前不执行准备，交出同一对象，使用前释放准备名额，退出时转交调用方异常信息。
- 上述验证只覆盖父函数的控制流，没有选择或创建真实后端，没有上传安装包、发送 HTTP 或运行模型。实际 SDK 失败和取消交错仍属未知。
- [本轮更新记录](../04-flow.md#boot-card-refresh-18868a79) · [此前完整卡片](boot-agent-sandbox-at-2f231865.md)。旧版实验、书籍语法来源和 SDK 阅读依据仍保留在此前记录中。

</details>
