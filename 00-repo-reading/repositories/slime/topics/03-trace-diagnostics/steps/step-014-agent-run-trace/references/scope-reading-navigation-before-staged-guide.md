# 逐步导航重构前的 3.3

2026-10-27，用户要求一点一点确定阅读内容；本文件保留改稿前的导航。[当前 scope](../01-scope.md#reading-order)继续维护正式版本。

### 3.3 打开 trace_utils.py 后怎样读

先看骨架，再打开函数卡沿①至④走完同一次调用。主线按这次运行的交接顺序阅读；辅助函数只在某一段出现疑问时回查，读完返回原位置。

```text
第一步 · 进入 with：谁启动 trace_span，记录要写到哪里       当前
    ↓
第二步 · 写开始并 yield：留下什么数据，交出什么对象
    ↓
第三步 · 回到调用方：执行业务，并向同一个对象补退出码
    ↓
第四步 · 离开 with：谁恢复 trace_span，怎样记录结束并收尾
```

| 阅读步骤与函数卡入口 | 原文件定位 | 本轮只看清什么，读完回到哪里 |
| --- | --- | --- |
| [第一步：进入](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-enter) | generate.py:286 → trace_utils.py:353–366 | 当前卡在 _coerce_handles；先读[当前 Sample 的调用与返回](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#coerce-sample-path)，得到 [handle] 后返回 362 |
| [第二步：开始与交出](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-start-yield) | trace_utils.py:369–398 | 写开始并保存编号；yield 交出 span_context，接回 generate.py:287 |
| [第三步：业务与属性](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-body) | generate.py:287–295 | span 与 span_context 是同一对象；补属性时本阶段还没有结束事件；离开 with 后恢复 398 |
| [第四步：恢复与收尾](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-exit) | trace_utils.py:412–425 → generate.py:296 | 正常退出走 else，配对写结束；finally 恢复上下文，然后继续调用方业务 |

