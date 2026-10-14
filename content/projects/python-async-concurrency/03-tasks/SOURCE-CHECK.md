# 第 03 课：create_task 的讲解核对

本次按已确认的教学顺序调整：回顾 01/02 → 直接 await 的顺序 → create_task 提前安排 → await Task 取得结果。正文只增加 create_task；gather 已迁到独立的第 05 课，原三组交错实验仍为独立折叠选读。

章节开头按“已知能力 → 新增要求 → 尝试旧法”组织：直接顺序 await 可以得到两个结果，但尚未满足两份独立工作在等待期间交错推进的要求。原回顾表、代码和输出保留，在观察旧写法之后才引入 create_task。

## 固定依据

- 核对日期：2026-10-13。
- Python：本机 CPython 3.12.3，默认任务调度；不把具体交错顺序推广到自定义或 eager task factory。
- Slime：沿用本专题固定快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，未更新源码版本；本轮核对本仓库保存的快照与 `learning-pack.json`，不声称重新查询了官方分支。
- 示例均为独立的标准库语言实验，没有运行 Slime、模型服务或训练。

## C01 · 创建和等待 Task

核对事实：`create_task` 安排协程并返回 Task；直接等待已有 Task 不会重启该协程；先等待一份已创建的 Task，不妨碍其他就绪任务在调用方挂起期间推进。

依据：本机 `asyncio.tasks.create_task`、`asyncio.tasks._PyTask.__init__`；后者默认使用 `loop.call_soon` 安排任务步骤。

实际执行：运行 `sequential.py` 与 `example.py`。两者使用同一个 `generate(rollout_id, seconds, started_at)`；10 等待 2 秒，11 等待 1 秒。`time.perf_counter()` 记录相对时间，只用于观察，不参与调度。

- 顺序等待：10 在约 0 秒开始、约 2 秒恢复，然后 11 才开始并在约 3 秒恢复。
- 提前安排 Task：10、11 都在约 0 秒开始等待；11 在约 1 秒恢复，10 在约 2 秒恢复。`main` 等 10 返回后才依次收到 10、11，最终结果仍为 `[10, 11]`。
- 这证明当前例子中的等待重叠与结果收取顺序，不构成精确的计时或调度保证。回归检查只忽略日志的可变时间前缀，仍逐行核对事件及其顺序。
- 正文说明协作式让出执行机会；没有使用 TaskGroup，也没有创建额外工作线程。

## C02 · 已迁至第 05 课：gather 收集结果

核对事实：`gather` 接收 Task，也能通过内部 `_ensure_future` 安排传入的协程；正常完成时按传入顺序遍历子任务、组装结果。`*tasks` 是 Python 参数展开。

依据：本机 `asyncio.tasks.gather` 的子任务创建和结果收集逻辑，以及 [Python 3.12 官方文档](https://docs.python.org/3.12/library/asyncio-task.html#running-tasks-concurrently)。

实际执行：核对直接传协程得到 `[10, 11]`；核对完成顺序为 `[11, 10]` 的两个 Task 交给 `gather` 后仍得到 `[10, 11]`。正文对整组结果的说明限定于正常完成，异常行为放入单独补充。

## C03 · Slime 的组级任务组织

调用处：[`generate_and_rm_group` 固定源码](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L404-L416)。

核对本仓库 `python-async-concurrency/source_snapshot/slime/rollout/sglang_rollout.py.txt` 的第 404–420 行：循环用 `create_task(generate_and_rm(...))` 安排单样本任务，存入 `tasks`；第 415 行用 `group = await asyncio.gather(*tasks)` 接收整组结果，随后进入组级处理。未展开单样本业务实现。

## 保留与检查范围

- `example.py` 改为两份 Task 分别 await 的主实验；`sequential.py` 是同一生成函数的直接 await 对照；原 gather 实验另存为 `gather_example.py`。
- 原 `comparison.py` 和 Slime 摘录保持不变，正文中的相关下载已同步。
- 保留 `task-creation`、`gather-results`、`comparison-b`、`sleep-key-point` 四个显式锚点；其中旧 `gather-results` 保留为第 05 课的跳转入口。
- Slime 对照与全量源码位置统一放入页面末尾默认关闭的阅读区；原正文代码块、源码引用和显式锚点保留。
- 页面检查覆盖渲染后的正文顺序、折叠默认关闭、锚点及专题链接。专题与覆盖测试合计 14 项通过。
- Chrome 检查第 03、13、19 页在 1280px 与 390px 下的焦点、展开、收起、源码可见性和横向溢出。检查时仅在临时代理页面禁用主题过渡动画；未修改网站动画，未验证真实键盘按键事件。

第 05 课沿用同一份 `generate` 并扩展结果收集实验；03 的原 `gather_example.py` 下载地址保留，新入口与简短示例位于 `05-gather/`。
