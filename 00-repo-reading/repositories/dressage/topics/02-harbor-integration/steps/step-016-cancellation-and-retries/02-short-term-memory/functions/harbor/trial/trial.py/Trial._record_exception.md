# Trial._record_exception

- 源码：[Harbor trial.py:669–679](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L669)，固定 v0.25.0 发布提交。
- 首次单独展开：2026-11-16，Step 016；用户表示原父卡的用途概括看不清，当前补真实代码与前后数据。
- [scope 的 [1]](../../../../../01-scope.md#current-reading) → [Trial.run 的调用位置](Trial.run.md#cancel-record) → **当前函数** → [返回 [2] CANCEL 通知](Trial.run.md#cancel-notify)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Trial.run 已捕获 CancelledError，在通知插件前留下这次取消的诊断资料。
2. **具体内容**：已有异常记录就直接返回；否则填写 TrialResult 的异常字段，并向异常文本文件写入 traceback。
3. **建议构建的心智模型**：

   > 给这次 Trial 留下第一份异常记录：结果对象里一份结构化信息，文件里一份 traceback 文本。

4. **调用代码**：

   ```python
   except asyncio.CancelledError as exc:
       self._record_exception(exc)         # 当前：保存异常资料。
       await self._emit(TrialEvent.CANCEL)  # 返回后：通知插件。
       # 后续关闭桥接、恢复输出、raise，仍由 Trial.run 完成。
   ```

## 本场景的输入与输出

**带着什么进入？** `exc` 是父函数捕获的取消异常；`self.result` 是这次 Trial 已有的结果对象。本例假设它的 `exception_info` 还没有填写。

**要解决的问题**：任务被取消了，怎样留下一份可以查到类型、原因和调用栈的记录？

下面保留全部业务语句，仅省略已有异常时的 debug 日志：

```python
def _record_exception(self, exc: BaseException) -> None:
    if self.result.exception_info is not None:
        # 已有第一份异常记录，不覆盖，也不重写下面的异常文件。
        return

    self.result.exception_info = ExceptionInfo.from_exception(exc)
    # 修改内存中的结果对象：异常类型、消息、traceback、发生时间。

    self.paths.exception_message_path.write_text(traceback.format_exc())
    # 把当前 except 上下文的 traceback 写入这次 Trial 的异常文本文件。
```

**发生了什么变化？** 假设传入的是无附加消息的 `CancelledError()`，静态示意如下：

```text
调用前：self.result.exception_info = None
调用后：self.result.exception_info
          exception_type      = "CancelledError"
          exception_message   = ""
          exception_traceback = 当前异常的 traceback 文本
          occurred_at         = 记录时的 UTC 时间

同时：exception_message_path 指向的文件写入 traceback 文本。
返回：None；父函数继续执行 _emit(CANCEL)。
```

这里没有返回一个新 TrialResult，而是修改已有对象；完整结果文件由后续收尾保存。它也不发出取消、不清理环境、不执行 raise。`traceback.format_exc()` 读取的是当前正在处理的异常上下文，本例正处于父函数的 except 中。

## 我的直接表述（原话）

> 请看一下之前的step是如何生成这里的函数卡片的吧
> 这里的这个record exception 我感觉我完全看不清楚到底在做什么

以上是先前卡点。随后用户表述：

> 价单来说就是在这里的result exception中还有当前的这个paths中记录到底异常的文件是什么 法身时间等一系列内容
> 好的 我大概理解了
> 我觉得这个short term memory很好
> 那么继续吧

助手校准：异常字段和时间进入 result.exception_info；paths 提供路径，文件写入 traceback 文本。用户已表达大概理解，未表示全部异常处理机制已掌握。

## 尚不清楚

- 当前先接清异常对象到结果字段与文件的变化；文件写入失败和诊断资料的后续消费不展开。
- 示例未执行真实 Trial 取消；不据此确认环境清理或跨版本运行成功。

<details>
<summary>来源与验证</summary>

- Trial._record_exception：固定提交 trial.py:669–679。
- ExceptionInfo 的四个字段与 from_exception：同提交 models/trial/result.py；消息来自 str(exc)，无参数 CancelledError 的消息可为空。
- 仅静态源码核对；实际时间与 traceback 未虚构为运行输出。
- [本步记录](../../../../../04-flow.md)。

</details>
