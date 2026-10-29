# E2BSandbox

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../../02-rollout-reward/steps/step-011-generate-and-rm-group/03-long-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/03-long-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/sandbox.py:160–387](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L160-L387)，由助手核对；记录对象是 Slime 的封装类。
- 首次接触：Step 2，2026-10-21，在评测环境的进入与退出中接触；Step 5 首次独立整理类卡。
- 最近认识更新：2026-10-22，用户在阅读类卡后表示基本理解 `cand` 与 E2BSandbox，并要求接着看 `install_cli`；这是对对象模型的整体反馈，不代表底层 SDK 与通信细节全部掌握。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、源码和本页对象状态整理，作为理解参考。

1. **使用场合**：`boot_agent_sandbox` 为 Agent 准备执行环境时创建该类的实例；此前 `_grade_scaleswe` 也使用同一个类创建独立的评测环境。

2. **具体内容**：保存镜像、规格、存活时间等配置；进入后持有 E2B SDK 客户端与沙箱 ID，通过它们提供执行命令、读写文件和回收环境的接口。

3. **建议构建的心智模型**：

   > `E2BSandbox` 是 Slime 操作一份远端沙箱的本地入口。它先保存环境配置，进入时申请远端环境并保存 SDK 客户端；后续操作通过这个客户端发送，文件和进程留在远端。
   >
   > `cand` 指向这个类的实例，`cand._sb` 指向它持有的 SDK 客户端。两个对象都在运行 Slime 的 Python 进程中。

4. **调用代码**（[generate.py:106–111](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L106-L111)，只摘出对象构造、进入与交接，省略限流和异常包装）：

   ```python
   cand = E2BSandbox(image)
   await cand.__aenter__()
   await HARNESS_CLS().install_cli(cand)
   ```

## 本场景的输入与输出

承接 [boot_agent_sandbox](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md) 的执行场景，沿用教学镜像名。以下是静态推导，没有申请真实沙箱。

**输入：构造时传入镜像字符串。**

```python
image = "example-image"
```

调用处只传 `image`。类还支持 `timeout`、`image_metadata_key`、`rpc_retries`、`size` 四个可选关键字参数；本例均未传。为展示具体状态，假设 `SLIME_AGENT_SANDBOX_IMAGE_METADATA_KEY=image`，其余相关环境变量及旧名称均未设置，采用源码默认值。

**输出：`E2BSandbox(image)` 得到一个本地实例；进入成功后仍使用同一个实例。**

| 实例字段 | 构造完成后 | `__aenter__` 成功后 |
| --- | --- | --- |
| `cand.image` | `"example-image"` | 保留 |
| `cand.image_metadata_key` | `"image"` | 保留 |
| `cand.size` | `"md"` | 保留 |
| `cand.timeout` | `3600`，远端环境存活时间，单位秒 | 保留 |
| `cand.rpc_retries` | `6`，RPC 尝试次数配置 | 保留 |
| `cand._sb` | `None` | 操作这份远端环境的本地 `e2b.AsyncSandbox` 客户端 |
| `cand.sandbox_id` | `""` | 从 SDK 客户端读取的沙箱编号，具体值未取得 |

- **构造 → 保存配置**：此时还没有远端环境；`image` 是环境标识，`image_metadata_key` 是向网关传递它的键名。
- **进入 → 补齐操作入口**：`__aenter__` 用配置申请环境，将返回的客户端保存进 `_sb`，再保存 ID，并返回同一个对象。创建失败时抛出异常，不能把它当作已就绪。
- **返回调用方 → 继续使用**：当前调用没有接收 `__aenter__` 的返回值，直接将已更新的 `cand` 交给 CLI 安装。安装由调用方另行组织，`__aenter__` 本身不安装 CLI。

### 本地对象与远端环境

```text
运行 Slime 的 Python 进程
  cand → E2BSandbox 实例
          ├─ image 等配置
          ├─ sandbox_id
          └─ _sb → E2B AsyncSandbox 客户端
                     └─ 网络请求 → 远端沙箱中的文件与进程
```

- **地址从哪里来**：Slime 这段创建调用不显式传 URL，由 SDK 配置决定。前轮核对的官方 SDK 支持 `E2B_API_URL`、`E2B_DOMAIN`，认证使用 `E2B_API_KEY`；创建响应与连接配置共同用于定位具体沙箱。详细规则和版本边界见[地址与客户端的展开](../../../../../../../../01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#sandbox-client-and-address)。
- **操作怎样过去**：例如 `cand.exec(cmd)` 内部调用 `cand._sb.commands.run(...)`，SDK 发送请求并接收结果。创建成功提供后续访问所需的信息；每次远端操作仍需通信，不能据此假定一条永久连接。`_rpc_retry` 负责调用与重试，实际请求由 SDK 发出。
- **退出后怎样看对象**：`__aexit__` 尝试销毁远端环境，但不会清空本地 `_sb` 或 ID。保留这些字段不证明远端仍可用，也不证明销毁一定成功。

### 操作入口：需要时再进入对应实现

| 入口 | 接收什么，交回什么或改变什么 | 继续查哪里 |
| --- | --- | --- |
| `__aenter__` | 已保存的配置 → 申请环境、更新 `_sb` 与 ID，返回 `self` | [已有进入卡片](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md) |
| `exec` | 命令与执行选项 → 远端执行，返回 `(exit_code, stdout, stderr)` | [源码 309–340](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L309-L340) |
| `write_file` | 远端路径与内容（字符串、字节或本地 `Path`）→ 写入远端文件，返回 `None` | [源码 342–378](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L342-L378) |
| `read_file` | 远端路径 → 文件文本；当前实现捕获普通异常时返回空字符串 | [源码 380–387](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L380-L387) |
| `__aexit__` | 退出时调用 → 尝试回收远端环境，返回 `None`，捕获到的回收错误记日志 | [已有退出卡片](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md) |

这是一组能力入口，不代表按表格顺序执行。已有进入、退出卡片采用评测场景的 `ev`；此处采用执行场景的 `cand`，复用同一类的方法，不是共用同一次运行中的远端沙箱。其余方法本轮只定位职责与接口。

读完回到 [boot_agent_sandbox 的准备阶段](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md)，继续理解它如何将这个对象交给安装过程，再通过 `yield sb` 交付调用方。

## 我的直接表述（原话）

2026-10-22 对本地对象和远端创建的复述节选：

> 我可以理解这里对应的创建一个e2b的本地对象
> 我也了解在aenter的时候这里在对象就绪的情况下aenter
> 通过rpc call 在远端创建了一个沙箱对象

对 `_sb` 与后续通信的追问节选：

> 以及这里直接把这个外部的sandbox直接保存在了本地的_sb里面的话
>
> 后续是对这个sandbox直接操作了？ 把动作直接传输到这里的sandbox？
> 因为已经通过rpc建立好了通信？

在讨论类卡与方法卡分工后，确认创建：

> 好的那么做一个这样子的卡片吧

完整追问见[原始讨论](../../../../../../../../01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#sandbox-client-and-address)。上述确认针对记录方式。

阅读类卡后的反馈节选：

> 好的 我基本上理解了
> 那么现在进入下一个部分吧
> 我清楚了这里的can和这里的e2bsandbox

完整反馈与后续入口见[从沙箱对象进入 CLI 安装](../../../../../../../../01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#install-cli-entry)，原话中的 `can` 按上下文对应 `cand`；底层 SDK 机制仍保留为未知。

## 尚不清楚

- 实际部署的 SDK 版本、服务地址和沙箱编号尚未取得，没有真实远端运行证据。
- SDK 与网关内部如何路由、连接怎样复用，以及重试与取消的完整行为尚未展开。
- `exec`、读写文件的具体实现与失败处理，本页只给操作入口；CLI 安装转入 [common.py::install_npm_cli 主记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)，下层机制按需继续。

<details>
<summary>来源、验证与完整例子</summary>

- Slime 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：`sandbox.py:160–205` 的配置与构造、`273–387` 的进入退出及操作接口；当前调用是 `generate.py:106–111`。本轮静态核对字段、默认值、方法入口与返回类型，没有新增远端实验。
- 地址与客户端沿用前轮核对的 E2B 官方提交 `f0c19af61d0845c53f4255cc1ebf79014fb9a883`，具体源码链接见[当时的证据](../../../../../../../../01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#sandbox-client-and-address)。Slime 依赖未锁定 `e2b` 版本，外部源码不能充当实际部署版本。
- 既有进入、退出卡片及其局部验证一并保留；`boot_agent_sandbox` 的四条替身验证不代表真实远端创建、安装或销毁成功。
- 格式沿用 [Session 类卡片](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/classes/slime/agent/adapters/common.py/Session.md)；本次[建卡与分工记录](../../../../../../../../01-coding-agent-rl/steps/step-006-agent-sandbox/04-flow.md#e2b-class-card)保存用户确认和引用调整。

</details>
