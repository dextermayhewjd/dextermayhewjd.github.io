# MiniMax × Harbor 实施任务约定

- 本项目目标与边界见 README.md；引入任务工具或迁移记录不增加建设范围。
- 从本目录运行 Backlog.md。当前版本 1.54.0，filesystem-only，配置在 backlog.config.yml。由外层学习仓库管理，不初始化嵌套 Git，不自动提交或推送。
- 操作前运行 `backlog instructions overview`，再按需读 task-creation、task-execution、task-finalization。
- 任务、依赖、验收和文档通过 CLI 管理，不直接编辑 Backlog 管理的文件。1.54.0 的决策 CLI 缺少正文编辑能力，可用自带网页编辑器/API；不为此随意升级工具。
- Q04 → MH-001，Q01 → MH-002，Q02 → MH-003，Q03 → MH-004。先搜索再创建，避免恢复旧三目录或重复建卡。
- 任务状态、具体实施计划与结果只在 tasks 维护。decisions 记录已确认选择；docs 记录总体路线、候选调查及原文快照；README 记录目标和导航。
- doc-001 是迁移前原文，只供追溯，其旧状态和旧链接文字不是当前操作指令。doc-002 是总体路线，doc-003 是接口调查。decision-001 保存已确认的范围。
- 只保存真实直接依赖，阅读建议顺序不等于阻塞；未验证不标 Done，静态核对、建卡和迁移不算实际功能完成。
- 实际代码与测试在对应源码仓库；任务记录源码版本、提交与验证证据。密钥不写入文档。
