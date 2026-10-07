# slime 当前源码：文件图与跨文件函数链

本轮按用户已确认的 A 方案实现本地原型。主线程负责最新源码、岗位顺序、第一章阅读合同和源码测试；网站侧负责双视图、准确源码定位与范围进度。本阶段不提交、推送或发布。

## 来源与范围

- 当前基准由主线程核对为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。真实第一章内容只能从该最新快照重新提取；版本号用于引用一致性，不作历史教学。
- 不复用旧 `8c17` 的章节内容、5 个 views、26 个 steps、milestones 或成长叙事。阶段、目标、调用边和边界由新合同提供。
- 合同未到达前只用标记 `fixture: true` 的合成交互夹具。夹具不代表 slime，保存在 tests/fixtures，不能进入正式发布内容。
- 不把点击、悬停、展开、阶段选择或图构建成功记录为已学。

## 两个联动视图

文件图按真实 path 聚合，不按模块别名重复计算。文件显示未记录自检、部分完成、本章范围完成；没有本章目标的文件显示本章未纳入。它同时列出未覆盖定义或更深目标。

函数链将函数放在所属文件容器内，显示当前阅读阶段的重点和真实接口。函数点击打开准确源码，并反向标出文件；文件选择标出该文件中的函数。阶段切换不改源码版本、节点位置或调用关系。收尾、异常与等待边由最新源码合同决定。

文件容器用 `g[data-file-id]` 和 `rect[data-file-group]`；函数节点用 `rect[data-stage][data-source-ref]`。容器背景不得作为普通 data-stage 节点。连线继续使用 data-from/to/kind/label/route，区分流程与引用。

## 数据合同

以主线程的 learning-pack v1 为正式合同，不另维护源码目录。网站页面资源保留原 learning-pack.json，并从中导出 SVG 与阅读器索引；模块配置只是呈现投影。字段为：

```text
schemaVersion: 1
chapterId, title, repository, revision, generatedAt
fixture: true 只用于合成测试与本地演示
inventory: [{path, category, group, inChapter}]
files: {path: {blobSha256, totalLines, functions: [{symbol,line,endLine}], text}}
references: {refId: {available,revision,path?,symbol?,line?,endLine?,blobSha256?,text?,reason?,label}}
views: [{id,label,description,steps: [{id,goalId,progressKey,label,kind,depth,summary,inputs,returns,effect,condition,caller,callee,files}]}]
functionReferences: {path::symbol: 完整定义引用ID}
```

path 必须是仓库相对路径，行范围为正整数。step.caller 与 step.callee 使用准确引用 ID，symbol 显示限定名。text 为对应行范围的源码摘录，完整 SHA、路径、限定名与行范围在源码面板同时可见。不可用的引用显示 reason 并禁用源码跳转，不能伪造实现；不从旧 catalog 补行号。

stageFunctions 与 codeFunctions 绑定引用 ID，不再用裸 def 名。一个调用处可以没有 def，一份文件也可能有多个同名方法。点击函数图打开 canonical 完整定义；步骤的调用处／实现处按钮打开各自准确窗口。source-reference shortcode 生成带引用 ID 的源码块；旧 LCC 页面仍保留原裸名索引。

## 学习状态

目标身份使用源端 progressKey，绑定 repository、revision、目标内容、源码范围与 depth；goalId 只用于逻辑导航。网站另校验当前引用元组，范围或深度变化不继承旧自检。

goal 的状态由读者逐项显式自检确认；文件只聚合本章目标。范围完成并不表示整个函数或文件掌握。例如会话导出入口的合同目标完成，轨迹算法仍可列为未覆盖目标。

当前焦点用紫色边框；未记录、部分、本章范围完成分别用灰、橙、蓝。使用独立 reading 图例，不能沿用新增/修改/任务运行的含义。点击选中仅加粗线与边框，不改学习状态。

本机保存仅发生在读者显式确认或撤销自检时。localStorage 的键包含版本、仓库、快照与章节；记录还校验每个目标的范围与深度。焦点、展开与阶段选择不保存。存储不可用时仍可阅读；恢复视图不清记录，清除自检有单独按钮。

## 文件职责与兼容

- assets/js/reading-progress.js：来源校验、范围状态与记录序列化，无 DOM 依赖。
- assets/js/reading-view.js：阶段、自检、本机保存、文件状态与双图联动。
- architecture-explorer：通过可选 reading 参数接入；原有源码面板、窗口调整、箭头追踪与键盘操作继续复用。
- source-reference：输出源码身份与原文，不以函数名猜测范围。
- reading 图例与样式仅作用于选择该模式的图。
- tests/fixtures/reading-prototype：合成代码和图，测试同名方法、未覆盖项与作用域聚合。

## 验收

1. 跨文件同名 run 以及没有 def 的调用片段均定位正确。
2. 阶段与图形操作不改变自检记录；只有显式自检会改变进度。
3. 空目标不算完成；部分目标与本章范围完成正确聚合，未覆盖项继续显示。
4. SHA、范围或深度变化不继承旧自检，本机保存失败不阻塞阅读。
5. 双图选择联动，源码引用、键盘、窄屏、ID 命名和无脚本回退可用。
6. 新合同未确认时夹具不能被描述为实际 slime；原 LCC 测试全部兼容。
