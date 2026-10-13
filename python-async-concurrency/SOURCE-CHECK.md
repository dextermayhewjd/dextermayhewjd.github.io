# 来源、统计边界与验证

## 源码版本

- 核对日期：2026-10-13。
- 当前可用源码：`/home/hongshi/projects/slime`；Git 根目录已核对。
- 固定 HEAD：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 该提交时间：2026-10-07 10:49:25 +0800；标题：`fix(weight-sync): honor checkpoint shard indexes in disk delta sync (#2442)`。
- origin：`git@github.com:dextermayhewjd/slime.git`，属于 fork。
- 本次直接查询官方 `https://github.com/THUDM/slime.git` 的 `refs/heads/main`：`05e3b017fed9e02de418c2fbac9d75602a534be5`。它与本地 HEAD 不同；本目录统计本地固定版本，不声称覆盖之后的提交。
- 旧阅读记录中的 `/home/fredkeira/projects/slime` 在当前机器不存在；既有章节绑定的 `22a89f9...` 也不是本次本地 HEAD。本目录单独注明版本，没有改写原阅读路线。
- 开始时源码仓库已跟踪文件无差异；存在未跟踪的 `asyncio_concurrency_best_practices/`。它作为已有资料保留，不进入本次扫描，也未被修改。

## 统计口径

`tools/scan.py` 遍历 `git ls-files` 中的 Python 源文件，解析 AST 并记录位置。完整规则、识别来源、文件哈希与计数在 [summary.json](summary.json) 和扫描器中。

- 语法出现、导入、API 调用、非调用 API 引用分别计数；不能把它们相加称为“调用次数”。同一源码行可以包含多个位置。
- API 引用包含类型注解、异常类和常量；它们也属于实际用法，但不是调用。
- 只有标准库/语言机制进入原生类别。Ray、PyTorch、HTTPX 等接口不因名字含 `async` 或 `wait` 而变成 Python 原生 API；这些文件中的 `await` 仍属于 Python 语法。
- 无法可靠确定接收者类型的 `.wait()`、`.result()`、`.join()` 等保留为候选，单独展示，不混入已解析 API 调用。阅读时需回到构造和赋值位置核对。
- 静态扫描不执行模块，不证明运行时绑定、分支可达性、并发安全或调用次数。动态导入、`getattr` 计算出的调用等不能据此保证穷尽。
- Markdown 中的教学代码另见 [DOCUMENTATION-SNIPPETS.md](DOCUMENTATION-SNIPPETS.md)，与 `.py` 统计分开，避免中英文文档和真实实现重复计数。
- [source_snapshot/](source_snapshot/) 保存命中源文件的原字节副本，用 `.py.txt` 后缀避免作为模块或测试被发现；不是移走、改写或可独立运行的实现。

## 书上怎么说

网络请求需要限制并发数量，避免同时向服务端施加过多请求。[依据 A]

## 我的判断（本书未覆盖）

Slime 把信号量、生产者结果队列、线程池和任务取消用在不同职责上。本目录根据源码分别列出这些用法，不能仅凭一个 API 名称把某段实现认定为最佳实践。

`asyncio.timeout()` 属于 Python 3.11 之后的 API，不在这本以 Python 3.10 为基准的书中。实际出现位置与版本要求按源码及 Python 官方文档核对。

## 依据

A — 第 21 章《异步编程》：Throttling Requests with a Semaphore

- 英文：`corpus/en/ch21.md:483–606`，锚点 `throttling-requests-with-a-semaphore`。
- 中文：`corpus/zh/ch21.md:445–571`，同一锚点，“21.7.2 使用信号量限制请求”。
- 版本：*Fluent Python, 2nd Edition*（O'Reilly, 2022），基于 Python 3.10；本次工具解释器 Python 3.12.3，不等于 Slime 所有部署环境版本。
- 镜像：`/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local`。

原文：

> Network clients like the ones we are studying should be throttled (i.e., limited) to avoid pounding the server with too many concurrent requests.

对照：

> 像我们分析的这种网络客户端应该限流，以免对服务器发起过多并发请求。

上述引文已核对中英文同一锚点、完整小节行号和逐字内容；未复制整本书。

## 官方语义核对

- 协程、Task、gather、wait、取消、线程桥接及 timeout：[Python 3.12 Coroutines and Tasks](https://docs.python.org/3.12/library/asyncio-task.html)。
- 异步锁和信号量用于同一事件循环的任务同步：[Synchronization Primitives](https://docs.python.org/3.12/library/asyncio-sync.html)。
- 有界异步队列的等待及线程安全边界：[Queues](https://docs.python.org/3.12/library/asyncio-queue.html)。
- 线程池、Future 与取消边界：[concurrent.futures](https://docs.python.org/3.12/library/concurrent.futures.html)。
- ContextVar 的局部状态和 token 恢复：[contextvars](https://docs.python.org/3.12/library/contextvars.html)。
- 信号处理与平台约束：[signal](https://docs.python.org/3.12/library/signal.html)。

## 验证方式

在项目根目录执行：

```bash
python3 python-async-concurrency/tools/scan.py /home/hongshi/projects/slime --check
```

需要更新源码版本或统计时，去掉 `--check` 重新生成。更新后还应人工核对 GUIDE 的固定链接和本文件的版本说明。生成器只更新自己的清单与快照，不改 Slime 源码。

本次验证结果记录在 [VALIDATION.json](VALIDATION.json)。验证涵盖重新扫描、统计一致性、源码快照、文档链接和所摘录的代码；没有运行训练、模型服务、GPU 测试或沙箱。
