# 04 · 启动执行沙箱：问题与解释

[本步入口](README.md) · [阅读范围](01-scope.md)

<a id="scope-confirmed"></a>

## 1. 2026-10-22：先建立步骤并明确 scope

前一步提出的入口与理由见 [Step 4 的推荐记录](../step-005-agent-preparation/04-flow.md#boot-agent-sandbox-recommendation)。用户先要求简单构建启动执行沙箱这一步，随后明确：

> 好的那么请简单构建一下这个step吧
> 不需要提前填写过多的信息，例如具体的函数
> 但是需要先把这里的scope弄清楚
> 看一下已有的skill吧

本轮按现有 scope skill 建立三段范围：阅读目标、指挥官函数、核心骨架。保留完整任务位置，仅聚焦 `boot_agent_sandbox` 的正常启动与交接，不预先填写新函数卡片或阅读后的结论。

Step 4 的 `03 + 02` 继承为本步 `03`：30 份函数记录、1 份 Session 类记录。保留原话、认识时间、来源与未知，只调整必要的相对链接；本步 `02` 暂为空索引。

静态核对的入口是 `generate.py:203` 与同文件的 `boot_agent_sandbox:96–134`。本地固定提交仍为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，官方 main 查询为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；未更新源码或运行沙箱。用户确认了本步主题和准备方式，尚未表达对启动实现的理解。

<a id="scope-local-skeleton-correction"></a>

## 2. 2026-10-22：复核 skill，补回本步局部骨架

用户反馈：

> 这里确定正确使用了这个skill吗
> 怎么还是缺少了一点这里的scope应该有的内容呢？

**核对结果**：初稿采用了三段标题、整体骨架和停止位置，但漏掉了本步入口的局部骨架与阅读导航。助手把“不提前填写具体函数”解释得过宽，连 scope 中必要的调用关系也省掉了。[scope skill](../../../../../.agents/skills/repo-reading-scope/SKILL.md)要求提取当前任务的核心调用，并说明返回位置；[Step 003](../step-004-trajectory-to-samples/01-scope.md)和 [Step 004](../step-005-agent-preparation/01-scope.md)已展示“整体定位 → 局部展开”的写法。

本次修正 [scope](01-scope.md#boot-agent-sandbox-local-skeleton)：

- 保留完整七项骨架，在第 2 项下补出创建对象、启动沙箱、安装 CLI、交出 `sb`、退出回收的正常路径，附实际行号。
- 给出阅读导航：进入与退出复用已有卡片；当前 Claude Code 路径的 CLI 安装只定位实现与用途；交付后接回 `generate:203–213`。
- 保留原先的简洁范围，不提前创建新函数卡片或填写阅读后的任务总结。局部骨架是阅读地图，不是用户已经理解的记录。

**方法边界**：现有 skill 的 reference 主要示范 Step 0 的整体骨架，此前提出的[局部导航条件分支](../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#scope-skill-context-branch-proposal)仍未写入 skill。本轮修正当前材料，不将未采用的提案表述为现行条款。

本轮静态核对了固定版本的 `generate.py:96–134、203–215`、`sandbox.py:174–189、281–307` 与 `claude_code.py:36–42`。源码 HEAD 与上节一致，未运行远端沙箱，也未将格式修正记为新函数已读。

<a id="boot-agent-sandbox-function-card"></a>

## 3. 2026-10-22：从 scope 进入 boot_agent_sandbox 的函数记录

用户明确要求：

> 好的那么这里把这个boot agent sandbox 给分析一下吧
> 单独创建一个function 的short term memroy吧

已按短期 memory skill 建立 [boot_agent_sandbox 卡片](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md)。沿用前一步 `md` 示例中的 `image = "example-image"`、`instance_id = "issue-123"`，两者均为教学值。

本轮解释围绕三个区别建立：

1. 调用装饰后的函数先得到上下文管理器；进入 `async with` 后才开始准备环境。
2. `cand` 经进入和安装后仍是同一个对象，`sb = cand` 保存它，再由 `yield sb` 交给调用方；`instance_id` 只用于失败日志，不是会话或沙箱 ID。
3. 调用方使用结束后，才回到 `finally` 等待退出回收。工作区准备与 Agent 运行仍由调用方负责。

卡片按“镜像到准备结果”“交出对象到退出回收”两段组织，均保留代码、分条说明和子函数跳转。进入与退出链接此前累计卡片，注明执行沙箱与旧评测场景的差别；CLI 安装只给实际入口，不新建未展开的子卡。重试策略放在折叠说明中。

**证据范围**：固定源码仍为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`；官方 main 查询为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，未更新 checkout。Python 3.12.3 下提取原函数，用替身核对正常使用、块内异常、安装失败后成功与安装尝试耗尽四条路径；确认进入、同一对象交付、准备名额释放、退出及异常传播的顺序。未运行真实远端沙箱、CLI 或 Agent。语言依据来自本地《Fluent Python》第 2 版对应双语小节与当前 `contextlib` 实现。

用户确认了本次分析和建卡，尚无对本函数的机制复述。本轮不据此标记 Step 5 完成，也不预填阅读后的 task flow。

<a id="sandbox-client-and-address"></a>

## 4. 2026-10-22：本地客户端怎样操作远端沙箱

用户在阅读函数卡片后表示大概理解，继续追问：

> 1.好的 我大概理解了
> 那么看一下这里的内容呢吧
> 我的理解是这里在创建的过程中首先是在cand部分创建了一个沙箱对象
> 然后这里就设计了e2bsandbox的 aenter了对吧
>
> 2.然后这里还有通过使用这个aenter的时候通过rpc来创建一个sandbox
> 但是我其实比较想要知道的内容是
> 这里的cand的部分？
>
> 我可以理解这里对应的创建一个e2b的本地对象
> 我也了解在aenter的时候这里在对象就绪的情况下aenter
> 通过rpc call 在远端创建了一个沙箱对象
>
> 但是一个问题是
> 这里的沙箱对象的远端的地址是在哪里配置好的吗？
> 以及这里直接把这个外部的sandbox直接保存在了本地的_sb里面的话
>
> 后续是对这个sandbox直接操作了？ 把动作直接传输到这里的sandbox？
> 因为已经通过rpc建立好了通信？

这次复述已经区分了本地构造与进入时申请远端环境。新增疑问是：返回本地的到底是什么、怎样知道请求发往哪里、创建是否意味着建立了永久连接。助手据此补充当前 [boot_agent_sandbox 卡片](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md)，不另建 SDK 函数卡或改写前序记忆。

### 先把两个本地对象与远端环境分开

1. `cand = E2BSandbox(image)` 创建 Slime 的本地封装，最初 `cand._sb = None`。
2. `await cand.__aenter__()` 进入这个对象的方法，里面的 `self` 就是 `cand`。它调用 `AsyncSandbox.create(...)`，由 SDK 向服务申请远端环境。
3. 服务返回沙箱编号等信息；SDK 据此构造本地 `AsyncSandbox` 客户端，交给 `self._sb` 保存。保存的是操作入口，远端的文件和进程仍在服务器上。

```text
本地：cand（Slime E2BSandbox）
        └─ cand._sb（E2B SDK AsyncSandbox 客户端）
                   └─ 根据沙箱编号和连接配置发送网络请求 → 远端环境
```

### 地址来自哪里

需要分开“向哪里申请环境”和“操作刚申请的哪一份环境”。本段 Slime 代码只传 `timeout` 和 `metadata`，没有显式传 URL；连接配置交给 E2B SDK。

| 要确定的信息 | 本轮核对的官方 SDK 如何取得 |
| --- | --- |
| 创建沙箱的服务 API 地址 | `api_url` 参数可覆盖；未传时读取 `E2B_API_URL`，再使用默认规则。非 debug 模式下默认是 `https://api.<domain>` |
| 基础服务域名 | `domain` 参数可覆盖；未传时读取 `E2B_DOMAIN`，再用默认的 `e2b.app` |
| 访问服务的认证 | `api_key` 参数或 `E2B_API_KEY`；这是认证信息，不是服务地址 |
| 操作具体沙箱所需的信息 | 创建响应提供 `sandbox_id`、`sandbox_domain` 等信息；SDK 保留它们和连接配置，生成操作地址并设置路由信息。另支持 `E2B_SANDBOX_URL` 覆盖操作地址 |

`image` 表示要启动的环境。Slime 把它写进配置指定的 metadata 键，由兼容网关解释；它不承担服务地址的职责。这里核对的是配置规则，没有读取私有环境文件，也没有取得实际部署的地址或沙箱编号。

### 后续怎样执行动作

以已有 `exec` 接口为例，下面只展示交接，省略参数与重试包装，没有实际执行：

```text
await cand.exec("pwd")
  → cand._sb.commands.run("pwd", ...)
  → SDK 发送命令请求
  → 远端执行 pwd
  → SDK 接收结果
  → Slime 返回 (exit_code, stdout, stderr)
```

因此可以把后续操作理解为“通过本地客户端，把动作发给对应的远端沙箱”。创建成功提供了后续请求所需的身份和连接信息；每个后续动作仍需要相应的网络通信，连接可以复用，也可能重建。Slime 的 `_rpc_retry` 是执行及重试传入操作的包装，不是单独建立通信的 API；`_reset_conn_pool` 的说明也明确下一次请求可以重新连接。

回到 `boot_agent_sandbox`：`__aenter__` 完成后，`install_cli(cand)` 接到的还是这个本地封装，并通过它的操作接口准备远端环境。当前只补齐这层交接，CLI 安装细节仍未展开。

### 证据与范围

- Slime 固定提交仍为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。本地构造见 [sandbox.py:174–189](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L174-L189)，重试、进入与客户端赋值见 [238–300](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L238-L300)，命令转发见 [309–339](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L309-L339)。官方 Slime main 查询仍为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，未更新 checkout。
- E2B 官方 SDK 本次固定到提交 `f0c19af61d0845c53f4255cc1ebf79014fb9a883`。地址配置见 [connection_config.py:223–353](https://github.com/e2b-dev/E2B/blob/f0c19af61d0845c53f4255cc1ebf79014fb9a883/packages/python-sdk/e2b/connection_config.py#L223-L353)；请求创建、读取返回信息并构造本地客户端见 [sandbox_async/main.py:1174–1243](https://github.com/e2b-dev/E2B/blob/f0c19af61d0845c53f4255cc1ebf79014fb9a883/packages/python-sdk/e2b/sandbox_async/main.py#L1174-L1243)；保存状态与生成操作地址见 [sandbox/main.py:35–55](https://github.com/e2b-dev/E2B/blob/f0c19af61d0845c53f4255cc1ebf79014fb9a883/packages/python-sdk/e2b/sandbox/main.py#L35-L55)。
- 后续命令的 RPC 客户端与请求构造见 [sandbox_async/commands/command.py:39–59](https://github.com/e2b-dev/E2B/blob/f0c19af61d0845c53f4255cc1ebf79014fb9a883/packages/python-sdk/e2b/sandbox_async/commands/command.py#L39-L59) 和 [294–345](https://github.com/e2b-dev/E2B/blob/f0c19af61d0845c53f4255cc1ebf79014fb9a883/packages/python-sdk/e2b/sandbox_async/commands/command.py#L294-L345)。
- 版本边界：Slime 的 [requirements.txt:6](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/requirements.txt#L6) 只列 `e2b`，未锁版本；本轮检查的 Python 环境未安装 E2B。以上官方 SDK 是解释机制的外部源码证据，不能当作实际部署的已安装版本；网关内部路由与真实网络请求未验证。

用户原话与助手澄清分别保留；尚无对这次补充解释的反馈，不标记 Step 5 完成。

<a id="sandbox-record-boundary"></a>

## 5. 2026-10-22：对象关系与操作实现怎样分别记录

用户接着询问 E2B 沙箱及其操作是否需要单独的函数卡片。当前建议是为 Slime 的 `E2BSandbox` 建立类卡，承接 `cand`、`_sb` 和远端环境的共用模型；进入、退出复用已有函数卡，执行命令、写文件等方法按实际追问展开。[完整问题与分工建议](../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#e2b-object-card-boundary)保存在制度讨论中。

这次是记录归属的讨论，尚未生成新卡、迁移现有解释或展开新方法，不将建议记作本步已完成或用户已确认。

<a id="e2b-class-card"></a>

## 6. 2026-10-22：确认并建立 E2BSandbox 类卡片

用户认可上一轮的类卡与方法卡分工，要求：

> 好的那么做一个这样子的卡片吧

已建立本步 [E2BSandbox 类卡片](02-short-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)，沿用 Session 的栏目：定位、LLM 四项、场景输入输出、原话、未知和折叠来源。使用相同的 `image = "example-image"` 教学值，分开呈现构造完成与进入成功后的状态，再连接 `cand`、SDK 客户端和远端环境。

- **类卡**保存关键配置与字段、地址来源的简短说明，以及进入、执行命令、读写文件和退出的用途与入口。
- **方法卡**继续复用本步 `03` 中的 `__aenter__`、`__aexit__`，说明旧评测场景与当前执行场景的差别。其他方法只定位，没有预建整套函数记录。
- **父函数卡**保留完整输入输出和准备、交付、回收两段实现；上轮增加的共用对象说明改为链接类卡。第 4 节的原问题、解释与源码依据继续保留。

本轮核对 Slime 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `sandbox.py:160–387` 与 `generate.py:106–111`；官方 main 仍为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，未更新 checkout。字段值按明确的教学环境假设静态推导，外部 SDK 的证据沿用第 4 节的固定提交；未新增真实远端或完整 Agent 运行。

此次确认针对类卡的生成与记录分工，卡片详略和技术解释仍待反馈，不标记 Step 5 完成。

<a id="install-cli-entry"></a>

## 7. 2026-10-22：从沙箱对象进入 CLI 安装

用户反馈并指定接续内容：

> 好的 我基本上理解了
> 那么现在进入下一个部分吧
> 我清楚了这里的can和这里的e2bsandbox
> 我比较想要知道治理和harness_cls相关的install_cli
> 是否应该看一下了呢？

据此将 E2BSandbox 的对象模型记录为用户已基本理解，保留 SDK、连接复用与故障处理等未知。继续同一个 Step 005，进入 `generate.py:111` 的 `HARNESS_CLS().install_cli(cand)`，不另开步骤。

**入口与理由**：此前解决的是怎样获得可操作的环境；下一处直接回答怎样在这份环境中准备 Agent CLI。沿用 Claude Code 路径，`HARNESS_CLS` 由 `generate.py:45–52` 选为 `ClaudeCodeHarness`，因此读 `claude_code.py:36–42` 的具体实现。`BaseHarness.install_cli` 是接口声明；公共安装过程位于 `common.py::install_npm_cli`，两者职责不同。

本轮建立 [ClaudeCodeHarness.install_cli 卡片](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md)，保留以下交接：

1. `sb` 接到刚才已进入的 `cand`，使用同一份沙箱。
2. 从本机环境变量取得 Node 运行包和 Claude Code npm 包的路径，转换为 `Path`；这些是安装材料，不是新的远端地址。
3. 将沙箱、两个路径和 Claude 检查命令交给 `install_npm_cli`。后者负责准备 Node、传包、安装和检查；本轮先接清输入输出，内部机制后续按问题展开。
4. 成功时返回 `None`，变化保留在远端环境中；返回 `boot_agent_sandbox:115` 后继续 `sb = cand`。后续 `run` 才组织具体题目的执行。

**停止位置**：能解释具体 Harness 的选择、安装材料的来路与成功后的环境变化。暂不展开 Node 解压、文件上传、命令等待与重试的完整实现；示例路径未在本机核实，也未实际运行安装。原有完整骨架保留，scope 只更新本行阅读范围与边界。

源码仍为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，官方 main 查询仍为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。本轮静态核对 `generate.py:45–52、109–115`、`claude_code.py:18–20、36–42`、`common.py:63–66、125–151`，没有新增沙箱、CLI 或训练运行证据。用户尚无对本次安装交接的机制复述。

<a id="upload-and-remote-install"></a>

## 8. 2026-10-22：上传安装包与在远端安装是两个动作

用户接着复述并追问：

> 好的 我简单理解就是在远端已经有一个沙箱的情况下
> 给出一个本地的node还有还有要安装的npm package
> 然后直接把这个claude 在这里的这个sandbox上安装上？
> 这是我的理解？
> 也就是把这个node 和cli包直接发送给这里的沙箱还是在沙箱里面安装 我不是特别理解
> 以及这里的具体的桉树调用是否应该需要额外再看一下这里的common里面的install npm cli呢

用户已将已有远端环境与安装材料联系起来，疑问集中在文件传输和安装发生的位置。沿用本步范围，进入 [install_npm_cli 函数卡片](02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)：它组织这两类动作，直接回答当前问题。

**本次源码澄清：先上传包，再在同一远端沙箱里安装。**

1. `node_runtime` 与 `npm_package` 都是运行 Slime 的主机上的包文件路径。`Path` 本身只描述路径，真正上传时才读取文件内容。
2. `install_node22` 先处理 Node 包：本例 `.xz` 在本机解压，tar 上传为远端 `/tmp/node22.tar`，随后在沙箱中展开到 `/opt/node22`，准备命令链接并检查版本。
3. `sb.write_file("/tmp/harness-cli.tgz", npm_package)` 把本机 CLI 包传到远端文件系统；完成后只是有了包文件。
4. 本机组装 `install_cmd`，再由 `exec_and_wait` 把 npm 安装及检查命令交给同一沙箱执行。npm 使用的是刚上传的远端路径；退出码为零时，本函数返回 `None`。
5. 返回 `ClaudeCodeHarness.install_cli`，再回到 `boot_agent_sandbox:115`，接着使用已经准备好的 `cand`。后续 `run` 才进入具体任务的运行。

**记录边界**：新建一张 `install_npm_cli` 卡片，父卡继续保留材料选择和委托关系；Node 准备只解释必要动作，`exec_and_wait` 只接清执行位置、等待与返回值。本轮没有继续展开 SDK 传输、后台执行和轮询的内部机制，也没有为所有辅助函数预建卡片。

证据沿用本地固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：`harness/common.py:125–178`、`sandbox.py:82–145、309–358`、`claude_code.py:36–42`。教学路径沿用上一张卡片，未读取真实安装包、执行上传或运行安装。用户的初步复述和本次助手解释分别保留，后者尚待反馈。

<a id="common-install-primary-record"></a>

## 9. 2026-10-22：参数适配与公共安装实现的主次

用户进一步指出：

> 虽然这里具体调用的代码是claudecode harness install cli
> 但是claude的只是类似于穿了一个参数
> 具体的实现需要看一下这里的common才对啊

源码支持这一判断：`claude_code.py:36–42` 读取两份包路径，指定 Claude 检查命令，调用公共函数；`common.py:125–151` 才组织 Node 准备、CLI 上传、npm 安装、结果检查和重试。这里是方法委托普通函数完成安装，基类的接口声明另在 `common.py:63–66`。

据此调整记录的主次：

- [install_npm_cli](02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md) 是完整安装主记录；保留 Claude Code 调用作为场景输入，补齐环境变量到实参的来源。其“调用代码”用于解释实参，下方三个阶段解释公共函数体。
- [ClaudeCodeHarness.install_cli](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md) 收为引用入口，保留真实源码位置、委托关系、首次接触与认识更新。旧原话和解释仍在本文件第 7、8 节，明确未知归入公共卡片。
- scope、函数索引和父卡直接把安装机制的阅读导向 common；本步范围、整体骨架与前序记忆不变。

本轮仅核对上述固定版本的源码并调整记录，未运行安装。用户这次确认的是实现职责的区分，不据此把上传、等待或重试的内部机制记为已掌握。

<a id="install-restatement-and-retry-boundary"></a>

## 10. 2026-10-22：复述安装主线，细分包处理与重试范围

用户复述：

> 好的那么我可以理解为这里是本地准备好了之后先解压 然后把这个文件写到远端
> 然后通过执行的方式把这里的指令执行了
> 让这个包在远端能够做到正确的安装
> 我这里对于这个内容的理解
> 下面的for 更多的是对于各种exit code和attempt的边界的把握

这次表述已接起“本机材料 → 上传 → 远端命令完成安装”，并识别出循环控制执行结果和尝试次数。助手根据源码进一步细分：

1. Node 示例包是 `.tar.xz`，本机先去掉 `.xz` 压缩层，tar 上传后在远端展开；CLI 的 `.tgz` 包直接上传，再由远端 npm 安装。不能把两种包都理解成本机先解压。
2. 循环只区分零与非零退出码。零立即成功返回，非零采用相同的重试逻辑；`attempt` 从 0 到 2，最多执行三次，有后续机会时等待 2 秒、4 秒，三次都返回非零才抛出最终失败。
3. 重试对象是 CLI 的安装及检查命令。Node 准备和 CLI 包上传已在循环前完成；这些操作以及命令调用直接抛出的异常不属于此处的非零退出码重试。

源码仍为固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `harness/common.py:38–39、135–178`。本次只核对静态分支，未执行真实安装或故障模拟。原话已加入 [install_npm_cli 主记录](02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)；新增的细分解释与用户已表达的理解分别记录，不据此结束 Step 5。

<a id="agent-sandbox-flow-closure"></a>

## 11. 2026-10-22：按既定范围收拢准备、交付与回收

用户反馈：

> 好的 我觉得我这里基本上完成了这里对于boot agent sandbox的理解了
> 你觉得目前这里还有什么需要具体考虑的吗？
> 还是可以完成对于这一步的task flow总结了呢？

助手对照本步原 scope 与已有函数记录，判断可以收束：本地对象的构造、进入时申请远端环境、公共函数安装 CLI、`yield sb` 交给调用方和退出回收，都已有对应说明；不需要为等待、限流与完整失败恢复再展开一组新函数，才能整理当前主线。

本次 [task flow](05-task-flow.md) 集中接清两个交接：

1. `boot_agent_sandbox` 交出的是能够操作远端环境的本地对象。Claude Code 的安装方法选参数，common 的公共函数组织安装，两者按已确认的分工引用。
2. 交出后，调用方在 `generate.py:204–213` 依次准备工作区、运行 Agent、取得 diff；离开 `async with` 时才回到启动函数的 `finally` 请求回收。正常退出后继续独立评测。

`exec_and_wait`、底层 SDK 传输、并发与取消、内外两层重试及真实部署验证保留为按需深入项。用户的反馈说明对本函数已基本理解，不据此宣称这些细节也已掌握。

本次静态核对固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `generate.py:95–134、203–219` 和 `sandbox.py:281–307`，没有新增真实沙箱或安装运行。下一处任务交接是 `swe.prepare_workspace`，这里仅作为待确认候选，不创建下一步或新函数卡片。
