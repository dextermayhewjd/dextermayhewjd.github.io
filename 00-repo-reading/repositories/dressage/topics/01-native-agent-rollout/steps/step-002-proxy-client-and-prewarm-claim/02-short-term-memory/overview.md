# Step 002 · 本步函数索引

- [blackbox_dispatch.generate](functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)：调取完整主线，当前定位客户端与预热领取；不表示重新阅读全部函数。
- [get_proxy_client](functions/dressage/rollout/generate/runtime.py/get_proxy_client.md)：用户提出代理初始化与上下文登记理解，已补充客户端/服务端区别。
- [claim_prewarm](functions/dressage/rollout/prewarm/store.py/claim_prewarm.md): 领取入口，已展开源码说明。
- [PrewarmStore.claim](functions/dressage/rollout/prewarm/store.py/PrewarmStore.claim.md): 用户已串联领取流程；已补充 record、初始化 Task 与底层环境的区别。
- [PrewarmHandle](classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md): 五个交接字段与调用者用法。
- [PrewarmStore.start](functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)：用户已串联 Task 创建、登记与后续等待；已补充启动和完成的区别。
