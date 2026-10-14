# 第 19 课：Lock 核对记录

- 标准库实验：Python 3.12.3，最低 Python 3.11（使用 TaskGroup）；采用默认事件循环与任务工厂。
- 标准库依据：[Python 3.12 Lock](https://docs.python.org/3.12/library/asyncio-sync.html#lock)。另核对本机 `/usr/lib/python3.12/asyncio/locks.py` 的 `Lock.acquire`、`Lock.release` 与 `_ContextManagerMixin`；上下文进入等待取得锁，退出释放锁。
- `example.py` 与 `manual.py` 对同一个读取、等待、写回操作分别使用两种配对写法；它们不是 Slime 函数的直接裁剪。
- `without_lock.py` 展示人为加入 `sleep(0)` 后的更新覆盖；`cancellation.py` 与 `failure.py` 验证退出后可重新取得锁。取消的实验先等待持锁任务退出，再检查重新取得。
- 泳道图中的 L 行号对应本课 `example.py`，每一行只有一份任务执行；图记录的是本次正常实验，不承诺所有程序固定以 A 在先。

## Slime 固定版本

已确认的路径 `/home/fredkeira/projects/slime` 本次不存在。沿用已确认仓库，不更换项目；从 GitHub 固定提交重新获取文件，逐字核对既有快照与学习包摘录。

- 提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 文件：`slime/backends/megatron_utils/server/megatron_server.py`。
- SHA-256：`43ad090936020c367a6cdaa6c7c9589a76f99149438a74ff9a7e404268ea95a4`。
- L422–468：共享锁、请求入口、状态检查与预留。
- L484–515：异常处理、最终状态登记与清理。
- 原实现的这些锁内状态修改没有显式 `await`，不能把独立计数实验当作原实现的逐行复刻。
- 本课只核对标准库语义和静态源码，没有运行 Slime 服务或训练。
