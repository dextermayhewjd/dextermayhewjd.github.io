---
title: "学习路线与完成标准"
description: "8 个模块、41 个编号单元；取消和整组失败在前，完成顺序与时间预算在后。"
weight: 900
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideSummary: true
---

## 1. 每次只学一个新问题

全课分成 **8 个模块、41 个编号单元**，最终包含已选定的 **98 项 API/方法**，以及理解它们必需的语法和异常类型。第 10、11、20、21、23、24、28、31、33、35、36 单元按问题拆成子课，01–41 主编号保持不变。

**01–22、24–38 已整理完成；23、39–41 仍按规划补写。** 这是正文编写状态，实际阅读进度与本轮优先内容见下面的续学表。旧 URL 保留，不能用网址数字推断新课号。

本专题只讲 Python 原生异步与并发。每个单元只增加当前必要的关系；源码与完整位置清单放在各页末尾按需展开。

<span id="priority-reading"></span>

<span id="reading-status"></span>

### 当前学习记录

**2026-10-16：36.2 尚未读懂，暂时跳过，不计为已掌握。** 待回访的问题是 `to_thread` 与 `run_coroutine_threadsafe` 的必要性、协程创建和执行的位置，以及两次结果返回的方向。

**2026-10-17 当前学习第 24 单元：ContextVar。** [24.1 · ContextVar.set / get：保存每份任务自己的值](../11-contextvars/)已初步理解，当前继续 [24.2 · ContextVar.reset：用 token 恢复修改前的值](../24-contextvar-reset/)；整课尚未标记为掌握。

**2026-10-18 当前先看 RLock。** 从 [28.1 · Lock](../28-thread-lock/) 回顾互斥，再进入 [28.2 · RLock：允许同一线程嵌套加锁](../28-thread-rlock/)。ContextVar 的 token/reset 留待继续，尚未标记为掌握。

此前短补：[call_later：定时登记与 Slime 分批放行](../loop-call-later/)。 先分清立即登记、到期和实际执行，再用 Slime 的 AsyncPacer 观察分批放行。[call_soon 的完整教学](../loop-call-soon/)保留供回顾；36.2 仍暂缓。下面保留课程的基础顺序，供回查使用。

<span id="supplement-lessons"></span>

### 补充教学（不编号）

这里负责学会机制：从问题、完整代码和实际输出出发，逐步解释执行过程与用途。左侧在第 38 课后直接列出：

- [call_soon：登记回调、Handle 与执行](../loop-call-soon/)
- [call_later：定时登记与 Slime 分批放行](../loop-call-later/)

<span id="function-comparisons"></span>

### 函数对比（关系摘要，不编号）

[进入函数对比目录](../comparisons/)。这里用少量文字、对照表和关系句归纳接口的共同点、差别与选择条件，供复习和后续画思维导图。第一次学习或有疑问时，返回对应的完整教学。

已有三份摘要：[create_task 与 loop.call_soon](../comparisons/call-soon-vs-create-task/)、[call_soon 与 call_later](../comparisons/call-soon-vs-call-later/)、[Lock 与 RLock](../comparisons/lock-vs-rlock/)。它们位于单独的“函数对比”分组，不承担逐步教学。

### 基础回顾与后续路线

先用不涉及线程的例子，分清结果对象、提供者与等待者；再把这套理解用于线程池。第 20 单元的四节基础放在 Event 之后，第 33 单元继续保留远端版的四节拆分。

| 顺序 | 学习单元 | 本次要看清什么 |
| --- | --- | --- |
| 1 | [20.2 · get_running_loop：取得正在运行的事件循环](../20-running-loop/) | 取出已有循环，不创建另一份工作 |
| 2 | [20.3 · create_future / set_result：保存一次完成的结果](../20-future-result/) | 先保存再读取，分清 Future 与结果值 |
| 3 | [20.4 · await Future：等待别处交付结果](../20-await-future/) | 等待者挂起，提供者完成，同一个 Future 连接两边 |
| 4 | [20.5 · Future 的状态与异常](../20-future-state/) | 区分等待、读取、失败和重复完成 |
| 5 | [33.1 · 回顾当前循环](../33-current-loop/) → [33.2 · 指定线程池](../33-run-in-executor/) → [33.3 · 并发交接](../33-await-handoff/) → [33.4 · 循环时钟](../33-loop-time/) | 保留提交、等待实验与时间预算的分节讲解 |
| 6 | [34 · wrap_future](../34-wrap-future/) | 接回已经提交的工作，不重新提交 |
| 7 | [35.1 · 复习状态与取消](../35-future-results/) / [35.2 · 复习结果交付与源码](../35-future-completion/) | 按需复习，第 20 单元已正式引入的 API 不重复计数 |
| 8 | [35.3 · Task.add_done_callback](../35-task-callbacks/) | 在已有结果机制上新增完成回调 |
| 9 | [36.1 · 手动管理事件循环](../36-manual-event-loop/) → [36.2 · 跨线程提交协程](../36-threadsafe-submit/) | 36.2 尚未读懂，暂时跳过，保留回访入口 |

**基础顺序是 20.2–20.5，再到第 33 单元。** 当前阅读位置以上方学习记录为准。已经熟悉 Future 基础时，35.1–35.2 可按需回顾，35.3 继续正式讲解完成回调。既有后续章节与 URL 全部保留，不用等全部 41 单元学完才进入 Slime 普通样本生成链。

| 基础与后续补充 | 在 Slime 中解决什么 |
| --- | --- |
| 已讨论 36.1：创建、运行、关闭事件循环；配套 run_forever / stop | AsyncLoopThread 让后台线程的循环持续处理工作 |
| 暂缓 36.2：run_coroutine_threadsafe；配套 call_soon_threadsafe | 尚未读懂；以后回访从另一线程提交协程、通知循环停止的关系 |
| call_soon / call_later | AsyncPacer 安排本批、下一批等待者继续，接上已经学过的 Future 完成 |
| current_task；Agent 分支再补 Task.get_loop | 找到当前请求对应的任务，或把清理工作交回任务所属的循环 |

这些是具体源码需要的补充，98 项正式 API 的统计范围不变。遇到 dp_rank_context 的 @contextmanager 时，再与 21.4 的异步版本作同步对照。普通批次生成里的 create_task、Semaphore、gather、wait、result、to_thread、取消与收尾已经有对应课程。

如果进一步读持续生成的 fully-async 分支，再补第 30 课的线程队列与 threading.Condition；不把这一分支的全部基础提前塞进普通生成路径。核对基于已保存的 Slime 22a89f9 快照，未将已编写课程当作整套框架掌握度。

已经学过的 [34 · wrap_future](../34-wrap-future/)和 [25 · inspect](../25-inspect-awaitable/)可用于回顾对象身份。[37 · subprocess.run](../37-subprocess-run/)与新写的 [38 · Popen / communicate](../38-popen-communicate/)保留，进程线先停在这里。

[统计表](../api-frequency/)当前按以下规则标色：单项 API 的四库同类占比至少 1% 标蓝；Slime 列的 API 或语法次数大于等于 5 单独标红，其余三库仍按至少 10 次标橙。这是静态位置数，不是运行时频率或学习完成度。此次补课按主链实际依赖选择，不要求每项都有高频标色。

侧边导航保留已讨论和当前阅读的内容。20、24、28、31、33、35、36 各自按小节分组，第 24 课显示 24.1 与 24.2，第 28 课显示 28.1 Lock 与 28.2 RLock，第 36 课显示已发布的 36.1、36.2。第 30、32 课继续隐藏；23、39–41 先留到对应场景，41 个主编号与原定 98 项 API 目标不变。

每次按这个顺序学习：

1. 确认本单元列出的前置已经理解。
2. 只解决本单元的问题，预测并运行主例子。
3. 能复述原子结论并完成自查，再进入下一单元。
4. 模块结束时回看等待、结果和退出是否能串起来；全课结束时再做只含已学机制的综合自查。

### 忘了前面的内容时

打开[知识地图与回忆练习](../knowledge-map/)，每次选 1–3 个概念。先写一句自己的解释，再核对概念关系、预测短代码的输出，最后记下错因与下次回忆时间。

地图按“工作怎样开始、如何等待、怎样收尾、取消影响谁、任务如何协调、资源如何退出”连接 01–22 单元。它方便复习，不改变下面的学习顺序；课程已编写完成，也不等于你已经掌握。

{{< python-async-curriculum >}}

## 完成全课时检查什么

1. **98 项调用/方法都有正式讲解。** 仅在代码里出现、作为辅助展示或放进源码清单，不算完成解释。
2. **相关语法和异常没有遗漏。** 包括 `async with`、`async for`、异步生成器、`try/finally`、`except*`，以及取消、未完成读取、队列空满和子进程超时。
3. **能解释边界。** 分清安排与执行、任务与结果、协程挂起与线程阻塞、取消请求与真正退出。
4. **能观察失败和清理。** 不只会运行正常路径，还能指出异常、取消与超时之后谁负责等待和释放。

课程规划已做逐项映射检查；当前正文完成状态仍以上方说明为准，不把规划覆盖当作已经掌握。

新增范围依据四库总调用量加权筛选：合计覆盖 **1614/1899（85.0%）**，扩充前为 1528/1899（80.5%）。当前各库为 verl 81.2%、AReaL 87.6%、Slime 87.8%、Miles 82.9%；这是调用位置覆盖，不代表运行频率或掌握程度。七组新增接口和四项必要配套的具体次数见[完整 API 统计](../api-frequency/)。Condition、进程池、信号和低层 I/O 仍按需补充。

[从第 01 课开始](../01-async-def/) · [返回专题首页](../) · [版本与参考](../references/)
