# 第 22 课源码核对

- 对照仓库：`/home/hongshi/projects/verl`；只读，工作区干净。
- 当前 HEAD：`e5a627cf55c94d85406556854c2c1a22db4ff5e7`。
- 教学绑定固定提交：`1d367a4f459a43768f76312c0d3430a99ec46b8c`，沿用四库统计快照。
- 两份源文件由本地 `git show <固定提交>:<path>` 读取，与保存快照逐字和 SHA-256 一致。
- `learning-pack.json` 保留行号、原文与完整源文件哈希。
- 主例子只保留 ensure_async_iterator 的同步输入分支；打印与 sleep(0) 是教学添加，不是原实现。
- 运行环境：Python 3.12.3；主例子、错误消费和无挂起对照均独立运行。
- 普通协程、异步生成器与上下文管理器分别核对；未提前引入 aclosing、anext 或协议类实现。
