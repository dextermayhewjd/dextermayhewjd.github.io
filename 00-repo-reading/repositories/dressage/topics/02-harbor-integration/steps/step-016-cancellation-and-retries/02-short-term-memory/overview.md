# 本步函数索引

- [Trial.run：取消分支](functions/harbor/trial/trial.py/Trial.run.md#trial-cancellation)：保留前序完整卡片，本步补 CancelledError 与 finally 交接；待用户反馈。

- [Trial._record_exception](functions/harbor/trial/trial.py/Trial._record_exception.md)：[1] 取消异常的结果字段与文件记录，读完返回 Trial.run 的 [2]。

- [DressageHarborPlugin._on_cancel](functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_cancel.md)：[2] CANCEL 回调的取消标记及路由静止，返回 Trial.run 的 [3]。
