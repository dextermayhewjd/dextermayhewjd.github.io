# 本步两种容器副本：采样参数与结果列表

[返回函数卡](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md)。本页是 Python 机制补充，不新增阅读步骤。

## 书上怎么说

《Fluent Python》第 2 版说明：list(已有列表) 创建新的外层列表，成员仍引用原来的对象；这是浅拷贝。[依据 A]

## 我的判断（本书未覆盖的 Slime 场景）

- sampling_params.copy() 给每个 Task 一份参数字典；更改一个副本的顶层键不会改其他副本，嵌套可变对象仍需另行考虑共享。
- group = list(group) 创建结果容器的外层副本；紧接着按 idx 替换槽位。它没有重新生成样本，也没有深拷贝 Sample。
- 原列表的槽位与 Sample 对象本身是两回事：前面的 session_id 赋值和下游操作仍可修改同一个 Sample。不能把浅拷贝解释成所有数据均隔离。

以上场景解释依据 Slime 18868a79 的 sglang_rollout.py:417–430；它不是书中的业务示例。

## 依据

A · 第 6 章 › Copies Are Shallow by Default / 6.4 默认做浅拷贝

- 英文：corpus/en/ch06.md:237–307；锚点 copies-are-shallow-by-default。
- 中文：corpus/zh/ch06.md:228–298；同一锚点。
- 本地镜像根目录：/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/。
- 版本：本书基于 Python 3.10；本次核对环境 Python 3.12.3。

原文：

> However, using the constructor or `[:]` produces a shallow copy (i.e., the outermost container is duplicated, but the copy is filled with references to the same items held by the original container).

中文对照：

> 然而，构造函数或 `[:]` 做的是浅拷贝（即复制最外层容器，副本中的项是源容器中项的引用）。

两侧小节范围及引句已逐字核对。本轮未新增运行实验；函数卡中此前的隔离验证与这里的书面依据分别保留。
