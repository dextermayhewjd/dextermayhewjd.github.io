# 第 21 课：异步上下文管理器核对记录

- 标准库依据：[Python 3.12 contextlib.asynccontextmanager](https://docs.python.org/3.12/library/contextlib.html#contextlib.asynccontextmanager)。
- 实验环境：Python 3.12.3。核对本机 `contextlib.py` 中的 `asynccontextmanager` 和 `_AsyncGeneratorContextManager`：调用工厂创建管理器，进入时推进到 yield，正常退出时继续推进；使用区异常在 yield 处传入。
- 正文先用 `yield_steps.py` 补齐一次产出与暂停的边界，再解释装饰器；不要求先学异步迭代、装饰器实现、类或协议方法。
- `manual.py` 与 `example.py` 管理同一种教学资源。`failure.py`、`cancellation.py` 直接导入后者的工厂，验证已进入后的异常和一次取消都先完成清理。
- 教学字典的 `open` 字段与 `sleep(0)` 只是可观察替身，没有启动 E2B、远程沙箱、进程或服务。

## 固定源码

- 已确认的本地 Slime 路径 `/home/fredkeira/projects/slime` 本次不可用；从同一个 GitHub 固定提交重新读取，没有改换项目。
- 提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 文件：`examples/coding_agent_rl/generate.py`，`boot_agent_sandbox(image, instance_id)`。
- SHA-256：`493f995c961ae302d81725c134f122a6933a4396236a498d514550dd8d7707b1`。
- 文件原字节与已有快照相同，学习包范围包含装饰器、函数签名、准备、yield 和 finally。
- 保留真实函数名及两个参数；删除类型注解、E2BSandbox 实现、安装、并发限制与重试。真实 `await sb.__aexit__(None, None, None)` 在教学实验中用一次异步等待及状态修改替代。
- 原实现中进入失败、安装失败和重试耗尽都有独立分支。正文区分进入前与成功进入后的清理，不声称装饰器自动处理任意部分初始化失败。
- 只运行标准库教学实验，没有运行 Slime 沙箱服务。

## 六节拆分

2026-10-15 按确认后的学习边界拆为 21.1–21.6：准备/使用/关闭、yield、函数传递与装饰器、正常进入退出、异常、取消。旧 URL 对应 21.4；原四份补充脚本继续保留。21.5、21.6 的完整脚本复用相同的 boot_agent_sandbox 函数，资源模拟与来源版本均不改变。
