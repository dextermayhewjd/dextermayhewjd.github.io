---
title: "源码用法与教程对照"
description: "每种原生机制对应讲解，每个扫描位置可回到完整源码。"
weight: 850
ShowToc: true
hideMeta: true
hideInOverview: true
---

## 这里的“覆盖”指什么

教程覆盖当前固定版本中扫描到的原生语法、标准库接口及有接收者线索的方法，每节末尾都有全部相关源码位置。标准库知识先用小实验讲清，再到完整源码查看它在业务里的输入、交接和退出。

同名的 `.get()`、`.join()`、`.close()` 不能单凭名字认定为并发接口。没有可靠接收者线索的记录仍放在第 21 节的核对表中，保留原始代码，不混入已确认的 API 数量。

{{< python-async-coverage >}}

## 下载与重新核对

- [逐条源码到讲解的完整映射](/python-async-concurrency/teaching-coverage.json)
- [按知识点整理的 Markdown 对照](/python-async-concurrency/teaching-coverage.md)
- [原始统计与源码索引](../usage-index/)

这份对照不声称覆盖其他 Slime 版本、动态生成的代码或 Python 标准库里本仓库未使用的所有接口。更新源码后需要重新扫描并补齐新增映射，不能沿用旧的“无缺项”结论。

[回到学习顺序](../)
