# Step 016 阅读过程

## 2026-11-16 · 快速阅读一次外部取消

用户确认“快速看一下这里的这个step016”。本轮限定 Agent 执行期间一次外部取消，核对 Harbor v0.25.0 的 Trial.run/_finalize，以及 Dressage 3e3142fe 的 _on_cancel/_on_end/_finalize_attempt。未运行取消实验，也未确认跨版本兼容。

主线：Trial.run 捕获 CancelledError → 记录异常并发出 CANCEL → 关闭 bridge、恢复输出 → raise；异常向上传出前先执行 finally 中的 _finalize，正常收尾时停止环境、写 TrialResult 并发出 END。插件 CANCEL 标记 cancel_requested/poisoned，必要时 quiesce；END 的 _finalize_attempt 在取消分支跳过训练 bundle 提交，但仍执行 finally 中的 _close_attempt。

只讨论单次取消且清理正常完成的路径。清理失败、再次取消、进程崩溃与远端资源实际消失均未验证；不能把 finally 或 shield 当成绝对清理保证。普通异常与外部取消分开：前者可记录后返回 TrialResult，后者重新抛出，不能视为自动重试。当前尚无用户对本段的复述。


## 2026-11-16 · scope 明确 Trial.run 的当前入口

用户询问 scope 是否需要纳入 Trial.run。本次将 3.2 第一项明确为当前取消分支，并链接本步调取的完整函数卡；保留历史、补充取消局部，避免仅有远端源码链接。当前看 except 后返回 finally；未预建未读辅助函数卡，未标为掌握。


## 2026-11-16 · 将 scope 3.2 聚焦取消处理

用户确认调整 3.2，认为原范围相对快速阅读目标过大。保留局部骨架和导航表，改以 Trial.run 的 except CancelledError 为入口；编号依次对应捕获传播、CANCEL 短回查、返回 finally/END。普通失败重试和实际验证移入按需折叠，3.1 保留整体背景。原 3.2 及上下文保存到 [调整前快照](references/history/2026-11-16-before-cancellation-scope-focus.md)。未新增辅助函数卡，未声称运行验证或掌握。


## 2026-11-16 · 3.2 恢复嵌套 finally

用户要求 scope 明示 _finalize 外层仍有脱敏和日志关闭的 finally。本次恢复原嵌套关系，并说明前项抛异常后仍尝试后项，不等于保证清理成功；同步第 3 项导航。两个辅助方法仅标用途，不扩大下钻范围。


## 2026-11-16 · 明确 except 内先读什么

用户要求 scope 说明 _record_exception 开始的局部阅读顺序。3.2 将 except 拆成 1.1 记录、1.2 事件通知、1.3 关闭桥接与恢复输出、1.4 raise；当前在 1.1，只短看输入、异常字段和 traceback 写入。2 继续作为 1.2 的回调回查，3 接 finally。未建立新的辅助函数卡，未扩展实现阅读范围。


## 2026-11-16 · scope 与 Trial.run 统一当前地图

用户确认两处使用同一取消骨架和 [1]–[6] 编号。已同步 scope 3.2 与本步 Trial.run，每个导航直接落到函数卡相应段落；旧正常路径整体折叠并注明历史编号。当前仍在 [1] 记录取消，回调与收尾按主线接续，不预建六张子卡，不改旧步骤。两处骨架按文本一致性核对，原话与历史来源保留。


## 2026-11-16 · 单独展开 _record_exception

用户表示父卡的用途概括仍无法看清当前函数，要求参考之前的函数卡。按已认可的短卡格式独立展示调用现场、真实业务语句、异常字段与文件前后变化、返回 [2] 的位置；scope [1] 和 Trial.run 调用处均链接子卡。函数短，不套用长函数的多层骨架；尚无用户掌握反馈或运行验证。


## 2026-11-16 · 异常记录理解反馈与 CANCEL 接续

用户表示大概理解异常记录并认可短卡形式，原话补入 _record_exception 卡；助手区分结果字段与路径指向文件。按用户继续要求进入 [2] _on_cancel，建立短卡，标明事件交接、AttemptRecord 标记变化和返回 [3]。不展开 _safe/排空内部，未运行取消实验。


## 2026-11-16 · [3] 恢复输出也包含停止环境

用户确认继续。核对 Harbor v0.25.0 single_step.py:57–60，_recover_outputs 依次同步 Agent 输出、收集产物、停止环境；修正此前“环境停止要等 _finalize”的过度简化。当前无 bridge 时 _close_bridge 直接返回。父卡与 scope 同步补充停止位置，正常路径随后回到 raise/finally。停止标记不能代替实际资源回收验证，未深入传输或 shield 机制。
