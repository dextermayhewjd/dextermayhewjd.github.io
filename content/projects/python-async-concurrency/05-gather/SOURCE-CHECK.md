# 第 06 课 gather 核对记录

## 1. 本课边界

本课只新增“等待多个已有 Task，并按传入顺序收集返回值”。主实验沿用 03、04 的 `generate(rollout_id, seconds, started_at)`，保留 10 等 2 秒、11 等 1 秒的设置。

1. 先承认逐个 await 再组合列表能够取得结果，再引入一次等待并取得列表的需求。
2. 主实验使用已经由 create_task 安排的 Task，明确 gather 不会重启它们。
3. 参数展开、直接传协程、无计时简短版本及异常边界放在补充折叠区。
4. 正常路径的返回顺序与任务完成顺序分开。异常时不声称整组一定成功，也不把 gather 当作 TaskGroup 的全部生命周期管理替代品。

## 2. 资料与版本

- 主实验使用标准库，按 Python 3.12 默认调度核对。
- [官方 gather 文档](https://docs.python.org/3.12/library/asyncio-task.html#running-tasks-concurrently)明确正常结果按传入顺序排列；传入协程会被安排为 Task；默认异常传播不自动取消其他任务。
- `learning-pack.json` 沿用原教程 Slime 快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 中的 `generate_and_rm_group` 连续摘录。
- 三库共同使用表依据 `python-async-reference/report.json` 的各自固定版本，使用核心包静态调用位置数，不将不同版本的源码行号混用。

## 3. 迁移与兼容

03 的 gather 讲解迁到本课。原 `03-tasks/#gather-results` 留下跳转链接，`03-tasks/gather_example.py` 保留下载兼容；本课的同名简短示例与它一致。

`teaching-topics.json` 中 gather 的讲解目标改为 `05-gather/#gather-results`，并重新生成全部源码位置映射。原第 06 课及后续显示编号顺延，旧页面地址保留。相邻导航、首页、学习规划及章节交叉引用同步更新。

## 4. 验证

1. 新的结果顺序检查先因缺少本课示例而失败，加入示例后通过。观察到 11 先完成，最终列表仍为 `[10, 11]`。
2. `python3 -m unittest discover -s tests -p 'test_python_async_*.py'` 的 17 项检查通过。既有线程和 Streams 示例需要在允许本地套接字的环境中运行。
3. 03、04、05 的 `generate` 函数 AST 一致；简短示例与原 03 下载文件逐字一致；页面展示代码与可下载脚本一致。
4. 23 个章节的标题、权重、相邻导航编号与目标一致；gather 源码记录均指向新的 05 入口，旧 03 锚点及下载地址仍可访问。
5. 两份统计生成器的 `--check` 通过。Chrome 在 1280px、1920px 下确认页面无横向溢出、源码默认关闭，空格键可以展开和收起。
