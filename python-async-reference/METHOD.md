# 统计与匹配规则

1. 扫描范围以每个 Git 仓库的 git ls-files 为准，仅解析已跟踪 Python 文件；版本、工作区差异与逐文件哈希在 inventory.json 中。
2. 调用、非调用引用、导入、语法节点分别计数。同一个调用表达式不再重复算成引用。
3. 构造函数、已知工厂或注解提供的方法接收者线索放在 inferred_method；它们仍是静态推断，不是运行时类型证明。
4. 同名但未知类型的方法只列为 instance_candidate。不把 Ray、HTTPX、aiohttp、业务对象的方法计成 asyncio。
5. 官方 loop.method 展示名规范到 asyncio.AbstractEventLoop.method；已知执行器、队列子类的继承方法可映射到其基类文档。原名称和证据保留。
6. inspect、contextlib、typing、collections.abc、builtins、unittest 等较大文档仅选择与异步相关的条目，选择集合保存在 report.json。
7. 文档符号目录包含零命中 API。某 API 被多页描述时，页面统计会重叠；逐 API 总矩阵按规范名去重，不能累加页面数字当仓库总量。
8. 文档之外的已识别 API 与未知接收者候选分别导出；二者不能相互替代。没有条目被悄悄丢弃。
9. 这是静态清单：不证明分支实际执行、调用频率、并发正确性或学习掌握程度；不解析运行时 monkey patch、动态导入、任意跨函数数据流和反射。
10. 本资料夹不运行模型、训练、GPU、远程 RPC 或部署；文档获取只访问 Python 官方站点。
