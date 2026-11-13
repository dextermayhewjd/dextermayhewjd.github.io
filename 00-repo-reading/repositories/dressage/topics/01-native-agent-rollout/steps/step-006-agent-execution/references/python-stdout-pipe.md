# Python 怎样读取 CLI 的标准输出

> 只回答：父进程怎样通过管道读取子进程输出，bytes 又怎样变成文字和 JSON。这里不展开模型 API 或训练轨迹。

[回到函数卡的进程启动](../02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#start-process) · [stdout 与模型 API 的区别](../../../../../references/cli-output-and-model-api.md)

2026-11-08，从 _run_claude_turn 卡提取。保留原先的小实验及验证边界，不是新的一门并发课程。

## 1. 管道怎样接起来

**标准输出是一条输出通道，不等于终端屏幕。** 平时从终端运行 CLI，它的输出通常接到终端；这里由 Python 启动 CLI，并主动改变输出的去向。

1. `stdout=asyncio.subprocess.PIPE` 要求创建子进程时，把它的标准输出接到操作系统管道的写端。
2. Claude 照常向自己的标准输出写内容，不需要知道接收方是终端还是 Python。
3. Python 持有管道读端，asyncio 将它包装为 `process.stdout`，因此可以异步读取。

```text
Claude stdout -> OS pipe -> process.stdout -> raw_line
                                               |-> stdout.log
                                               +-> JSON events
Claude stderr -------------------------------> stderr.log
```

在当前架构中，父进程 BlackboxServer 与它启动的 Claude 子进程都在沙箱内；这段管道是进程间的数据通道，不是从远端终端界面抓文字。cwd 只决定 Claude 在哪个目录工作，不负责捕获输出。

正常读取到的 stdout 先由 Python 写入 `claude_code.stdout.log`，再解析；不是先写日志，再去日志里读取。stderr 则直接连接到了另一个日志文件。

**最小验证：用一个会打印文字的 Python 子进程代替 Claude。**

```python
import asyncio
import sys

async def main():
    process = await asyncio.create_subprocess_exec(
        sys.executable,                    # 启动另一个 Python 进程。
        "-u",                              # 子进程不缓冲标准输出。
        "-c", "print('hello from child')", # 子进程只打印一行。
        stdout=asyncio.subprocess.PIPE,     # 将它的输出接到管道。
    )
    assert process.stdout is not None
    async for raw_line in process.stdout:   # 父进程从管道读到 bytes。
        print("父进程读到：", raw_line.decode().rstrip())
    returncode = await process.wait()
    assert returncode == 0

asyncio.run(main())
```

本地实际输出：

```text
父进程读到： hello from child
```

这只验证标准库的子进程输出管道，没有运行 Claude 或模型。异步逐行读取在没有完整行可读时会等待，不表示每个模型 token 都立即交给 Python；子进程的缓冲与换行也会影响何时读到数据。


<a id="decode"></a>

## 2. decode 与 JSON 解析分别做什么

这里连续进行的是两种普通的数据转换。下面是一行输出的格式示意，非真实 Claude 运行结果：

```python
raw_line = b'{"type":"result","result":"done"}\n'
line = raw_line.decode("utf-8").strip()  # bytes -> str
event = json.loads(line)                # JSON 字符串 -> dict
```

Python 是在解析 Claude CLI 自己输出的 JSON，而不是通过这段 decode 重新获取模型 API 的原始请求、回复或 logprob。

## 3. 读完回到哪里

回到[函数卡第 3 段](../02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#read-stdout)，继续看 raw_line 怎样写日志、转换成 event，以及何时等待进程退出。

<details>
<summary>来源与记录</summary>

- 源码依据：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，blackbox_server/adapters/claude_code.py:556–590。
- 小实验已在此前对话中本地运行，输出与退出码已核对；本次仅迁移笔记，没有运行 Claude、沙箱或模型。
- [拆分前完整记录](history/run-claude-turn-before-split-2026-11-08.md)保留全部原话和形成过程。
- [本次拆分记录](../04-flow.md#stdout-notes-split)；掌握状态仍以用户实际反馈为准。

</details>
