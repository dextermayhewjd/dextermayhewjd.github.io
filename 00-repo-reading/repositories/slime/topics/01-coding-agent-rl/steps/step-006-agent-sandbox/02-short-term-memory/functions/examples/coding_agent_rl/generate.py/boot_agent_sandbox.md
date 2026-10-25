# boot_agent_sandbox

- 源码定位：[examples/coding_agent_rl/generate.py:110–164](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L110-L164)。
- 首次接触：此前在 Coding Agent 整体骨架中定位；Step 5，2026-10-22 开始独立记录，旧编号保留历史语境。
- 最近认识更新：2026-10-24，用户以创建、进入和退出概括本函数的职责；具体步骤未逐项复述。旧版理解保留，底层等待、并发和故障恢复仍有未知。
- 本轮源码校准：2026-10-24，更新工厂、Harness、追踪、限流与退出调用；[旧版完整卡片](../../../../../references/boot-agent-sandbox-at-2f231865.md)保留。版本核对不改变个人认识日期。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_generate` 已登记会话，接下来准备供工作区、Agent 运行和结果收集使用的执行沙箱。
2. **具体内容**：按镜像与后端配置创建沙箱对象，进入环境并安装当前 Harness 的 CLI；成功后交出同一个对象，调用方退出上下文时请求回收。
3. **建议构建的心智模型**：

   > 管理一次执行环境的使用期：准备好沙箱与 CLI → 交给调用方使用 → 使用结束后回收。

4. **调用代码**（`_generate:283–298`，省略追踪包装与后续调用）：

   ```python
   async with boot_agent_sandbox(
       md["image"], instance_id, harness=harness, trace=base_sample
   ) as sb:
       baseline = await swe.prepare_workspace(sb, md["workdir"], md)
       ...  # 继续运行 Agent、收集统计和补丁，完成后离开这个块
   ```

## 本场景的输入与输出

沿用 [md 参考](../../../../../../step-005-agent-preparation/references/metadata.md) 中的 `image="example-image"`、`instance_id="issue-123"`。本页采用默认的 Sunabako 后端，假设第一次准备成功；下面始终跟踪同一个 `cand`。值为教学构造，未创建真实沙箱。

- **输入**：镜像 `image`、已经选好的 `harness`；另有题目编号 `instance_id` 用于失败日志，`trace=base_sample` 用于追踪记录。
- **交付**：成功进入 `async with` 后，`as sb` 取得环境与 CLI 都已就绪的沙箱操作对象。
- **退出**：调用方离开这个上下文时，本函数请求后端回收对应环境。

<a id="boot-single-scenario"></a>
<a id="1-按配置选择沙箱对象121"></a>

### 1. 得到 cand：一个沙箱操作对象（121）

进入 `async with` 时，才开始执行下面的准备；仅调用 `boot_agent_sandbox(...)` 得到的是上下文管理器。

```python
cand = create_sandbox(image)  # 根据镜像和后端配置，取得候选沙箱对象
```

**此时的 `cand`**：本地的 SunabakoSandbox 对象，保存了准备所需的信息；下一段才让对应执行环境就绪。

需要展开时进入 [create_sandbox:8–16](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16)；Sunabako 对象的初始字段见 [__init__ 卡片](../sunabako_sandbox.py/SunabakoSandbox.__init__.md)，读完回到下面的 `132` 行。

<details>
<summary>后端选择与已有 E2B 记录</summary>

`SWE_SANDBOX_PROVIDER` 未指定时选择 Sunabako，配置为 `e2b` 时选择 E2B。两种实现都由同一入口创建，但内部字段与 SDK 各自不同；旧版的 `_sb` 字段不能直接套到 Sunabako 上。实际沙箱 ID 由后端建立，本例没有取得真实 ID。

选择 E2B 时可回顾[进入](../../../../../03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)与[退出](../../../../../03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)记录。它们保留旧版来源，具体实现已在本轮核对未变。

</details>

<a id="2-进入环境并准备-cli132143"></a>

### 2. 让同一个 cand 具备运行条件（132–143）

以下是成功路径的源码节选，省略追踪、限流和失败包装。

```python
await cand.__aenter__()  # 让这个对象对应的执行环境就绪
await (harness or HARNESS_CLS()).install_cli(cand)  # 在同一环境中准备 CLI
sb = cand  # 交付前换一个变量名，仍指向同一个对象
```

**此时的 `cand`**：已经能操作执行环境，CLI 也已准备好。`sb` 与它指向同一对象，没有新建第二份沙箱。

需要展开时：[环境进入卡片](../sunabako_sandbox.py/SunabakoSandbox.__aenter__.md)读完回到 `135` 行；[CLI 安装](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L38-L55)读完回到 `143` 行。

<details>
<summary>安装分支与本段的补充说明</summary>

- 本例传入的是 ClaudeCodeHarness，未指定 native 包，沿用 npm 安装；具体材料与安装过程见[公共安装记录](../../../slime/agent/harness/common.py/install_npm_cli.md)。指定 native 包时走另一条安装分支。
- 已传入 `harness` 时使用该对象；否则由 `HARNESS_CLS()` 提供默认实现。
- 本处不接收 `__aenter__` 的返回值，继续使用已就绪的 `cand`；安装效果保存在执行环境中。

</details>

<a id="3-交给调用方使用退出时回收160164"></a>

### 3. 交出 sb，使用结束后回收环境（160–164）

下面只裁掉追踪包装，保留实际的交付与退出调用：

```python
try:
    yield sb  # 交给调用处的 as sb，本函数暂停
finally:
    await sb.__aexit__(*sys.exc_info())  # 调用方离开上下文后，请求回收环境
```

**现在由调用方使用 `sb`**：`_generate:283` 接住这个 `sb`，在 `285–298` 行使用它准备工作区、运行 Agent、收集结果。等调用方离开 `async with`，本函数才从暂停处继续到 `finally`。

回收由 [SunabakoSandbox.__aexit__](../sunabako_sandbox.py/SunabakoSandbox.__aexit__.md)完成；正常退出后回到 `_generate:301` 的评测。

<details>
<summary>退出时的追踪包装、异常信息与完整源码</summary>

```python
try:
    yield sb  # 交到调用处的 as sb，随后暂停本函数
finally:
    with trace_span(trace, "sandbox_cleanup", record_error=False) if trace else nullcontext():
        await sb.__aexit__(*sys.exc_info())  # 离开上下文时，把当前异常信息交给后端
```

正常离开时 `sys.exc_info()` 为三个 `None`；异常离开时包含异常类型、对象和 traceback。后端若抛出或转换异常，按其实际行为向外传播；调用退出方法本身不构成远端回收成功的验证。

</details>

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

<a id="boot-lifecycle-user-restatement"></a>

2026-10-24，重排卡片后的表述：

> 简单来说就是创建一个sandbox之后在进入之后做什么
> 然后在推出的时候做什么事情
> 这是我对于这个boot agent sandbox的理解

环境准备、交给调用方使用及退出回收的源码对应见[本轮澄清](../../../../../04-flow.md#boot-lifecycle-restatement)；助手补充与本次原话分别记录。

<details>
<summary>2026-10-22 原 E2B 场景的表述与后续追问</summary>

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

完整原话与助手对客户端、地址和连接的澄清见[本轮展开](../../../../../04-flow.md#sandbox-client-and-address)；后续反馈按实际表达追加在下面。

读过 CLI 安装后，用户对本函数整体理解的反馈：

> 好的 我觉得我这里基本上完成了这里对于boot agent sandbox的理解了
> 你觉得目前这里还有什么需要具体考虑的吗？
> 还是可以完成对于这一步的task flow总结了呢？

本次反馈与按 scope 收束的依据见 [Step 5 · 准备、交付与回收总结](../../../../../04-flow.md#agent-sandbox-flow-closure)。

</details>

## 尚不清楚

- 用户已初步串起 Sunabako 的字段准备、环境创建与退出；产物保存的条件和范围已补澄清，真实部署配置、镜像材料与 SDK 内部仍未展开。
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
- [本次单场景重排](../../../../../04-flow.md#boot-single-scenario-layout) · [重排前全文](../../../../../references/boot-agent-sandbox-before-single-scenario-layout.md)。
- [本轮更新记录](../../../../../04-flow.md#boot-card-refresh-18868a79) · [此前完整卡片](../../../../../references/boot-agent-sandbox-at-2f231865.md)。旧版实验、书籍语法来源和 SDK 阅读依据仍保留在此前记录中。

</details>
