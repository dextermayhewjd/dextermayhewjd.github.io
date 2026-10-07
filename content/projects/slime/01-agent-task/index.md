---
title: "进阶串联：Coding Agent 单任务闭环"
weight: 900
hideInOverview: true
summary: "阅读最新 slime 的单任务闭环，按真实文件与调用引用追踪工作区、Harness、patch、评估、导出和清理。"
draft: false
ShowToc: false
compactDiagramLegends: true
---

{{< chapter-outline id="slime-task-outline" title="本章阅读路径" >}}

## 1. 我想弄清楚的问题 {#task-question}

一个 Sample 如何成为 Coding Agent 的任务，如何把代码改动交给独立评估，最后变成训练样本或失败结果？这一章只追踪调用与数据合同，不把 CLI、轨迹算法或整个文件都当作已经学完。

来源为 [THUDM/slime](https://github.com/THUDM/slime)，本轮快照为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。所有代码从该版本的 Git blob 导出，版本仅用于保持引用一致；阅读阶段不是历史成长。源码摘录遵循同版 [Apache 2.0 许可](./SOURCE-LICENSE.txt)。

## 2. 文件覆盖图与当前函数链 {#task-diagrams}

{{< architecture-explorer id="slime-task-reader" reading="learning-pack.json" modules="explorer.json" roles="function-roles.json" src="images/files.svg" width="1200" legend="reading" caption="图 1：五个本章文件与全部原生路径。文件完成仅指本章 trace 范围自检；其余 640 文件未纳入。" >}}

{{< architecture figureId="slime-task-chain" functionExplorer="slime-task-reader" trace="true" src="images/chain.svg" width="1000" legend="reading" caption="图 2：函数按实际文件容器组织，点击函数查看准确完整定义；上方“调用处／实现处”查看本步引用范围。每条线标明接口与条件；源码存在与引用范围已校验，跨文件绑定按本轮课程对照，不是静态解析器对运行关系的证明。" >}}

## 3. 按当前阅读阶段追踪 {#task-stages}

五个视图使用同一份当前源码，逐步关注输入、会话、执行产物、独立评估、导出与清理。上方步骤说明展示问题、输入、输出、副作用与条件；“调用处／实现处”打开不同的准确引用。

成功退出码不等于评估通过；工作目录中的修改还要被捕获，再按任务协议独立评分。训练轨迹导出与评估占位结果是不同分支，具体路径由当前步骤的条件说明。

## 4. 本章理解的边界 {#task-boundaries}

本章 25 项目标都是 trace：能追踪是谁调用、输入来自哪里、返回与副作用去了哪里。只在你显式确认“已理解本步（自报）”后才写本机记录；点图、读源码与切视图均不自动计入。

`BaseAdapter.finish_session` 在本章只追踪导出合同，轨迹拆分与对齐留待后章。外部 Agent CLI 和 E2B SDK 没有仓库内的完整实现，界面会显示边界原因并禁用假源码跳转。文件目录还列出本章未覆盖的静态定义。

本页面是本地原型，验证的是源码引用和网页交互；本轮没有运行模型、CLI、沙箱或训练。

## 5. 固定版本的源码引用 {#task-sources}

<details>
<summary>展开步骤引用与完整定义（39 段可读源码、2 个外部边界）</summary>

{{< source-reference id="ref_48e5b39f3b04f17745aa" >}}

{{< source-reference id="ref_4c6ca49146189b82fe3a" >}}

{{< source-reference id="ref_a524943e1cdb73604891" >}}

{{< source-reference id="ref_841d44afe66454a14945" >}}

{{< source-reference id="ref_12fd87846f14dc1f7cc0" >}}

{{< source-reference id="ref_04f27441abaa3dad3efa" >}}

{{< source-reference id="ref_f80dd1f8dbfd9c822337" >}}

{{< source-reference id="ref_7d871d94225e6ea94c46" >}}

{{< source-reference id="ref_339e507f24b8cc845784" >}}

{{< source-reference id="ref_1d80f579e94447f42e9f" >}}

{{< source-reference id="ref_6163b92ea527474639a4" >}}

{{< source-reference id="ref_69b33de09561cb5e2188" >}}

{{< source-reference id="ref_dbabc34e61f304d9dc52" >}}

{{< source-reference id="ref_0b6526f03cb8f9109bcd" >}}

{{< source-reference id="ref_394db266157b7e10367d" >}}

{{< source-reference id="ref_a148ec7e6477c757c7ea" >}}

{{< source-reference id="ref_a073485fa3f7b92024f4" >}}

{{< source-reference id="ref_2ec90e943543c22e649e" >}}

{{< source-reference id="ref_7d006b63f1248831b119" >}}

{{< source-reference id="ref_150d2fd2b9062c14a74f" >}}

{{< source-reference id="ref_4a6f322587319d1d7c81" >}}

{{< source-reference id="ref_71545e29cccdfd14f263" >}}

{{< source-reference id="ref_418df14117afd35e9b55" >}}

{{< source-reference id="ref_edc6b9ef089749108c22" >}}

{{< source-reference id="ref_451df8189c4d9a5e4cfd" >}}

{{< source-reference id="ref_1844a2faf8496148380f" >}}

{{< source-reference id="ref_1aaf9e7a5601f3d617ac" >}}

{{< source-reference id="ref_d43fbe9f11c8c316d16d" >}}

{{< source-reference id="ref_028a31f4e7d3a53dc92f" >}}

{{< source-reference id="ref_eaa4d28f001a0057d08c" >}}

{{< source-reference id="ref_da8519fb210945772b6c" >}}

{{< source-reference id="ref_fed9087cb06d20e8ed23" >}}

{{< source-reference id="ref_4fe524fd3a9fe7eff43e" >}}

{{< source-reference id="ref_52fe5614038a71f03f05" >}}

{{< source-reference id="ref_fd1c9dc9909e127848df" >}}

{{< source-reference id="ref_1c539d773f1bac7e6b58" >}}

{{< source-reference id="ref_6f816a7d44c99d94a3fe" >}}

{{< source-reference id="ref_1530ce19e693affe8a21" >}}

{{< source-reference id="ref_ca9e07e4fd72b14e5bda" >}}

{{< source-reference id="ref_2ff1e60ee9dab76e510c" >}}

{{< source-reference id="ref_aaa45d19dca64ec1077e" >}}

</details>
