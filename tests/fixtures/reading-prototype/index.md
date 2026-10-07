---
title: "跨文件阅读器测试夹具"
ShowToc: false
compactDiagramLegends: true
---

**这是交互测试夹具，不是 slime 最新源码或学习材料。**

{{< architecture-explorer id="reading-fixture" reading="learning-pack.json" modules="explorer.json" src="images/files.svg" width="1200" legend="reading" caption="测试文件图；未记录不表示实际运行状态。" >}}

{{< architecture figureId="reading-chain" functionExplorer="reading-fixture" trace="true" src="images/chain.svg" width="1000" legend="reading" caption="测试跨文件调用关系；节点位于所属文件容器，非执行记录。" >}}

## 测试源码

{{< source-reference id="caller" >}}

{{< source-reference id="run-a" >}}

{{< source-reference id="run-b" >}}

{{< source-reference id="external" >}}
