# slime 阅读双视图实现计划

> 执行方式：本会话按任务逐步实现，先验证状态与源码身份，再验证本地原型。用户已授权按可行方案推进；本轮不 commit/push/deploy。

**目标：** 在网站复用源码阅读器，为最新 slime 第一章准备文件覆盖图、跨文件函数链与按范围自检的本地原型。

**架构：** 直接消费主线程 learning-pack v1，新 stages 由 views/steps 提供。纯状态模块和 DOM 阅读模块分开；现有 architecture-explorer 只增加可选来源索引与通知接口，无 reading 参数的页面维持原行为。

**技术：** Hugo Extended、原生 JavaScript、SVG、Python unittest 与本地 Chrome；不新增运行时外部依赖。

**设计：** [slime-reading-design](../specs/2026-10-07-slime-reading-design.md)。

## 全局约束

- 当前真实基准为 2f2318653f6f794dddd321eff7c9d4b7b174643f；正式内容等待主线程重新提取的合同，不读旧 8c17 内容。
- 夹具明确 fixture: true、独立仓库与测试 SHA，不混入正式 content。
- 点击不算学习；范围自检不算整函数或整文件掌握。
- 无 reading 参数时不改变 LCC 行为；不发布或改部署配置。

## 任务 1：准确源码身份与范围状态

文件：新增 assets/js/reading-progress.js、tests/test_reading_progress.py。

接口：ReadingProgress.create(config) 返回模型，提供 selectView(id)、checkGoal(id, checked)、fileStatus(id)、sourceStatus(id)、snapshot()、restore(record)。ReadingProgress.sourceURL(config, sourceId) 返回固定 SHA 的行范围链接。

- [ ] 写真实浏览器测试：两个文件同名 Worker.run 的链接不同，调用片段无 def 也有准确身份。
- [ ] 验证阶段选择不增加任何目标完成记录；无本章目标的文件为 out-of-scope。
- [ ] 验证一个目标完成只改变其范围；另一个目标未完成时文件为 partial，未覆盖项始终存在。
- [ ] 验证恢复必须匹配 SHA、行范围、scope；非法相对路径与错误行范围拒绝。
- [ ] 执行测试，记录 API 尚未实现的失败，再完成状态模块并复验。

行为断言示例：

```javascript
const m = ReadingProgress.create(config);
m.selectView('execution');
check(m.snapshot().checks.length === 0, '切阶段不能记完成');
m.checkGoal('trace-a', true);
check(m.fileStatus('worker-a').status === 'partial', '仅部分目标完成');
```

## 任务 2：源码块与现有阅读器接入

文件：修改 layouts/shortcodes/architecture-explorer.html、assets/js/architecture-explorer.js；新增 layouts/shortcodes/source-reference.html。

接口：source-reference 从 learning-pack.json 的 references 输出 section[data-source-ref] 内的元数据与代码；architecture-explorer reading 参数加载该页面资源并输出 data-reading-config。阅读器按 sourceRef 索引源码；选择通知使用 diagram:selection 和 diagram:function-selected。

- [ ] 增加夹具与失败的浏览器断言：点击同名 run 的两个链接，应分别打开所属文件的代码。
- [ ] 显式来源块优先按 sourceRef 索引；现有 bare-def 索引继续供 LCC 使用。
- [ ] 复用原源码面板，只提供来源显示标签与选择通知，不伪造新 def 名。
- [ ] 新阅读配置缺失或损坏时不能静默借用另一个函数；保留原正文与准确外链作为回退。

## 任务 3：双视图、自检与本地原型

文件：新增 assets/js/reading-view.js、assets/css/extended/reading.css、tests/test_reading_explorer.py、tests/fixtures/reading-prototype/；修改 architecture-figure 与 architecture-legend partial。

接口：ReadingView.attach(root, config) 绑定模型、阶段控件和事件；只在 reading 配置存在时运行。clone 的局部图同样同步阅读状态。

- [ ] 测试文件点击定位该文件函数、函数点击反向标文件；节点坐标和调用边不变。
- [ ] 添加阶段按钮、逐项自检、只在显式自检后本机保存和独立清除按钮；所有学习文案强调自报与本章范围。
- [ ] 同步全局文件图、当前链与局部副本；文件容器背景不参与函数连线判定。
- [ ] 使用真实 localStorage 验证保存、刷新恢复、版本隔离，以及点击前后记录完全相同。
- [ ] 验证键盘、390/1180/1600 宽度、源码字段、图例与无脚本回退。
- [ ] 夹具通过临时 Hugo content mount 构建，本地预览来自 /tmp，不添加到正式网站内容。

浏览器断言示例：

```javascript
const before = localStorage.getItem(storageKey);
sourceLink.click();
check(localStorage.getItem(storageKey) === before, '读源码不能自动记学习');
```

## 任务 4：新合同与回归

- [ ] 主线程合同到达后核对 repo、完整 SHA、每条 caller/callee 的路径、限定名和范围；先转换为网站呈现投影再接真实章节。
- [ ] 正式投影与 2f231 最新源码逐条核对；测试夹具只验证 UI，不作为源码证据。
- [ ] 执行 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests；执行 bash tests/test-project-navigation.sh 与 Hugo 生产构建。
- [ ] 对照设计记录已完成部分、失败／跳过和真实合同接入状态；保持本地未发布，由主线程审查接续。

## 审查重点

- 新 SHA、范围或深度变化时记录不可误继承：任务 1／3 的恢复测试负责。
- 同名函数与无 def 调用处不能串片段：任务 1／2 的来源定位测试负责。
- 空目标和保留给后章的算法不能变成全文件完成：任务 1／3 的覆盖测试负责。
- 私有模式或损坏的浏览器记录仍可读源码：任务 3 的存储回退测试负责。
- 夹具、旧源码或局部运行结果不得混成最新源码事实：任务 4 的来源核验负责。
