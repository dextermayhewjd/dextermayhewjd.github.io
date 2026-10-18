# Python 异步和并发：Slime 全量用法汇编

集中存放 Slime 中实际出现的 **Python 语言及标准库异步、线程、进程和同步机制**。这是项目根目录下的独立资料夹，不属于 `slime_photo`，也不移动或改写 Slime 源码。

源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。本次遍历 **381 个已跟踪 Python 文件**；测试、示例、插件和工具脚本均在范围内。

网站学习入口：[Python 异步与并发项目](https://dextermayhewjd.github.io/projects/python-async-concurrency/)。按知识点阅读，与下方全量资料对应。

当前课程安排见 [8 模块、41 单元的课程设置](../python-async-reference/curriculum.md)，网页入口为[学习路线与完成标准](../content/projects/python-async-concurrency/learning-route/index.md)。01–03 保留原课，新增 04 语法前置，原 04 起顺延，已整理 01–22、24–38，第 20 单元的 20.2–20.5 正式讲当前循环、结果对象、等待交付和状态异常；第 35 单元的 35.1–35.2 复习结果读取与源码交付，35.3 正式讲完成回调；36.1、36.2 分别整理循环的手动生命周期与跨线程提交，其余单元按规划补写，最终包含全部已选定的 98 项 API。本目录的旧页编号和全量索引保留用于复用与回查，不表示要同时学完。

旧版教程保留 **23 页**；当前路线另有语法前置与拆分后的独立课程。第 10 单元是 `15-gather-failures` 和 `15-gather-exceptions`，第 11 单元是 `11-taskgroup-failures` 和 `11-exception-groups`，各分两节。第 09 单元学习取消，12 单元学习 as_completed，13–16 学习超时和预算，17 单元在原 `06-semaphore` 地址学习许可与释放，18 单元在原 `07-queues` 地址学习异步数据交接，19 单元在 `19-async-lock` 学习共享状态的异步互斥，20 单元从 `20-async-event` 的通知与标志出发，再用 20.2–20.5 学习 Future 基础，21 单元拆为 21.1–21.6：资源三阶段、yield、装饰器、正常进入退出、异常、取消；原 `21-async-contextmanager` 地址保留为 21.4，22 单元在 `22-async-iteration` 学习逐项异步产出与顺序消费；已有 URL 均保留。新 TaskGroup 失败实验核对 CPython v3.12.3 源码，常规 TaskGroup 页继续使用 AReaL 的固定快照，其余 Slime 统计版本不变。完整映射见 [teaching-coverage.md](teaching-coverage.md) 和 [teaching-coverage.json](teaching-coverage.json)，知识点定义以 [teaching-topics.json](teaching-topics.json) 为准。

补充教学与关系摘要分开维护：专题根目录的 `loop-call-soon/`、`loop-call-later/` 保存完整例子与讲解；`comparisons/` 保存精简的函数关系，供复习和思维导图使用，两边互链，不增加正式课号。

## 从哪里看

| 内容 | 文件 |
| --- | --- |
| 按任务主线理解各机制，配真实源码 | [GUIDE.md](GUIDE.md) |
| 每种机制的所有位置及分类计数 | [usage-categories/](usage-categories/) |
| 每个 Python 文件的扫描结果 | [FILES.md](FILES.md) |
| 可搜索、筛选的逐条清单 | [inventory.tsv](inventory.tsv)、[inventory.json](inventory.json) |
| 按类别和每种 API 的次数统计 | [STATISTICS.md](STATISTICS.md) |
| 机器可读统计与扫描规则 | [summary.json](summary.json) |
| 文档中出现的 Python 示例，单独统计 | [DOCUMENTATION-SNIPPETS.md](DOCUMENTATION-SNIPPETS.md) |
| 命中源码的原字节快照 | [source_snapshot/](source_snapshot/) |
| 源码版本、统计边界与参考依据 | [SOURCE-CHECK.md](SOURCE-CHECK.md) |
| 本次验证结果 | [VALIDATION.json](VALIDATION.json) |

## 语言用法统计

| 语法 | 源码位置数 |
| --- | ---: |
| `async def` 定义合计 | 288 |
| 其中：协程函数 | 281 |
| 其中：异步生成器函数 | 7 |
| 异步生成器中的 `yield` | 7 |
| `await` 表达式 | 409 |
| `async with` 语句 | 42 |
| `async for` 语句 | 1 |
| 带 `async for` 子句的推导式 | 0 |

完整函数名、所属文件和行号见 [syntax.md](usage-categories/syntax.md)。一次执行可能多次经过同一位置；这里是静态源码位置数量。

## 按机制查看所有用法

| 范围 | 主要内容 | 完整清单 |
| --- | --- | --- |
| 协程调度与同步 | 事件循环、Task、Future、gather、wait、超时、取消、Semaphore、异步队列 | [asyncio](usage-categories/asyncio.md) |
| 线程与共享状态 | Thread、Lock/RLock、Event、Condition、local | [threading](usage-categories/threading.md) |
| 同步队列 | Queue、Empty、Full 与跨线程数据交接 | [queue](usage-categories/queue.md) |
| 执行器 | ThreadPoolExecutor、Future、结果收集 | [executors](usage-categories/executors.md) |
| 进程 | multiprocessing、启动上下文、进程池及生命周期 | [multiprocessing](usage-categories/multiprocessing.md) |
| 外部命令 | Popen、run、输出和进程退出处理 | [subprocess](usage-categories/subprocess.md) |
| 请求上下文 | ContextVar 与上下文恢复 | [contextvars](usage-categories/contextvars.md) |
| 异步协议辅助 | asynccontextmanager、异步反射、类型标记、内置协议入口 | [contextlib](usage-categories/contextlib-async.md)、[inspect](usage-categories/inspect-async.md)、[类型](usage-categories/async-typing.md)、[内置](usage-categories/async-builtins.md) |
| 操作系统相关配套机制 | signal、文件锁、进程控制、同步等待 | [signal](usage-categories/signal.md)、[fcntl](usage-categories/fcntl.md)、[os](usage-categories/os-process.md)、[sleep](usage-categories/time-sleep.md)、[select](usage-categories/select.md) |
| 需要结合接收者核对的方法 | `.cancel()`、`.result()`、`.join()`、`.get()`、`.put()` 等 | [候选方法](usage-categories/candidates.md) |

每个分类文件列出该类的全部记录，包含文件、行号、所在函数、源码行和识别来源。空分类会明确显示没有命中，不补造 Slime 未使用的示例。

## 怎样理解“所有用法”

本目录对上述固定版本的已跟踪 `.py` 文件做完整遍历。源码中的导入、API 调用、非调用引用和语言语法分别统计；类型注解、异常类、常量也保留。文档代码块另表列出。

同名对象方法需要结合类型判断，因此另列候选表，避免把字符串 `.join()`、字典 `.get()` 或 Ray 方法算作原生并发 API。扫描无法证明所有动态绑定或生成代码；具体限制见 [SOURCE-CHECK.md](SOURCE-CHECK.md)。

Ray、PyTorch、HTTPX、aiohttp 等第三方接口不计为原生标准库 API。调用它们时使用的 `await`、`async with` 等 Python 语法仍在语法表中，周边原生线程或事件循环也会按实际用途记录。

## 重新扫描与校验

从本项目根目录执行：

```bash
# 只校验，不改已有清单
python3 python-async-concurrency/tools/scan.py /home/hongshi/projects/slime --check

# 源码版本变化后，重新生成清单、分类表和快照
python3 python-async-concurrency/tools/scan.py /home/hongshi/projects/slime
```

扫描器仅使用 Python 标准库，不导入 Slime，也不启动模型、训练或服务。更新后另行核对导读中的固定源码链接。源码副本保持原有版权注释；许可证见 [SOURCE-LICENSE](SOURCE-LICENSE)。

## 校验教程覆盖

```bash
python3 python-async-concurrency/tools/build_teaching_coverage.py --check
```

源码或讲解入口变化后，先更新知识点对应关系，再去掉 `--check` 生成新的完整映射。未映射的 API、语法或已有接收者线索的方法会使校验失败。

第 33 单元分为 33.1 `33-current-loop`、33.2 `33-run-in-executor`、33.3 `33-await-handoff`、33.4 `33-loop-time`，依次复习已有循环对象、讲指定线程池的异步等待、等待时的协程切换、循环时钟；目录归在同一组。主例子与独立补充实验均已登记在 manifest 中，原 URL 和下载保留。

第 34 单元 `34-wrap-future` 只讲把已提交工作的执行器 Future 接入 await；不重复提交工作，状态读取、手动完成结果与回调仍留在第 35 单元分开讲解。

第 25 单元 `25-inspect-awaitable` 独立辨认函数与调用返回的对象；原 `21-async-inspection` 页面保留作多主题参考，正式入口与源码映射转到新课。

第 37 单元在 `37-subprocess-run` 单独讲解 subprocess.run，以本地 Python 子程序验证启动、同步等待、退出码和捕获的输出。旧进程综合页面保留，subprocess.run 的教学覆盖入口迁到新课。

第 38 单元在 `38-popen-communicate` 承接第 37 课，同一子程序配合 Popen 与 communicate 演示启动后继续执行、稍后收集输出与等待。两节之间的子程序保持一致。
