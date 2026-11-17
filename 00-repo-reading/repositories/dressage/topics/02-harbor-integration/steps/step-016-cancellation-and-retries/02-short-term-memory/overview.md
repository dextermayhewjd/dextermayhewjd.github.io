# 本步函数索引

- [Trial.run：取消分支](functions/harbor/trial/trial.py/Trial.run.md#trial-cancellation)：保留前序完整卡片，本步补 CancelledError 与 finally 交接；待用户反馈。

- [Trial._record_exception](functions/harbor/trial/trial.py/Trial._record_exception.md)：[1] 取消异常的结果字段与文件记录，读完返回 Trial.run 的 [2]。

- [DressageHarborPlugin._on_cancel](functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_cancel.md)：[2] CANCEL 回调的取消标记及路由静止，返回 Trial.run 的 [3]。

- [Trial._finalize](functions/harbor/trial/trial.py/Trial._finalize.md)：Step 015 完整卡调取；当前取消场景中的共同收尾、保存结果与 END。

- [Trial._scrub_jobs_dir](functions/harbor/trial/trial.py/Trial._scrub_jobs_dir.md)：[6a] 已知敏感值的文本脱敏；返回内层 finally。
- [Trial._close_logger_handler](functions/harbor/trial/trial.py/Trial._close_logger_handler.md)：[6b] 移除、关闭本 Trial 日志 handler 并清空引用。
