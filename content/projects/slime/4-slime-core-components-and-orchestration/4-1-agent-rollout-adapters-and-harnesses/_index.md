---
title: "4.1. Agent Rollout Adapters and Harnesses"
summary: "架构图、阅读材料与下级章节。"
weight: 10
ShowToc: false
ShowReadingTime: false
ShowPostNavLinks: false
hideMeta: true
---

先看[项目开头的任务生命周期总览](/projects/slime/#agent-lifecycle)，再从各动作页的定位图进入具体数据流。

下面保留 CodeWiki 原图作为组件导航。原图的启动调用实际由外层 `generate()` 发起；本例的直接 HTTP 客户端是沙箱中的 CLI，没有独立 External Platforms 实现。原图动作 1 的接收入口与动作 7 一起说明，动作 8 的响应返回在 3.5 展开。

{{< figure src="diagram.svg" alt="CodeWiki 组件关系概览，用于选择阅读主题" class="slime-diagram" >}}

## 阅读材料

- [本节 README](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/README.md>)
- [Slime Core 完整请求流程](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/Slime%20Core%20%E5%AE%8C%E6%95%B4%E8%AF%B7%E6%B1%82%E6%B5%81%E7%A8%8B.md>)

[CodeWiki 原始章节](<https://codewiki.google/github.com/thudm/slime#slime-core-components-and-orchestration-agent-rollout-adapters-and-harnesses>) · [本节资料文件夹](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/tree/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses>)
