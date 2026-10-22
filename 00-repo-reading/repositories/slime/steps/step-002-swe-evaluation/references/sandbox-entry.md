# Sandbox 基础与上下文过程参考

[返回 E2BSandbox.__aenter__ 函数卡片](../02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)

本页保留从函数卡片移出的讲解，按问题查阅；函数的最小模型仍在卡片中。下列代码与配置沿用同一个教学场景，没有新增真实沙箱运行。

<a id="sandbox-basics"></a>

## 1. Sandbox、image 与本地操作对象

- **Sandbox**：本任务用于运行命令、读写文件的独立执行环境；通过 `E2BSandbox` 使用的环境在远端服务上。
- **image**：指定创建环境所用镜像的名称或标识，例如 `"teaching/calc:v1"`；这个字符串不包含镜像的全部文件。
- **E2BSandbox 对象**：本地保存配置并提供环境操作方法；内部的 `_sb` 是 SDK 对象，`sandbox_id` 是远端环境的标识。它不包含远端全部文件、进程或内存。

<a id="ev-is-same-object"></a>

**`ev` 具体是什么：本例中，它和[下节教学展开](#async-with-entry)里的 `manager` 指向同一个对象。** `manager` 只是为了展示调用顺序临时起的变量名。对象先由 `E2BSandbox(image)` 构造出来，随后才调用其 `__aenter__`。

```python
# 对应下节教学展开得到的对象；这里展示正常进入后的关系
ev is manager                 # True：两个变量指向同一个 E2BSandbox 对象
ev.image                      # "teaching/calc:v1"：原先保存的镜像标识仍然在
```

- `image` 是镜像标识字符串，构造器通过 `self.image = image` 保存它；不是把整个镜像的文件内容装进 Python 对象。
- 进入时按这个标识请求创建远端环境，并更新原对象的 `_sb` 和 `sandbox_id`。`self.image` 没有被改写。
- 最后的 `return self` 把原对象交回来，`as ev` 让 `ev` 指向它。这是本类的返回约定；其他上下文管理器可以返回其他对象。

## 2. async with 怎样安排进入与退出

<a id="async-with-entry"></a>

**先看进入顺序：完成准备，再执行缩进块。** `with` 和 `async with` 都安排“进入 → 执行代码块 → 退出”；异步版本会等待异步的进入、退出方法完成。

| 语法 | 进入时 | 退出时 |
| --- | --- | --- |
| `with` | 调用 `__enter__()` | 调用 `__exit__(...)` |
| `async with` | 等待 `__aenter__()` | 等待 `__aexit__(...)` |

把本例正常进入到第一句的顺序展开如下。`manager` 是为展示中间对象加的局部名称；这是教学展开，省略退出与异常处理，不是完整替换代码。

```python
manager = E2BSandbox(image)       # ① 构造本地对象，保存配置
ev = await manager.__aenter__()  # ② 执行进入方法，等它准备好环境并返回
await agent_sandbox.ensure_agent_user(ev, workdir)  # ③ 才开始原缩进块的第一句
```

- **Python 安排何时执行**：先运行并等待第 ② 步；只有成功返回，才把结果赋给 `ev` 并执行第 ③ 步。进入方法抛出异常时，不会开始缩进块。
- **这个类规定进入时做什么**：`E2BSandbox.__aenter__` 整理配置、请求创建沙箱、等待结果、保存 SDK 对象与 ID，最后返回 `self`。下面三段就是第 ② 步的内部内容。
- **等待谁**：当前评测流程在等待沙箱准备结果；异步等待挂起时，事件循环可以运行其他任务。本次代码块仍须等进入完成才执行。
- **“进入”的含义**：这里是执行环境准备逻辑。缩进块仍由本地 Python 进程执行，后续通过 `ev` 提交的命令才在远端沙箱中运行。

<a id="aenter-implementation"></a>

## 3. 本例配置与 __aenter__ 的实现展开

**输入：已由构造器填好配置的 `self`。** 本方法没有单独的 `image` 参数；镜像是在前面的 `E2BSandbox(image)` 中保存的。

```python
# 假设 SLIME_AGENT_SANDBOX_IMAGE_METADATA_KEY=image，其他配置采用默认值。
# 下面展示 __aenter__ 开始时的对象字段，不是重新赋值的源码。
self.image = "teaching/calc:v1"
self.image_metadata_key = "image"
self.size = "md"
self.timeout = 3600
self.rpc_retries = 6
self._sb = None
self.sandbox_id = ""
```

- `image_metadata_key` 指定用 metadata 中的哪个键传递镜像。兼容服务需支持这个约定；本例键名为 `"image"`。
- `size="md"` 是传给服务端的规格值；具体资源大小取决于服务端。
- `timeout=3600` 是传给沙箱创建接口的存活时间设置，单位为秒。外层的测试命令预算 `timeout_sec=60` 此时没有传入。

### 1. 对象配置 → 创建接口的 metadata（282–296）

```python
if self.image_metadata_key is None:
    raise RuntimeError(...)  # 教学节选：省略原错误消息
from e2b import AsyncSandbox

md = {self.image_metadata_key: self.image}

if self.size:
    prefix = self.image_metadata_key.rsplit("/", 1)[0] if "/" in self.image_metadata_key else ""
    size_key = f"{prefix}/size" if prefix else "size"
    md[size_key] = self.size
```

- **先检查镜像键名**：未配置时直接报错；配置有效才继续创建。
- **写入镜像**：本例先得到 `{"image": "teaching/calc:v1"}`。
- **补入规格**：本例键名不含 `/`，所以使用 `"size"`，最终得到下面的字典。
- **区分同名变量**：这里的局部变量 `md` 是新建的创建参数字典；它和 `_grade_scaleswe` 中保存完整任务信息的 `md` 不是同一个字典。工作目录、补丁和测试命令没有放进来。

```python
md = {"image": "teaching/calc:v1", "size": "md"}
```

### 2. 创建参数 → 用于操作沙箱的 SDK 对象（298）

```python
self._sb = await self._rpc_retry(
    "create",
    lambda: AsyncSandbox.create(timeout=self.timeout, metadata=md),
)
```

- **调用内容**：本例交给 SDK 的是 `timeout=3600` 和上面的 `metadata`。SDK 负责与配置的服务通信，具体传输在本行以下。
- **重试器的职责**：`lambda` 把“发起一次创建”交给 `_rpc_retry`。它执行该操作，遇到符合条件的错误时重试；成功时返回创建结果。本轮先停在这一职责边界。
- **接住创建结果**：`await` 成功返回后，SDK 对象存入 `self._sb`。它是在本地运行、用来访问远端沙箱的客户端对象。

### 3. 保存沙箱标识 → 把当前对象交给 ev（299–300）

```python
self.sandbox_id = self._sb.sandbox_id
return self
```

- **读取标识**：把 SDK 对象上的沙箱 ID 保存为 `self.sandbox_id`，让外层能够直接读取。
- **返回当前对象**：返回的是 `self`，所以外层的 `ev` 是这个 `E2BSandbox` 对象；前一步返回的 SDK 对象则保存在它的 `ev._sb` 中。
- **回到调用处**：`_grade_scaleswe:270` 接着将 `ev` 和 `workdir` 交给 `ensure_agent_user`。此时获得的是环境操作能力，后续才会准备用户、应用补丁并评分。

```text
ev：本地的 E2BSandbox 对象，即这里的 self
└─ ev._sb：本地的 AsyncSandbox SDK 对象
   └─ 通过服务接口操作远端沙箱
```

| 回到哪里 | 接着使用什么 |
| --- | --- |
| [_grade_scaleswe 第一段](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md#first-environment-call) | `ensure_agent_user(ev, workdir)` 使用已进入环境的 `ev`，准备执行用户与目录权限 |

<a id="verification"></a>

## 4. 来源、验证与原始讨论

讲解来自 Step 2 的原函数卡片。2026-10-21 按用户确认的精简方案移至本页；移动材料不表示新增理解或运行验证。早期追问与后续复述仍保存在原步骤的 `04-flow.md`。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`2f2318653f6f794dddd321eff7c9d4b7b174643f`；本方法 `sandbox.py:281–300`，默认值与构造器 `168–205`，重试器 `237–271`，外层调用 `swe.py:269–270`。
- 镜像键名的配置约定：`examples/coding_agent_rl/README.md:21–25、67`；示例启动脚本 `run_qwen36_35b_a3b_swe_8nodes.sh:213` 使用 `image`。本页假设相应配置已提供，没有把它当作当前机器的实测环境变量。
- metadata 的补充分支：若键名为 `sandbox/image`，规格键随之成为 `sandbox/size`；若 `size` 为空，不添加规格字段。
- 局部运行验证：导入真实 `sandbox.py`，只将 `e2b.AsyncSandbox` 替换为本地替身，使用教学镜像与沙箱 ID `demo-sandbox-001`。确认普通键名、带前缀键名、空规格三种输入的创建参数；确认 `ev` 就是原对象、SDK 对象被保存、ID 被复制；确认缺少镜像键名时在创建前报错。离开上下文时也观察到替身 `kill` 被调用。
- 这项验证没有运行实际 E2B SDK 通信、远端创建、重试故障或真实回收；不能作为服务部署、镜像可用或测试成功的证据。
- 原始场景：[Step 2 的 _grade_scaleswe](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md)。本次讨论：[Step 2 · 创建配置、SDK 对象与 ev](../04-flow.md#aenter-input-output)。
- 进入顺序另用 Python 3.12.3、真实 Slime 方法与可暂停返回的替身 SDK 验证：创建尚未返回时，缩进块未开始；返回后才执行块内第一句，正常退出时调用回收。语法依据的中英原文及本次追问见 [Step 2 · async with 的进入](../04-flow.md#async-with-entry)。
- `ev` 的对象关系依据构造器 `sandbox.py:183–189` 与进入方法 `298–300`；之前的替身实验已确认 `ev is manager`。`image` 未改写由当前固定源码核对。追问与语言依据见 [Step 2 · ev 与镜像配置](../04-flow.md#ev-is-same-object)，本次复述见 [创建时机确认](../04-flow.md#sandbox-creation-understanding)。

</details>


<a id="protocol-contract"></a>

## Sandbox 协议：理解 sb 参数的最小背景

回到 [ensure_agent_user 卡片](../02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md#sandbox-protocol)。正文只保留当前调用所需的接口与实例关系，这里保存语言依据。

### 书上怎么说

协议描述需要支持的接口；类型实现协议规定的方法，并满足相应类型签名，才能与协议相容。[依据 A]

### 我的判断（本书未覆盖）

- Slime 的 `Sandbox` 定义了命令执行、文件读写、进入与退出等接口。`ensure_agent_user` 把参数标为 `Sandbox`，在当前函数体中使用的是 `exec`。
- 本例传入的 `ev` 是 `E2BSandbox` 对象，参数名 `sb` 引用它，调用落到该对象的 `E2BSandbox.exec`。源码中的 `class E2BSandbox:` 没有显式继承 `Sandbox`；协议名称也不负责在运行时寻找或创建一个实现。
- 这些名称说明的是当前函数所需的背景。先放在该函数的输入旁边，等出现独立的协议设计问题时，再按需要扩展概念参考。

以上是对本仓库固定源码的解释：`2f2318653f6f794dddd321eff7c9d4b7b174643f`，`sandbox.py:28–59、160、309–340、390–399`，以及 `swe.py:35、269–270`。

### 依据

A · 《Fluent Python, 2nd Edition》（O’Reilly，2022），第 8 章 Static Protocols／中文“8.5.10 静态协议”。

- 英文：[corpus/en/ch08.md](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/en/ch08.md:1310)，第 1310–1499 行。
- 中文：[corpus/zh/ch08.md](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/zh/ch08.md:1268)，第 1268–1463 行。
- 双侧小节锚点：`static-protocols`。本书基于 Python 3.10，当前环境为 Python 3.12.3。

原文（英文第 1393 行）：

> A type `T` is consistent-with a protocol `P` if `T` implements all the methods defined in `P`, with matching type signatures.

对照（中文第 1353 行）：

> 如果类型 `T` 实现了协议 `P` 定义的所有方法且类型签名匹配，那么 `T` 就与 `P` 相容。

本轮已核对两个小节的锚点、范围与引文全文；Slime 的具体调用与卡片分工属于上面的源码解释。

<a id="async-with-exit"></a>

## 上下文退出：先完成清理，再交回评测结果

回到 [E2BSandbox.__aexit__ 卡片](../02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)。退出方法的实现与当前输入输出保存在该函数卡片；[_grade_scaleswe](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md#environment-exit) 保留退出时机与返回交接。这里保存语言依据和验证边界。

### 书上怎么说

- `with` 所管理的退出操作也适用于代码块通过 `return` 或异常结束的情况。[依据 A]
- 异步上下文管理器把进入、退出实现为 `__aenter__`、`__aexit__` 协程。[依据 B]

### 我的判断（本书未覆盖）

- Slime 的 `E2BSandbox.__aexit__` 等待 `self._sb.kill()`，处理当前评测环境；它既不接收评分，也不生成新的 `EvalResult`。
- 因此本例顺序是：形成 `EvalResult(1.0, True)` → 等待退出方法完成 → 经 `run_evaluation` 返回 → `generate` 接住 `reward, applied_cleanly`。
- 退出方法捕获的是回收代码里的 `Exception` 并记录 warning；不能据此声称所有异常或取消都被处理。评测主体抛出的异常没有被这个方法压下，仍向外传播。这里的 `None` 返回值不会替换正常路径上的评测结果。

上述关系来自固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `sandbox.py:302–307`、`swe.py:239–247、269–287` 与 `generate.py:215–219`，不是书中对 Slime 的描述。

### 依据

A · 《Fluent Python, 2nd Edition》（O’Reilly，2022），第 18 章 Context Managers and with Blocks／中文“18.2 上下文管理器和 with 块”。本书基于 Python 3.10，当前验证环境 Python 3.12.3。

- 英文：[corpus/en/ch18.md](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/en/ch18.md:31)，小节第 31–221 行。
- 中文：[corpus/zh/ch18.md](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/zh/ch18.md:29)，小节第 29–215 行。
- 双侧锚点：`context-managers-and-with-blocks`。

原文（英文第 35 行）：

> The `with` statement was designed to simplify some common uses of `try/finally`, which guarantees that some operation is performed after a block of code, even if the block is terminated by `return`, an exception, or a `sys.exit()` call.

对照（中文第 33 行）：

> `with` 语句的目的是简化一些常用的 `try`/`finally` 结构。这种结构可以保证一段代码运行完毕后执行某项操作，即便那段代码由于 `return` 语句、异常或 `sys.exit()` 调用而终止，也执行指定的操作。

B · 同书第 21 章 Asynchronous Context Managers／中文“21.6 异步上下文管理器”。本书基于 Python 3.10，当前验证环境 Python 3.12.3。

- 英文：[corpus/en/ch21.md](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/en/ch21.md:334)，小节第 334–380 行。
- 中文：[corpus/zh/ch21.md](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/zh/ch21.md:293)，小节第 293–343 行。
- 双侧锚点：`asynchronous-context-managers`。

原文（英文第 358 行）：

> That’s why PEP 492—Coroutines with async and await syntax introduced the `async` `with` statement, which works with asynchronous context managers: objects implementing the `__aenter__` and `__aexit__` methods as coroutines.

对照（中文第 318 行）：

> 鉴于此，“PEP 492—Coroutines with async and await syntax”引入了 `async with` 语句，用于实现异步上下文管理器，即一种以协程实现 `__aenter__` 和 `__aexit__` 方法的对象。

### 本地验证及其边界

通过 AST 提取真实的 `EvalResult`、`run_evaluation`、`_grade_scaleswe` 和 `E2BSandbox.__aexit__`，保持函数体不变；用本地替身替换环境创建、用户准备、补丁应用、评分与 SDK 的 `kill()`。替身 `kill()` 包含一次异步挂起，用事件列表观察调用顺序。

| 场景 | 实际观察到的退出顺序 | 调用方收到什么 |
| --- | --- | --- |
| 正常评分 | `kill-start → kill-done → caller-result` | `EvalResult(reward=1.0, applied_cleanly=True)` |
| 补丁处理失败 | 未调用评分；`kill-start → kill-done → caller-result` | `EvalResult(reward=0.0, applied_cleanly=False)` |
| 回收抛出 `RuntimeError` | `kill-start → cleanup-warning → caller-result` | 已形成的 `EvalResult(reward=1.0, applied_cleanly=True)` |
| 评分抛出 `ValueError` | `kill-start → kill-done → caller-error` | 原评分异常，未转换成零分 |

四条路径的顺序与结果断言通过。没有调用真实 SDK、远端环境、补丁工具或测试命令，也没有验证远端删除、取消或网络故障恢复。中英引文及小节锚点另行核对；本次阅读过程见 [Step 2 的退出与返回讨论](../04-flow.md#evaluation-context-exit)。
