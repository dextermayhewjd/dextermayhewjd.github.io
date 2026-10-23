# 仓库阅读：逐步建立并记录认知模型

这里是适用于任意源码仓库的阅读方法入口。放在本仓库根目录，用 `00-` 前缀方便找到；各项目复用同一套方法，分别保存自己的目标、源码依据与理解过程。

## 这套方法来自什么要求

2026-10-19，用户在讨论 Slime 阅读时提出：

> 我觉得这里不对啊
> 这里的框架全景不应该考虑我已经读过generate？
> 1.首先 读slime主要是为了能够找到这份工作
> 2. 一系列的方法是为了降低心智负担
> 3. 或许我应该保留的是一个比较基本的每一个步骤，我对于每一个小的模块的理解是什么，
> 这其中包括了，我每一个步骤涉及了什么模块：folder/代码/具体的某一个function
> 达到下一步的过程中，创建新的步骤，继承上一步的对于整体的理解
> 这样子在一步步构建的过程中，认知模型就和被记录的代码一样，一点点被建立？

随后明确了适用范围：

> 我希望你在这个github repo的目录里这么构建，因为我觉得这个适用于任意一个repo

由此形成的约定是：**先确定为什么读这个仓库，再建立最小的整体模型；每一步继承上一步的模型，用真实代码增加或修正一个关系，并把这个理解过程保存下来。**

认知内容由学习者表达，助手负责初始定位、提问、核对与整理。个人记忆允许只知道职责而实现留白；助手的完整讲解单独作为参考，不自动填入个人模型。

“读过哪个函数”属于历史记录，影响回顾的深度；它不能代替整体模型的起点。“已有代码很多”也不意味着需要同时理解所有内部实现。

## 从哪里使用

每个 step 开始前，先与用户讨论要读哪个函数、围绕它弄清什么，以及短期 memory 准备保留哪些认识。助手可以提出候选函数及理由，由用户确认本步范围和记录重点后，再展开阅读和创建函数记录；不要求用户预先知道答案。已准备的材料、旧路线和此前读过的函数不能自动成为本轮主题。

- [制度讨论与待办](../backlog/repo-reading/README.md)：集中保存认知架构、步骤与记忆分工的讨论，先区分已确认内容与待定方案，再接续对应记录。
- [阅读范围 skill](../.agents/skills/repo-reading-scope/SKILL.md)：按阅读目标、指挥官函数、核心骨架三段组织 scope；包含五类过滤方法和已确认样例，可用 `$repo-reading-scope` 调用。
- [阅读顺序 skill](../.agents/skills/repo-reading-order/SKILL.md)：已有骨架后，根据当前问题推荐下一处入口，先看核心动作、再回查最小前置；可用 `$repo-reading-order` 调用。
- [短期 memory skill](../.agents/skills/repo-reading-short-term-memory/SKILL.md)：本步单函数记录与引用入口，包含“共同记录已覆盖时直接引用”的规则；可用 `$repo-reading-short-term-memory` 调用。
- [任务链路总结 skill](../.agents/skills/repo-reading-task-flow/SKILL.md)：阅读后整理 `05-task-flow.md`，以 Step 003 为主要 reference，串起关键交接、结果与边界；可用 `$repo-reading-task-flow` 调用。
- [repo-reading-memory 总入口](../.agents/skills/repo-reading-memory/SKILL.md)：整体记忆分工与长期继承；可用 `$repo-reading-memory` 调用。
- [长短期记忆专属文档](memory-format.md)：集中保存要求、当前格式、复述与追问流程、讨论来由和待验证问题；后续在这里持续修改。
- [当前 Step 01](../backlog/repo-reading/step-01-translate-preview/README.md)：统一格式的实际例子；新模板已同步，旧步骤保留历史快照。
- [格式讨论与确认记录](../backlog/repo-reading/2026-10-19-step-folder-format.md)：已确认每步一个文件夹，累计记忆采用整体地图加逐函数记录，并镜像源码目录。
- [Skill 重构推演 01](../backlog/repo-reading/2026-10-19-skill-refactor-round-01.md)：用消息与工具定义的实际转换样例，检验一个学习步骤的边界。
- [工作流](workflow.md)：开始、续读、展开一个步骤和保存记录时怎样做。
- [代码阅读指南](code-reading-guide.md)：方法一是剪枝三步法，方法二是记录数据变化、临时路径、设计疑问与局部观察；保留用户原文及当前源码对应说明。
- [项目入口模板](templates/repository.md)：新仓库的目标、范围、源码版本和记录入口。
- [单步文件夹模板](templates/step/README.md)：本步范围、短期记忆、前序长期记忆和理解过程。
- [逐函数记录模板](templates/function.md)：分别指向短期、长期 reference 模板；按认可样例依次保留原话、简短场景、输入输出、LLM 模型、未知和来源，省去重复归纳。
- [Slime 的应用记录](repositories/slime/README.md)：本方法的第一个应用；不把 Slime 的岗位目标套给其他仓库。

```text
00-repo-reading/
├── README.md
├── workflow.md
├── memory-format.md
├── templates/
│   ├── repository.md
│   ├── function.md
│   └── step/
│       ├── README.md
│       ├── 01-scope.md
│       ├── 02-short-term-memory/
│       │   ├── overview.md
│       │   └── functions/          # 镜像源码的目录和脚本名
│       ├── 03-long-term-memory/
│       │   ├── overview.md
│       │   └── functions/
│       └── 04-flow.md
└── repositories/
    └── <repo>/
        ├── README.md
        └── steps/
            ├── step-000-initial-model/
            └── step-001-<本步问题>/
```

项目的步骤在真正展开对应问题时创建，不预生成一长串空章节。现有课程和章节目录继续作为资料索引；步骤编号只表达理解记录的先后，不表示函数执行顺序或项目开发历史。

2026-10-19 用户确认：“一个整体地图，每一个函数都单独记录”，且与项目本身 folder 结构一致。记忆目录按 `functions/<源码相对路径>/<完整函数名>.md` 组织；保留源码目录及脚本名，脚本在笔记侧成为同名文件夹。只创建实际接触到的记录。

2026-10-20 用户进一步明确：整体地图与任务主线保存在步骤层；`02` 保存本步单函数记录，`03` 保存由此前步骤累计的同格式函数记录，overview 只做索引。Step 0 的函数放在 `02`，`03` 初始为空；到下一步再继承。不能用整体关系图替代函数卡片。

下一步把上一份 `03` 和 `02` 合并成新的 `03-long-term-memory/`，本步的新理解保存在 `02-short-term-memory/`。旧步骤保留当时快照，完整模型保留在新步骤中；来源、未知与函数说明一并继承。

要在另一个学习仓库使用，可复制本入口、工作流和 `templates/`，建立自己的 `repositories/<repo>/`，并在该仓库的 `AGENTS.md` 中链接工作流。跨仓库的规则需要显式接入，不会自动生效。
