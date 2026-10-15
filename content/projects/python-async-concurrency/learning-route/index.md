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

全课分成 **8 个模块、41 个编号单元**，最终包含已选定的 **97 项 API/方法**，以及理解它们必需的语法和异常类型。第 10、11、21、23、31、33、35、36 单元按问题拆成子课，01–41 主编号保持不变。

**01–22、26–33 已整理完成；23–25、34–41 仍按规划补写。** 这是正文编写状态，实际阅读进度与本轮优先内容见下面的续学表。旧 URL 保留，不能用网址数字推断新课号。

本专题只讲 Python 原生异步与并发。每个单元只增加当前必要的关系；源码与完整位置清单放在各页末尾按需展开。

<span id="priority-reading"></span>

### 现在从哪里继续：只列未读的蓝黄重点

按本轮对话，01–22、26–29 已经讨论过，先从续学列表中移出；其余内容里只把[统计表](../api-frequency/)出现蓝色或黄橙色的课程列为本轮重点。完整课程与已有正文继续保留，暂缓不等于删除或已经学完。

侧边的当前学习导航保留已讨论及正在学习的章节。31.1、31.2 归在同一个第 31 课目录组内；现在进入的 33.1、33.2 同样归在第 33 课下，阅读任一小节时自动展开所在组。第 30、32 课继续隐藏。下表保留重点阅读入口，便于按当前侧重推进。

蓝色表示单项 API 的四库合计占同类总量至少 1%；黄橙色表示某个仓库至少出现 10 次。下面都属于调用位置，百分比的分母统一为 **1899**，是被标注 API 的占比，不是整节课的合计占比。

<div class="async-api-reference">

| 本轮顺序与课程 | 统计表中的标注依据 |
| --- | --- |
| **1. [31 · ThreadPoolExecutor：提交并收集线程池工作](../31-threadpool-submit/)**，先看已有的 31.1 | `ThreadPoolExecutor`：<span class="api-frequency-mark api-frequency-mark--total">31 次 / 1.63%</span>；<span class="api-frequency-mark api-frequency-mark--repo">AReaL 13 次</span>、<span class="api-frequency-mark api-frequency-mark--repo">verl 10 次</span> |
| **2. [33 · get_running_loop / run_in_executor：使用当前事件循环](../33-run-in-executor/)**，先读 33.1 | `get_running_loop`：<span class="api-frequency-mark api-frequency-mark--total">42 次 / 2.21%</span>；<span class="api-frequency-mark api-frequency-mark--repo">AReaL 19 次</span> |
| **3. [34 · asyncio.wrap_future：等待已有的执行器 Future](#curriculum-stage-bridges)** | `wrap_future`：<span class="api-frequency-mark api-frequency-mark--total">21 次 / 1.11%</span>；<span class="api-frequency-mark api-frequency-mark--repo">verl 12 次</span> |
| **4. [25 · inspect：辨认函数与可等待对象](#curriculum-stage-protocols)** | `iscoroutinefunction`：<span class="api-frequency-mark api-frequency-mark--total">23 次 / 1.21%</span>；<span class="api-frequency-mark api-frequency-mark--repo">verl 12 次</span>、<span class="api-frequency-mark api-frequency-mark--repo">Miles 10 次</span> |
| **5. [37 · subprocess.run：运行并等待外部命令](#curriculum-stage-processes)** | `subprocess.run`：<span class="api-frequency-mark api-frequency-mark--total">26 次 / 1.37%</span> |

</div>

**现在从 [33.1 · get_running_loop / run_in_executor](../33-run-in-executor/) 继续。** 先沿“工作线程 → 线程池 → 接回协程等待”学习 31、33、34，再补 25 的对象辨认，最后进入 37 的外部命令。31、33 已有独立正文；其余表内课程目前链接到规划，后续按此顺序补写。

第 30 课本轮暂缓；31、33 中未标色的配套内容只展开理解重点所需的部分。第 37 课按当前规划还需要第 32 课的退出与收尾概念，到那里时单独短补，不能把它冒称为高频。23、24、35、36、38–41 也先放到后续；完整的 97 项 API 目标与课程编号不变。

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

1. **97 项调用/方法都有正式讲解。** 仅在代码里出现、作为辅助展示或放进源码清单，不算完成解释。
2. **相关语法和异常没有遗漏。** 包括 `async with`、`async for`、异步生成器、`try/finally`、`except*`，以及取消、未完成读取、队列空满和子进程超时。
3. **能解释边界。** 分清安排与执行、任务与结果、协程挂起与线程阻塞、取消请求与真正退出。
4. **能观察失败和清理。** 不只会运行正常路径，还能指出异常、取消与超时之后谁负责等待和释放。

课程规划已做逐项映射检查；当前正文完成状态仍以上方说明为准，不把规划覆盖当作已经掌握。

新增范围依据四库总调用量加权筛选：合计覆盖 **1609/1899（84.7%）**，扩充前为 1528/1899（80.5%）。当前各库为 verl 81.2%、AReaL 87.6%、Slime 85.6%、Miles 82.9%；这是调用位置覆盖，不代表运行频率或掌握程度。六组新增接口和四项必要配套的具体次数见[完整 API 统计](../api-frequency/)。Condition/RLock、进程池、信号和低层 I/O 仍按需补充。

[从第 01 课开始](../01-async-def/) · [返回专题首页](../) · [版本与参考](../references/)
