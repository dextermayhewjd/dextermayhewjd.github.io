# Trial._close_logger_handler（Harbor）

[本步 scope · 6b](../../../../../01-scope.md) · [返回 Trial.run](Trial.run.md) · [源码 :1225](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1225)

**当前问题：文件已经保存和尝试脱敏，怎样结束本 Trial 的日志写入？**

调用方：Trial.run 的最内层 finally 执行 `self._close_logger_handler()`。输入来自对象持有的 logger 与 _log_handler，正常返回 None。

## ① 怎样停止本 Trial 的文件日志输出？

**这里收尾的是本 Trial 的 FileHandler，不是分析、修改或删除日志内容。** 它此前由 `_init_logger` 创建，负责把日志写入本次日志文件。

源码全文（trial.py:1225–1231），仅增加注释：

```python
def _close_logger_handler(self) -> None:
    if self._log_handler is None:                 # 没有 handler：无需关闭；重复调用也可返回
        return

    self.logger.removeHandler(self._log_handler) # 卸下这个输出渠道；不关闭 logger 或其他 handler
    self._log_handler.close()                    # 关闭文件写入资源；已有日志文件仍保留
    self._log_handler = None                     # 清空本 Trial 保存的引用
```

<details>
<summary>为什么放在脱敏之后？</summary>

脱敏过程仍可能记录跳过文件等调试信息，所以先尝试脱敏，再关闭日志 handler。调用方用嵌套 finally，使脱敏出错时仍尝试关闭；这不构成对之后新写入日志内容的额外脱敏保证。

</details>

## ② 读完回哪里？

返回 Trial.run。当前取消且清理正常完成的路径，到这里已完成最后一项清理，原 CancelledError 随后继续向上传播，不走末尾 `return self.result`。

若清理抛出新异常，最终传播的异常可能改变；不能用 finally 的存在推断每项清理一定成功。


<details>
<summary>个人表述、未知与源码依据</summary>

- 首次单独建卡：2026-11-17，Step 016；前一轮已在 Trial.run 第[6]段讲解，本次移入独立卡，不表示新增掌握。
- 用户要求：“不应该单独再看一下这里的这个函数卡片吗 同时在这里的scope中写一下？”本轮用户随后表述：“也就是这一个部分更多的只是一个filehandler？需要处理log的内容是我的理解？”助手校准：是 FileHandler 的关闭与解除关联，不是处理日志内容。
- 固定源码：Harbor v0.25.0，`fdba28fc411e47e8765420a1a063b4918fce3def`；仅静态核对，没有实际执行文件脱敏或日志关闭实验。
- 未展开：logging 的内部锁和多 handler 分发；本轮只理解本 Trial 持有的 FileHandler 生命周期。
- 展示反馈：用户要求将代码下逐句解释尽量移到行旁注释；本次仅调整展示，不改变函数逻辑或扩大阅读范围。
- [形成过程](../../../../../04-flow.md)。

</details>
