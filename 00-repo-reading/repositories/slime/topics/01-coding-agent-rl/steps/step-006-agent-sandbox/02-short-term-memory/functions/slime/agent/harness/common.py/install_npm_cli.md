# install_npm_cli

- 源码定位：[slime/agent/harness/common.py:125–151](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L125-L151)，由助手核对。
- 首次接触：Step 5，在 `ClaudeCodeHarness.install_cli` 中定位，2026-10-22 接续展开。
- 最近认识更新：2026-10-22，用户已复述本机材料上传后通过远端命令完成安装，并将 `for` 理解为退出码与尝试次数的控制。Node 与 CLI 包的处理差别、重试范围由助手进一步细分，尚待反馈。

**2026-10-24 当前版本接续**：本函数现在位于 [common.py:129–155](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L129-L155)，`install_node22` 位于 `158–182`；两者与旧版 AST 均相同，原有安装理解可复用。本步未设置 Claude Code 的 native 包，调用从 `boot_agent_sandbox:135 → ClaudeCodeHarness.install_cli:50–55` 进入，完成后回到 `boot_agent_sandbox:143`。

本步当前传入 Sunabako 对象，沿同一 Sandbox 接口交付本机包文件、执行节点上的安装命令；接口规定 `write_file` 接收主机 `Path`，Sunabako 再委托其 SDK。下面保留原 E2B 场景、`2f231865` 行号和已有原话，作为这份公共安装实现的完整例子；E2B 的内部上传细节不直接作为 Sunabako SDK 的证据。本轮只核对接口与调用，没有新增安装运行。见[本轮收束与版本核对](../../../../../../04-flow.md#agent-sandbox-closure-18868a79)。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据当前 Claude Code 路径、调用代码和输入输出整理，作为理解参考。

1. **使用场合**：`ClaudeCodeHarness.install_cli` 已选好两份安装包路径与检查命令，把它们交给本函数，为已创建的沙箱准备 CLI。

2. **具体内容**：先准备远端的 Node 22，再把本机的 Claude Code npm 包上传到远端 `/tmp/harness-cli.tgz`，在沙箱中执行 npm 安装和检查，等待完成后返回。

3. **建议构建的心智模型**：

   > 本机提供安装材料，`install_npm_cli` 组织“上传文件 → 在同一远端沙箱中安装 → 检查结果”。
   >
   > 上传后得到的是包文件；远端执行安装命令后，才得到可运行的 CLI。成功返回 `None`，安装效果留在沙箱中。

4. **调用代码**（`claude_code.py:37–42`：调用方怎样传入参数）：

   ```python
   await install_npm_cli(
       sb,
       node_runtime=Path(os.environ[self.node_tarball_env]),
       npm_package=Path(os.environ[self.cli_tarball_env]),
       check_cmd="ls -la /usr/local/bin/claude && /usr/local/bin/claude --version",
   )
   ```

   这段调用用于交代参数来源。当前阅读的实现是 `common.py::install_npm_cli`，其函数体按下方三个阶段展开。

## 本场景的输入与输出

本例用 Claude Code 展示公共安装函数的一次调用，沿用此前的教学路径。两份本机文件均未实际读取；以下环境变化是依据源码描述的正常成功路径。

**输入：同一个已就绪的沙箱、两份本机包文件的路径、一条检查命令。**

| 参数 | 本例传入什么 | 调用方从哪里取得 |
| --- | --- | --- |
| `sb` | 前面已进入的 `cand`，即 [E2BSandbox 本地对象](../../../../../classes/slime/agent/sandbox.py/E2BSandbox.md)，用于操作已有远端沙箱 | `boot_agent_sandbox` 创建并进入的对象；沿用 `image="example-image"` 场景 |
| `node_runtime` | `Path("/host/packages/node22.tar.xz")`，本机的 Node 运行包 | `SLIME_AGENT_NODE_TARBALL` 环境变量 |
| `npm_package` | `Path("/host/packages/claude-code.tgz")`，本机的 Claude Code npm 包 | `SLIME_AGENT_CC_TARBALL` 环境变量 |
| `check_cmd` | `"ls -la /usr/local/bin/claude && /usr/local/bin/claude --version"` | Claude Code 的 `install_cli` 指定 |

这里的“本机”指运行 Slime 这段 Python 的主机。调用方先从环境变量取字符串并转成 `Path`；缺少相应变量会在调用方报错。传入本函数后，才继续读取、上传文件内容。

**输出：返回 `None`；同一远端沙箱中增加可用的 Node 和 Claude CLI。**

```text
远端沙箱中的正常成功结果：
  /opt/node22/                已展开的 Node 运行文件
  /usr/local/bin/node、npm、npx  指向上述运行文件的链接
  /usr/local/bin/claude       npm 安装后可执行，并通过指定检查
```

返回后，`ClaudeCodeHarness.install_cli` 也返回 `None`，再回到 `boot_agent_sandbox:115` 的 `sb = cand`。继续使用原沙箱对象，版本文本不作为本函数的返回值。

### 1. 本机 Node 包 → 远端 Node 运行环境（135）

```python
await install_node22(sb, node_runtime)
```

- **已有材料**：`node_runtime` 指向本机包文件。本例是 `.tar.xz`，子函数先在本机去掉 `.xz` 压缩层，得到可上传的 tar 文件；其中的运行文件随后在远端展开。
- **跨到远端**：子函数通过 `sb.write_file` 把文件上传为沙箱中的 `/tmp/node22.tar`。
- **远端准备**：再通过 `sb.exec` 在沙箱内把 tar 展开到 `/opt/node22`，创建 `node`、`npm`、`npx` 的命令链接并检查版本。完成后回到本函数，才开始处理 CLI 包。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [install_node22，154–178](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L154-L178)：本机解压、上传、远端展开 | 沙箱已有 Node 和 npm，继续 137 行上传 CLI 包；本轮只接清这三项动作 |

### 2. 本机 CLI 包 → 远端包文件（137）

```python
await sb.write_file("/tmp/harness-cli.tgz", npm_package)
```

- **第一个参数是远端目的地**：`/tmp/harness-cli.tgz` 在沙箱的文件系统中。
- **第二个参数是本机来源**：`npm_package` 是 `Path`；`E2BSandbox.write_file` 会打开本机文件，把文件内容交给 SDK 上传。CLI 的 `.tgz` 包直接上传，本地不先解压它。
- **这一行完成后的变化**：远端多了一个包文件。安装动作在下一段发生，本机源文件继续保留。

### 3. 远端包文件 → 安装并检查 Claude CLI（138–146）

以下裁剪出首次执行成功的路径，暂时省略重试循环和失败分支；命令与实参保留原文。

```python
install_cmd = "npm install -g --prefix=/usr/local --no-audit --no-fund /tmp/harness-cli.tgz && " + check_cmd
exit_code, last_log = await exec_and_wait(
    sb, cmd=install_cmd, user="root", time_budget_sec=300, tag="harness-npm-install"
)
if exit_code == 0:
    return
```

- **先在本机组装字符串**：赋值给 `install_cmd` 还没有执行安装。
- **再把命令交给远端执行**：`exec_and_wait` 通过 `sb` 在同一沙箱里运行该命令，并等待结果。npm 从沙箱内的 `/tmp/harness-cli.tgz` 安装 CLI，安装前缀为 `/usr/local`。
- **安装成功后检查**：命令中的 `&&` 接上 `check_cmd`，因此 npm 成功后才执行 Claude 文件与版本检查。
- **把结果交回调用方**：`exit_code == 0` 时本函数返回 `None`；`last_log` 是辅助结果，不会被本函数返回。这里仅为后续运行 Agent 做准备。

外层 `for`（141–151）控制这条安装及检查命令的重试边界：

- 退出码只分为 **零与非零**：零表示成功并立即返回；非零都进入相同的重试判断，没有针对各个错误码分别处理。
- `NPM_INSTALL_RETRIES = 3`，`attempt` 依次为 `0、1、2`。还有下一次机会时分别等待 2 秒、4 秒；三次都返回非零退出码，最后抛出 `RuntimeError`。
- 每次重跑的是 `install_cmd`。Node 准备和 CLI 包上传位于循环之前，重试继续使用同一份沙箱和已上传的包。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [exec_and_wait，sandbox.py:82–145](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L82-L145)：怎样执行并等待命令 | 用退出码判断成功或重试；后台执行、轮询与标记文件的实现留待独立问题 |

## 我的直接表述（原话）

先前关于安装位置的疑问：

> 好的 我简单理解就是在远端已经有一个沙箱的情况下
> 给出一个本地的node还有还有要安装的npm package
> 然后直接把这个claude 在这里的这个sandbox上安装上？
> 这是我的理解？
> 也就是把这个node 和cli包直接发送给这里的沙箱还是在沙箱里面安装 我不是特别理解
> 以及这里的具体的桉树调用是否应该需要额外再看一下这里的common里面的install npm cli呢

随后明确本次应阅读的实现：

> 虽然这里具体调用的代码是claudecode harness install cli
> 但是claude的只是类似于穿了一个参数
> 具体的实现需要看一下这里的common才对啊

对上传、远端安装与循环的进一步复述：

> 好的那么我可以理解为这里是本地准备好了之后先解压 然后把这个文件写到远端
> 然后通过执行的方式把这里的指令执行了
> 让这个包在远端能够做到正确的安装
> 我这里对于这个内容的理解
> 下面的for 更多的是对于各种exit code和attempt的边界的把握

## 尚不清楚

- 已复述上传与远端安装的主线；Node 与 CLI 包的处理差别、零与非零退出码的分支及重试范围已补说明，尚待进一步反馈。
- `exec_and_wait` 怎样等待较长的安装任务，以及安装重试与外层重建沙箱怎样配合，本轮未展开。
- 本机两份安装包怎样准备、实际版本是什么，以及真实运行时的安装输出，尚未核实。

<details>
<summary>来源、验证与完整例子</summary>

- Slime 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：调用见 `claude_code.py:36–42`；本函数见 `harness/common.py:125–151`；Node 准备见 `154–178`。
- 上传文件内容的依据是 [E2BSandbox.write_file 的 Path 分支，342–358](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L342-L358)。远端命令通过 `E2BSandbox.exec:309–340` 交给 SDK 的 `commands.run`。
- 失败边界：次数与间隔常量见 `harness/common.py:38–39`。上述重试针对返回的非零退出码；前置准备、上传或 `exec_and_wait` 直接抛出的异常向外传播。此处未展开完整恢复机制。
- 本轮只静态核对源代码、调用参数与路径流向；未上传文件、安装 CLI 或运行真实沙箱。
- 原始问题、解释与阅读边界见 [Step 5 · 上传与远端安装](../../../../../../04-flow.md#upload-and-remote-install)。
- 最初的入口选择与用户原话见 [Step 5 · 从沙箱对象进入 CLI 安装](../../../../../../04-flow.md#install-cli-entry)；将安装主记录集中到本卡的依据见 [Step 5 · 参数适配与公共安装实现](../../../../../../04-flow.md#common-install-primary-record)。
- 本次复述及边界澄清见 [Step 5 · 安装主线与重试范围](../../../../../../04-flow.md#install-restatement-and-retry-boundary)。

</details>
