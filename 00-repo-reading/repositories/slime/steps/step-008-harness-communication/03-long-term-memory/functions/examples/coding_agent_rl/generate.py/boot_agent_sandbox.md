# boot_agent_sandbox

- 源码定位：[examples/coding_agent_rl/generate.py:95–134](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L95-L134)，由助手核对。
- 首次接触：此前在 Coding Agent 整体骨架中定位；Step 5，2026-10-22，开始独立函数记录。
- 最近认识更新：2026-10-22，用户在读过本地对象、远端申请与 CLI 安装后表示基本完成对本函数的理解，并提出总结 task flow；底层等待、并发与故障恢复仍保留为未知。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`generate` 已登记会话配置，接下来需要执行沙箱，供工作区准备、Agent 运行和 diff 提取共同使用。

2. **具体内容**：用 `image` 构造 `E2BSandbox`，进入远端环境并安装所选 Harness 的 CLI；准备成功后通过 `yield sb` 交给调用方，调用方退出上下文时再回收。`instance_id` 只用于本函数的失败日志；它不决定沙箱 ID。准备阶段还带有限流与失败重试。

3. **建议构建的心智模型**：

   > `boot_agent_sandbox` 管理一段执行沙箱的使用期：进入时准备好环境与 CLI，交出可操作沙箱的 `sb`；调用方使用结束后，再尝试回收环境。
   >
   > 它负责准备、交付与回收。工作区准备、运行 Agent 和提取 diff 由拿到 `sb` 的调用方继续组织。

4. **调用代码**（[generate.py:203–213](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L203-L213)，节选）：

   ```python
   async with boot_agent_sandbox(md["image"], instance_id) as sb:
       await swe.prepare_workspace(sb, md["workdir"], md)
       ...  # 调用方接着运行 Agent、提取 diff，之后才离开这个块
   ```

## 本场景的输入与输出

沿用 Step 4 的 [md 教学示例](../../../../../../step-005-agent-preparation/references/metadata.md)。镜像名与题目编号均为占位值；本例假定创建和 CLI 安装成功，未连接真实远端沙箱。

**输入：本次调用显式传入两个字符串。**

```python
image = "example-image"     # 来自 md["image"]
instance_id = "issue-123"   # 来自 md["instance_id"]
```

- `image` 交给 `E2BSandbox(image)`，用于申请对应环境。
- `instance_id` 用来标注准备失败的日志；执行会话的 `session_id` 没有传入本函数。
- 函数另使用已有配置：`HARNESS_CLS` 选择 CLI 实现，`_BOOT_SEM` 限制准备并发，`CONFIG.boot_retries` 限制尝试次数。本场景沿用 `ClaudeCodeHarness`，假定其安装依赖已配置。

**输出与状态变化：按调用、进入、退出三个时机看。**

| 时机 | 得到什么或发生什么 |
| --- | --- |
| 调用 `boot_agent_sandbox(image, instance_id)` | `@asynccontextmanager` 提供一个异步上下文管理器；这时还没有创建沙箱 |
| 成功进入 `async with ... as sb` | `as sb` 接住一个 `E2BSandbox` 对象：`sb.image == "example-image"`，`sb._sb` 保存操作远端的本地 SDK 客户端对象，`sb.sandbox_id` 保存 SDK 返回的编号；CLI 已完成安装 |
| 调用方离开 `async with` | 调用并等待 `sb.__aexit__(None, None, None)`，尝试回收对应远端环境；正常退出后调用方继续向下执行 |

这里交出的是可操作远端沙箱的本地对象，文件和进程在远端。具体 SDK 对象与 `sandbox_id` 未取得，不把题目编号 `"issue-123"` 当作沙箱编号。退出回收也不会把本地对象的这些字段清空。

对象本身的字段、`cand → _sb → 远端环境` 的关系与操作入口统一见 [E2BSandbox 类卡片](../../../../classes/slime/agent/sandbox.py/E2BSandbox.md)。读完接回下面的准备阶段：把就绪的同一个 `cand` 交给 CLI 安装，再保留为 `sb`。

### 函数内部怎样完成这次准备与交付

下面按两个职责段阅读，保留真实调用参数。第一段是一次成功尝试的教学裁剪，重试与异常包装在后面的折叠说明中；代码片段不能单独运行。

#### 1. 镜像 → 准备好的沙箱对象（106–115）

```python
cand = E2BSandbox(image)                     # 106
async with _BOOT_SEM:                        # 108
    await cand.__aenter__()                  # 109
    await HARNESS_CLS().install_cli(cand)     # 111
sb = cand                                   # 115
```

- **`image` → `cand`**：先构造本地对象并保存镜像等配置；远端环境在下一行进入操作中申请。
- **`cand.__aenter__()` → 对象就绪**：在同一个对象中保存 SDK 对象与沙箱 ID。本处没有用赋值接收它的返回值，后续继续使用已更新的 `cand`。
- **`install_cli(cand)` → CLI 就绪**：把同一个沙箱交给当前 Harness。Claude Code 的方法选择参数并委托 `common.py::install_npm_cli` 完成安装，成功后返回 `None`，效果留在沙箱环境中。
- **`sb = cand` → 保留准备结果**：两个变量指向同一个对象，没有再建第二份沙箱。
- **离开 `_BOOT_SEM` → 释放准备名额**：限流覆盖进入环境与安装 CLI，后面调用方使用 `sb` 时已离开这个限流块。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [E2BSandbox.__aenter__](../../../slime/agent/sandbox.py/E2BSandbox.__aenter__.md)：怎样申请环境并保存 SDK 对象 | 继续把 `cand` 交给 `install_cli`；旧卡使用评测场景的 `ev`，本页是执行场景的 `cand`，复用的是同一方法 |
| [install_npm_cli](../../../slime/agent/harness/common.py/install_npm_cli.md)：安装主记录；[ClaudeCodeHarness.install_cli](../../../slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md) 是传参入口 | 安装及检查完成后执行 `sb = cand`；命令等待的内部机制按需展开 |

#### 2. 准备结果 → 调用方使用 → 退出回收（131–134）

```python
try:
    yield sb                                # 132
finally:
    await sb.__aexit__(None, None, None)      # 134
```

- **`yield sb` → 调用处的 `as sb`**：交出上一段准备好的对象，本函数暂停；随后执行 `generate:204–213` 的缩进块。
- **调用方使用期间 → 保留这份环境**：工作区准备、Agent 运行和 diff 提取都使用它。它们写在调用方，不是 `yield` 后立刻执行回收。
- **调用方离开上下文 → `finally`**：正常结束或块内异常退出时，进入这里并等待回收方法。正常路径随后到 `generate:215`；块内异常不会因这个 `finally` 自动变成成功。
- **退出回收 → 保留责任边界**：`__aexit__` 请求 SDK 销毁远端环境；它会记录捕获到的回收错误，因此完成退出处理不等于已确认远端销毁成功。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [E2BSandbox.__aexit__](../../../slime/agent/sandbox.py/E2BSandbox.__aexit__.md)：SDK 回收与日志处理 | 等待退出完成，调用方继续正常流程或原有异常传播；旧卡的评分结果不属于本函数的输出 |

<details>
<summary>准备失败时怎样处理（103–130）</summary>

- `for attempt in range(CONFIG.boot_retries)` 限定准备的总尝试次数，每次构造一个新的 `cand`。
- CLI 安装抛出 `BaseException` 时，先等待该候选沙箱的 `__aexit__`，再重新抛出；外层只捕获 `Exception`，记录带 `instance_id` 的日志并等待后续尝试。不能把所有取消都理解成普通失败重试。
- 某次准备成功后，`sb = cand` 并 `break`；只有这份成功结果会被 `yield` 交出。
- 在配置允许至少一次尝试的前提下，若始终未成功，重新抛出最后一次异常，调用方的 `async with` 块不会开始。

本页只说明本函数的失败策略。SDK 内部重试、限流调度与取消细节仍留待独立问题；不据此推断所有故障都能成功回收。

</details>

## 我的直接表述（原话）

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

完整原话与助手对客户端、地址和连接的澄清见[本轮展开](../../../../../../step-006-agent-sandbox/04-flow.md#sandbox-client-and-address)；后续反馈按实际表达追加在下面。

读过 CLI 安装后，用户对本函数整体理解的反馈：

> 好的 我觉得我这里基本上完成了这里对于boot agent sandbox的理解了
> 你觉得目前这里还有什么需要具体考虑的吗？
> 还是可以完成对于这一步的task flow总结了呢？

本次反馈与按 scope 收束的依据见 [Step 5 · 准备、交付与回收总结](../../../../../../step-006-agent-sandbox/04-flow.md#agent-sandbox-flow-closure)。

## 尚不清楚

- 安装材料、上传与远端安装已集中到 `install_npm_cli` 记录；命令等待和完整失败恢复机制尚未展开。
- 并发限流、重试参数与取消交错的完整行为尚未展开。
- 本场景没有真实 SDK 对象、沙箱编号或远端安装结果；已有进入、退出卡片也不能代替本次真实运行。
- 实际部署使用的服务地址与 E2B SDK 版本尚未取得；本轮已核对官方 SDK 的地址配置与客户端关系，未展开网关内部路由。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，`generate.py:45–52、95–134、203–215`；对象状态见 `sandbox.py:174–189、281–307`，CLI 入口见 `claude_code.py:36–42`。
- 局部验证：Python 3.12.3 下提取原 `boot_agent_sandbox`，保留真实 `asynccontextmanager` 与信号量，用沙箱、安装和等待的替身核对四条路径：正常使用、调用方块内异常、首次安装失败后成功、安装尝试耗尽。确认进入前不创建环境、交出同一对象、使用期间已释放准备名额、退出与错误传播顺序。未连接远端、安装真实 CLI 或运行 Agent；没有验证取消交错和 SDK 故障。
- 形成过程：[Step 5 · 从 scope 进入函数记录](../../../../../../step-006-agent-sandbox/04-flow.md#boot-agent-sandbox-function-card)。整体定位与后续范围仍见 [scope](../../../../../../step-006-agent-sandbox/01-scope.md)。
- 客户端与地址补充：本地 `sandbox.py:174–189、238–300、309–339`；外部 E2B SDK 固定提交 `f0c19af61d0845c53f4255cc1ebf79014fb9a883`。Slime 的 `requirements.txt:6` 只列 `e2b`，当前检查的 Python 环境未安装它，外部源码不能充当本机部署版本。详细源码链接与边界保存在[本轮展开](../../../../../../step-006-agent-sandbox/04-flow.md#sandbox-client-and-address)。

**书上怎么说**：`@asynccontextmanager` 示例中，`yield` 的值绑定给 `async with` 的 `as` 变量。依据 A。

**我的判断（本书未覆盖）**：本函数交出的是已准备好的 `E2BSandbox`；具体准备、重试与回收由 Slime 源码决定。当前 Python 3.12 的 [contextlib.asynccontextmanager](../../../../../../../../../../../../../../usr/lib/python3.12/contextlib.py)实现与本地验证用于核对进入和退出时机。

**依据 A**：《Fluent Python》第 2 版，第 21 章，`Asynchronous Generator Functions` 中的 “Asynchronous generators as context managers”。本书基于 Python 3.10；本次核对环境为 Python 3.12.3。

- 英文：[ch21.md:1111–1387](../../../../../../../../../../../../.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/en/ch21.md:1111)，锚点 `asynchronous-generator-functions`。
- 中文：[ch21.md:1077–1332](../../../../../../../../../../../../.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/zh/ch21.md:1077)，同一锚点，21.10.1 异步生成器函数。
- 原文：The value of `data` will be bound to the `data` variable after the `as` clause in the `async with` statement below.
- 对照：`data` 的值将绑定下方 `async with` 语句中 `as` 子句的 `data` 变量。

</details>
