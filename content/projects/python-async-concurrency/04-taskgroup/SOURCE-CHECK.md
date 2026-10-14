# 第 04 课 TaskGroup 核对记录

核对日期：2026-10-13。运行环境：CPython 3.12.3。

## 1. 教学边界

1. 沿用第 03 课的 `generate(rollout_id, seconds, started_at)`；函数 AST 一致，只替换 `main` 中创建和等待任务的部分。
2. 本课只增加“由 TaskGroup 在退出作用域时等待组内任务”的关系。`async with` 和 `as group` 在首次出现处交代最小用法。
3. 主实验只有正常结束路径。没有引入 `gather`、Task 结果读取、异常组或取消算法；正文以一句话标出失败分支，留待后续学习。
4. 开头按“已有能力 → 新增要求 → 沿用旧法”推进，只聚焦一组相关任务在哪里统一等完。承认手动 `await` 可以完成等待；提前返回和异常退出的完整规则留到后续，不作为本课的主要问题，也不声称本实验验证了这些分支。
5. 方案对照放在例子和执行过程之后。三条结论分别说明任务归属、组内语句与任务执行的区别、正常退出时的等待责任。
6. 第二部分在宽屏下将默认收起的对比入口放到 TaskGroup 主代码右侧，展开后两栏并列。保留第 03 课完整原例及其下载链接；对比时聚焦 main 中的安排与等待位置，主代码保持直接可见。

## 2. 语义依据

- [Python 3.12 Task groups](https://docs.python.org/3.12/library/asyncio-task.html#task-groups)：组内任务在异步上下文退出时被等待。
- [Python 3.12 async with](https://docs.python.org/3.12/reference/compound_stmts.html#the-async-with-statement)：异步上下文进入和退出。
- 示例使用默认任务调度。可变时间戳只用于观察；回归检查关注每份任务的先后关系，以及组外打印晚于全部任务结束。

## 3. 源码证据

使用 AReaL 固定提交 `298412a40f5b84ae6b2042987e81777e6dd0f284` 的 `areal/v2/inference_service/data_proxy/app.py` 第 1008–1024 行。代码先建立评分 TaskGroup，在退出组后读取各任务结果。

`learning-pack.json` 记录固定版本、完整文件哈希、连续原文和行号；全文件快照位于项目根目录 `python-async-reference/repositories/areal/source_snapshot/`。本资料的固定范围中，Slime 和 verl 核心包没有 TaskGroup 调用，不把这页称作三库共同高频用法。

## 4. 验证

1. 新增两个检查先出现预期失败，补齐示例和路由后通过。运行示例无 stderr，组外的 `group finished` 始终晚于两份任务的结束日志。
2. `python3 -m unittest discover -s tests -p 'test_python_async_*.py'` 共 16 项通过，包含示例输出、源码哈希、页面导航、链接、折叠默认状态和完整 Slime 覆盖映射。
3. 上述完整测试需要允许本地套接字。在受限沙箱中，既有线程实验超时、Streams 无法绑定；同一套测试在允许本地套接字的环境中全部通过，未修改这些原有实验。
4. 实际 Chrome 检查 1280px 和 390px：页面无横向溢出，AReaL 源码组默认关闭，聚焦 summary 后用空格键可以展开和收起。
5. 两份自动统计的可重现性检查通过：`build_teaching_coverage.py --check` 与 `python-async-reference/tools/build_reports.py --check`。新增教学页没有改变原始仓库统计。

显示编号在本页之后顺延，已有页面地址和源码映射中的稳定 slug 保留。网站总览、上一节和下一节入口已同步。
