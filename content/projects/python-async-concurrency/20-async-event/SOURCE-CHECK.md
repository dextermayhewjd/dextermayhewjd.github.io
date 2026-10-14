# 第 20 课：Event 核对记录

- 语义依据：[Python 3.12 Event 文档](https://docs.python.org/3.12/library/asyncio-sync.html#event)。
- 实验环境：Python 3.12.3，默认事件循环与任务工厂；本课补充脚本使用 TaskGroup，因此整课要求 Python 3.11 及以上。
- 核对本机 `/usr/lib/python3.12/asyncio/locks.py` 的 `Event.__init__`、`wait`、`set`、`clear`：标志初始为假，wait 返回 True；set 完成现有等待者的等待，clear 重设标志但不撤回已经发生的唤醒。
- `example.py` 由单通知实验解释 set、等待者恢复、Task 返回三个阶段；`flags.py` 检查重复等待和清除；`broadcast.py` 检查多个等待者；`set_then_clear.py` 区分原有与新等待者；`cancellation.py` 检查取消一方不会通知或取消另一方。
- 正文用泳道图和实际输出旁注对照通知、恢复与完成；MAIN 与 FETCH 的身份在图前解释，L 行号指向 `example.py`，图与 `execution-flow.py` 下载内容保持一致。

## Slime 固定源码

- 已确认的本地路径 `/home/fredkeira/projects/slime` 本次不可用；从 GitHub 的固定提交重新核对，没有更换项目。
- 提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 文件：`tests/test_distributed_rollout.py`，L2071–2104。
- SHA-256：`4f73dedd74a7311414f4f8f6ba176c283772b888238aad1884781a8490dd586e`。
- 下载文件与 `python-async-concurrency/source_snapshot/tests/test_distributed_rollout.py.txt` 的原字节及学习包摘录均一致。
- 保留真实回调名称 `fetch(count)`、`group`、`release` 与 `[group]` 返回形状；主例子用字符串代替 Sample，删去 entered 握手、真实 worker、暂停和缓冲逻辑，使用一次 sleep(0) 展示等待者先进入的次序。它不是完整原函数的直接执行。
- 只验证标准库实验和静态源码，没有运行 Slime 服务或训练。
