# Learn Slime 默认入口改为 Agent 小课

用户反馈上一版首章太密集；默认入口改为自下向上的 17 小课、4 组。旧单任务闭环保留为进阶串联，不沿 25 步控件增加功能。

## 当前页面

- 首页：http://localhost:1326/projects/slime/
- 首课：http://localhost:1326/projects/slime/agent/01-sandbox/
- 小课：content/projects/slime/agent/{id}/index.md，由 agent-course shortcode 直接呈现主线程最终审阅的课程 JSON，网站不自行改写正文。

默认页面只有分组目录、问题、短解释、例子和一段实际源码。首课代码进一步缩为真实返回行，完整接口与版本放入细节折叠。勾选文案为“这节已读懂”，初态“未学”；范围与自报说明只在折叠图中出现。

首页已学模块图折叠且不画未来节点。其下按 16 个课程文件查看未学、部分完成和本课程目标完成；同文件按关联小课聚合，不重复计数，不显示 645 原生目录。prerequisites 是学习基础，不冒充调用关系，previous/next 是连续阅读顺序。

## 来源与记录

课程来自当前 THUDM/slime 2f2318653f6f794dddd321eff7c9d4b7b174643f；主线程已核对 17 个摘录与当前 Git blob，课程涉及全部 13 个 Agent 原生文件及 3 个必要外层接口。

agent-course.json 已同步审阅后的 REALIGN、非流式响应语义、首课减法和真实先修关系。使用新 progressKey，不继承旧 25 步记录。只有显式勾选改变本机记录；访问页面和展开答案不计学习。

## 验证

先运行短课入口缺失的预期失败，再实现简洁页面。桌面与手机行为检查已通过默认无大图/目录/旧控件、17 入口、源码正文、勾选点亮、撤销，以及后补的 iframe 实际刷新恢复和 sandbox 单课部分完成断言。

Hugo --buildDrafts 与既有导航检查通过，git diff --check 通过。保留其他会话的 CS285 内容；本轮未提交、推送或发布。

交付前网站 agent-course.json 与源端最终包按字节相同；明确先修关系与上下课顺序分开，05-Claude 的先修是 03-Harness。最终桌面/手机两个行为测试通过（6.152 秒），包括实际 iframe 刷新恢复、同文件部分完成与待学课保留。
