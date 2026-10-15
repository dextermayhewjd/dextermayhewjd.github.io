# 第 26–32 课：线程学习单元实施计划

目标：按已有课程规划完成 8 个独立页面，保留 26–32 编号与全部 API；31 分为 31.1、31.2。用户已确认优先推进这一组。

约束：Python 3.12 验证；标准库独立实验；开头列出真实旧知识连接；每课一个主要关系；正常路径后补必要失败与退出；用通知确定测试顺序，不靠计时猜测线程快慢。源码背景链接到已有固定快照材料。桌面、手机及下载可用。

- [x] 26：to_thread 与 time.sleep，区别同步函数和等待入口；上下文传播留到 24。
- [x] 27：Thread 的创建、start、is_alive 与 join。
- [x] 28：Lock 保护完整读改写；with 与 acquire/release 配对。
- [x] 29：Event 的 set/wait/clear 与线程合作退出。
- [x] 30：Queue 的 put/get/get_nowait，Empty/Full 与结束消息。
- [x] 31.1：ThreadPoolExecutor.submit 与 Future 状态、结果、异常、等待超时。
- [x] 31.2：map 的结果顺序与迭代位置的异常。
- [x] 32：取消排队工作、运行中取消失败、shutdown 等待与取消待执行项。
- [x] 同步 curriculum.json、课程表、manifest、频率页状态和优先阅读入口。
- [x] 验证全部新增示例、资源退出、构建、导航、页面与下载；保持预览运行。

主要文件：content/projects/python-async-concurrency/26-to-thread 至 32-threadpool-shutdown；python-async-reference/curriculum.json；python-async-concurrency/project-manifest.json；生成器及频率状态测试。

验证重点：线程不会因取消等待者被强停；join 和 result 的阻塞属于调用线程；Event 通知后仍须 join；map 输入顺序与完成顺序不同；shutdown(wait=False) 不等于运行中的工作结束。

验证记录：课程校验 13 项、频率校验 13 项、专题校验 42 项通过；导航构建通过。浏览器检查八页 × 两种宽度、73 个本地链接与锚点；新增 11 个脚本输出一致。
