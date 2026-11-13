#!/usr/bin/env python3
"""Render a self-contained Hugo reference from the local pattern catalog."""

import argparse
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "content/projects/python-design-patterns"
UPSTREAM = "https://github.com/dextermayhewjd/back_to_design_pattern"
PYTHON_VERSION = "3.12"
CATEGORIES = {
    "creational": ("创建型", "怎样创建和配置对象", 10),
    "structural": ("结构型", "怎样连接接口和组合对象", 20),
    "behavioral": ("行为型", "怎样分配行为和协调协作", 30),
}

# Guidance follows the local catalog's PYTHON312_CODE examples.
GUIDES = {
    "factory-method": (
        "把创建对象的选择放到一个入口里。",
        "Factory[T] 描述无参数、返回 T 的创建函数；Dialog[T: Button] 保存这个函数。主例用 lambda 创建 HTMLButton，再由 Dialog.render 调用按钮的 render。",
        "Dialog._factory 保存的是什么，HTMLButton.render 又为什么返回 HTML 字符串？",
        "只有少数固定类型时，普通函数和清楚的分支已经足够。类工厂适合创建过程需要保存状态或通过继承扩展的场景。",
    ),
    "abstract-factory": (
        "一次选择一整套相互匹配的对象。",
        "Factory[B, C] 声明两种创建方法，StandardFactory 分别创建 Button 和 Checkbox；build_ui 使用同一工厂取得两者，并返回 ComponentPair[B, C]。",
        "build_ui 接收的是产品还是工厂，返回的元组里又是什么？",
        "这个最小例子只提供 StandardFactory，展示产品对的统一创建，没有实际演示两套产品族之间的切换。完整产品族对照见传统写法。",
    ),
    "builder": (
        "把复杂对象的配置和构造组织清楚。",
        "QueryBuilder 保存 Query，用 from_table、select、where、take 逐步填写查询描述。Self 表示设置方法返回当前建造者类型，build 最后返回 Query。",
        "每一步修改 Query 的哪个字段，build 返回建造者还是查询描述？",
        "本例只收集查询描述，不执行 SQL，也不生成安全的参数化 SQL。Builder 与 yield 生成器是不同概念。",
    ),
    "prototype": (
        "基于已有对象，复制并调整少量状态。",
        "DocumentTemplate 保存文档模板，clone_with 用 dataclasses.replace 创建新实例并覆盖指定字段；Properties 是属性字典的类型别名，Self 描述同类返回值。",
        "custom_doc 的标题变了以后，base_doc 是否改变，properties 字典是否复制？",
        "复制的深浅必须按字段判断；独立修改嵌套列表或字典前，需要决定是否深拷贝。",
    ),
    "singleton": (
        "让调用方复用同一个实例。",
        "ServiceRegistry 在类属性 _instance 中保存实例，get_instance 第一次创建、后续返回保存的对象；Self 描述返回当前类的实例。",
        "为什么 registry1 is registry2 为真，实例引用保存在什么位置？",
        "本例通过 get_instance 复用实例；直接调用 ServiceRegistry() 仍会新建对象。类属性不跨进程共享，首次并发初始化也没有加锁。",
    ),
    "adapter": (
        "把现有接口转换为调用方期待的接口。",
        "XMLToDictAdapter 保存 XMLService 和一个转换函数，将 get_xml_payload 的字符串结果转换成调用方需要的字典。Converter[In, Out] 用 type 声明转换函数的输入输出类型。",
        "调用方要的接口是什么，适配器把原服务的返回值转换成了什么？",
        "先明确两边的接口差异。本例 parser 只是字符串替换演示，并不是完整的 XML 解析器；真正接入时要换成符合数据协议的解析函数。",
    ),
    "bridge": (
        "让两个变化维度可以独立组合。",
        "Shape[R] 保存满足 RenderBackend 协议的渲染器，Circle 重写 draw。形状与 VectorRenderer、RasterRenderer 两个渲染实现通过组合连接，R 描述渲染器类型。",
        "Circle 的渲染器换成 RasterRenderer 后，draw 把绘制动作交给谁？",
        "两个维度确实需要独立扩展时才值得拆开；只有一种稳定实现时，不必预先建立两套结构。",
    ),
    "composite": (
        "用一致的方式处理单个元素和嵌套容器。",
        "Leaf[T] 保存叶子值，Group[T] 保存子节点；type Tree[T] = Leaf[T] | Group[T] 描述两种节点的联合类型。render 递归组合子节点的结果。",
        "Group 中再放入 Group 时，render 如何继续取得其中 Leaf 的结果？",
        "这是树形结构的简化例子；如果允许循环引用，遍历需要另行处理循环。",
    ),
    "decorator": (
        "在现有行为外面逐层添加功能。",
        "logged 接收函数并返回 wrapper，functools.wraps 保留原函数的元信息。def logged[**P, R] 用 Python 3.12 的类型参数保留参数列表 P 和返回类型 R。",
        "包装函数在调用原函数之前和之后分别做了什么？",
        "GoF 装饰模式是一种组合思路，Python 的 @ 是应用装饰器的语法，两者相关但不完全等同；叠加顺序会影响行为。",
    ),
    "facade": (
        "为一组子系统提供一个方便的调用入口。",
        "PipelineFacade[In, Out] 把两个处理步骤收进一个 execute 入口：先将输入交给 step1，再将中间字符串交给 step2。Stage[T, U] 描述每个步骤的输入输出。",
        "execute 的原始输入、中间字符串和最终输出分别交给哪一步？",
        "外观可以简化入口，但不应把所有不相干的业务都集中进同一个大类。",
    ),
    "flyweight": (
        "让大量对象共享可复用的状态。",
        "FlyweightPool[K, V] 按键 K 缓存共享对象 V；首次遇到键时调用工厂创建 FontStyle，后续相同键直接复用。frozen、slots 的 dataclass 保存共享样式。",
        "两次使用相同字体名和字号获取的 FontStyle 是否是同一个对象？",
        "共享状态需要保持稳定；缓存键决定哪些实例可复用，缓存容量和生命周期也会影响内存占用。",
    ),
    "proxy": (
        "在访问真实对象时加入控制。",
        "LazyProxy[T] 保存一个返回 T 的工厂，第一次读取 target 时创建 HeavyResource，后续读取复用同一个目标；get_data 再调用目标的 fetch_data。",
        "创建 LazyProxy 与第一次 get_data 时，哪一步真正创建 HeavyResource？",
        "这是受控接口的懒加载示例，并非完整透明代理。工厂的返回类型 T 不自动保证存在 fetch_data 方法，接入其他对象时仍需核对接口。",
    ),
    "chain-of-responsibility": (
        "让请求依次经过多个可选择处理的环节。",
        "Pipeline[Req, Res] 依次调用 Step[Req, Res] 列表，None 表示继续传递，首个非 None 结果结束处理；全部未处理时返回 fallback。",
        "哪个返回值表示继续传递，哪个返回值会终止处理？",
        "先约定清楚继续、拒绝和完成分别如何表示；处理顺序通常也是业务规则的一部分。",
    ),
    "command": (
        "把一次操作保存成以后可以执行的值。",
        "Action[T] 保存数据 payload、正向函数 forward 和逆向函数 backward。TextBuffer 创建动作后，由调用方通过 apply 执行、revert 撤销。",
        "make_append_action、apply、revert 分别何时创建操作、修改内容和撤销修改？",
        "Callable 不会自动提供撤销。撤销需要保存足够的旧状态，外部副作用也未必能完全恢复。",
    ),
    "iterator": (
        "逐个产生元素，让调用方不必了解内部结构。",
        "batch_stream[T] 用 yield 分批交出列表；PipelineSource[T].__iter__ 用 yield from 交出内部元素。T 表示元素类型，不改变生成器的执行时机。",
        "batch_stream 何时开始产生批次，PipelineSource 的一次遍历何时创建生成器？",
        "每个生成器对象通常只能消费一遍；PipelineSource 每次调用 __iter__ 都创建新的生成器，因此这个源对象可以重复遍历。",
    ),
    "mediator": (
        "把多个参与者之间的协作集中到一个中间角色。",
        "Mediator[Msg] 保存处理函数，broadcast 将同一个 UIAction 依次交给这些函数。参与者通过中心通信，Msg 描述消息类型。",
        "UIAction 先交给谁，再由谁调用登记的处理函数？",
        "这里展示集中广播的最小结构，与观察者的示例接近。中介者是否承担协作调度，要看业务规则如何组织，不能仅凭类名判断。",
    ),
    "memento": (
        "保存状态快照，以便以后恢复。",
        "History[S] 保存状态快照并在 rollback 时取出最近一份；GameState 用 frozen dataclass 保存游戏状态，当前状态变化通过新建 GameState 表达。",
        "current 换成新 GameState 后，历史中保存的对象还是哪一份？",
        "frozen 只阻止字段重新赋值，不会递归冻结字段内部的列表或字典；快照还需要考虑复制深度和内存。",
    ),
    "observer": (
        "一次状态变化，通知多个订阅者。",
        "EventSource[T] 登记 Listener[T] 回调；emit 接收一个事件并同步调用各个监听函数。type Listener[T] = Callable[[T], None] 描述回调签名。",
        "emit 发送字典事件时，登记的监听函数接收到什么？",
        "这里的通知是同步调用，没有提供取消订阅接口；一个回调抛出异常会中断本次通知。观察者模式本身不意味着异步或多线程。",
    ),
    "state": (
        "让同一个对象在不同状态下响应不同。",
        "StateMachine[S, E] 按 (当前状态, 事件) 在 TransitionTable[S, E] 中查下一状态；trigger 修改状态并返回 self，Self 描述可继续调用的状态机对象。",
        "投币 coin 和推动 push 各在哪个状态下有效，触发后状态变成什么？",
        "表中没有对应项时会抛出 ValueError；类型参数不自动补全状态转换规则。复杂状态可以另行封装行为。",
    ),
    "strategy": (
        "保持调用流程不变，替换其中的算法。",
        "type Strategy[T, R] = Callable[[T], R] 描述策略函数；AlgorithmRunner[T, R] 保存策略，run 将输入交给它并返回结果。",
        "替换传入 AlgorithmRunner 的策略函数后，run 自身需要怎样改变？",
        "无状态的算法用函数很直接；算法需要配置、状态或多个关联操作时，策略对象仍然合适。",
    ),
    "template-method": (
        "固定处理步骤，把可变化的步骤留给调用方。",
        "BaseWorkflow[T, R].execute 固定先 sanitize 再 process 的步骤；TextWorkflow 通过重写两个方法指定文本处理行为，@override 标记这些重写方法。",
        "execute 固定了什么调用顺序，TextWorkflow 又替换了哪两个步骤？",
        "@override 帮助类型检查器核对是否正确重写，不会在运行时自动校验所有行为。模板方法依赖继承关系，应保持步骤接口稳定。",
    ),
    "visitor": (
        "针对一组对象类型增加新的操作。",
        "type Expression = Num | BinOp 描述表达式节点；evaluate_expression 用 match 区分数字、加法和乘法，再递归计算子表达式。",
        "遇到 Num 与 BinOp 时各执行哪个分支，嵌套加法和乘法怎样交回结果？",
        "这是用联合类型与模式匹配组织访问操作的替代方案，不是经典双重分派。新增节点类型时仍要补充相应处理分支。",
    ),
}

# Insert a short explanation beside the operation the reader is following.
ANNOTATIONS = {
    'factory-method': ('        btn = self._factory()', '调用保存的工厂函数，取得一个具体按钮实例。'),
    'abstract-factory': ('    return factory.create_button(), factory.create_checkbox()', '同一个工厂分别创建两种产品，作为一个元组返回。'),
    'builder': ('        return self._query', '交出内部的查询描述对象；这里不重新创建，也不执行查询。'),
    'prototype': ('        return replace(self, **changes)', '依据已有模板创建新实例，覆盖指定字段；未修改的字段值继续复用。'),
    'singleton': ('            cls._instance = cls()', '首次获取时创建，并把实例引用保存在类属性中。'),
    'adapter': ('        raw = self._service.get_xml_payload()', '从已有服务取出 XML 字符串，再交给转换函数。'),
    'bridge': ('        return self.renderer.draw_primitive("circle")', '圆形将绘制操作交给当前绑定的渲染器。'),
    'composite': ('        inner = ", ".join(c.render() for c in self.children)', '子节点可以是叶子或分组，都通过 render 取得结果。'),
    'decorator': ('        res = func(*args, **kwargs)', '保持原参数调用被包装函数，并保存它的返回结果。'),
    'facade': ('        intermediate = self._step1(payload)', '先取得中间字符串，再交给第二步。'),
    'flyweight': ('            self._pool[key] = self._factory(key)', '只有键首次出现时创建共享对象；之后直接复用。'),
    'proxy': ('            self._target = self._factory()', '第一次读取 target 时创建对象，后续读取复用。'),
    'chain-of-responsibility': ('            if res is not None:', 'None 表示继续传递；首个非 None 结果结束处理。'),
    'command': ('        self.forward(self.payload)', '执行之前保存的动作，将 payload 交给正向函数。'),
    'iterator': ('        yield items[i : i + batch_size]', '每次交出一批元素，然后暂停等待下一次取值。'),
    'mediator': ('            handler(message)', '中心将同一条消息同步交给每个处理函数。'),
    'memento': ('        self._checkpoints.append(state)', '保存这一份状态对象；当前状态随后可以换成新对象。'),
    'observer': ('            listener(event)', '同步通知一个监听函数；返回后再通知下一个。'),
    'state': ('            self.state = self._transitions[key]', '按当前状态和事件查表，将状态改为目标状态。'),
    'strategy': ('        return self.strategy(data)', '将输入交给保存的策略函数，返回它的计算结果。'),
    'template-method': ('        cleaned = self.sanitize(payload)', '外层固定先清洗再处理；具体步骤由子类重写。'),
    'visitor': ('            return evaluate_expression(l) + evaluate_expression(r)', '递归计算左右子表达式，再组合为加法结果。'),
}


def front_matter(title, description, weight, **extra):
    fields = {"title": title, "description": description, "weight": weight,
              "hideMeta": True, **extra}
    return "---\n" + "\n".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()
    ) + "\n---\n\n"


def bullets(items):
    return "\n".join(f"- {item}" for item in items)


def fenced(code):
    return f"```python\n{code.strip()}\n```"


def example_output(code):
    with tempfile.TemporaryDirectory() as directory:
        result = subprocess.run(
            [sys.executable, "-I", "-c", code], cwd=directory,
            check=True, capture_output=True, text=True, timeout=10,
        )
    return re.sub(r"executed in \d+\.\d+s", "executed in <elapsed>s", result.stdout).strip()


def main_example(pattern):
    code = pattern.python312_code
    target, comment = ANNOTATIONS[pattern.id]
    if target not in code.splitlines():
        raise ValueError(f"Example changed: review the annotation for {pattern.id}")
    indentation = target[:len(target) - len(target.lstrip())]
    return "".join(
        (f"{indentation}# {comment}\n" if line.rstrip("\n") == target else "") + line
        for line in code.splitlines(keepends=True)
    )


def render(source):
    if sys.version_info < (3, 12):
        raise SystemExit("Use Python 3.12 or newer to build and verify these examples.")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "src"))
    patterns = importlib.import_module("design_patterns.catalog").ALL_PATTERNS
    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True,
    ).strip()
    if {p.id for p in patterns} != set(GUIDES):
        raise ValueError("Catalog changed: update the editorial guidance before syncing.")

    pages = {Path("license.txt"): (source / "LICENSE").read_text()}
    introduction = front_matter(
        "Python 设计模式", "统一使用 Python 3.12，从实际问题理解 22 种模式与可运行示例。", 18,
    ) + """## 先看问题，再看模式

同一件事可能用普通函数就能做好，也可能需要对象组合。设计模式提供的是处理变化、依赖和协作的方法；实际写 Python 时，函数、生成器、dataclass 和 Protocol 都可以表达其中的一部分。

这里整理本地 `back_to_design_pattern` 的 **22 种模式**，**所有主例统一采用该项目的 Python 3.12 原例**。保留原例的类、方法、类型参数和调用方式，只补充关键行中文注释；讲解与运行输出同步核对。旧版原例和传统类结构仅在文末作为历史对照。

这里说的“Python 3.12 设计模式”，是**使用 Python 3.12 实现的设计模式示例**。模式本身不属于某个 Python 版本，也不是 Python 官方定义的一套新版模式。`type`、类型参数与 `@override` 使用 3.12 的能力，`Self` 等较早已有的语法仍然适用。有些原例是最小结构或 Python 替代表达，具体边界在各页说明。

阅读假设：认识函数、参数、返回值和类的实例即可。遇到陌生语法，可以先跟随示例的观察点，弄清对象和数据怎样变化。

可以从[工厂方法](creational/factory-method/)开始：先看 Python 3.12 原例和输出，再按疑问展开独立知识块，最后用一句话收拢设计职责。

## 从一个具体需求开始

| 现在的问题 | 可以先看 |
| --- | --- |
| 同一流程，要切换计算方法 | [策略：把函数当作参数](behavioral/strategy/) |
| 给已有函数增加日志或计时 | [装饰器：包装原有行为](structural/decorator/) |
| 新旧接口不一致 | [适配器：转换接口](structural/adapter/) |
| 一个变化要通知多个地方 | [观察者：登记和调用回调](behavioral/observer/) |
| 想逐项读取数据 | [迭代器：yield 与生成器](behavioral/iterator/) |
| 创建对象时有多种选择 | [工厂方法：集中创建入口](creational/factory-method/) |

这些是按问题查找的入口，不要求按顺序读完所有模式。

## 三类模式

"""
    for category, (label, question, weight) in CATEGORIES.items():
        group = [p for p in patterns if p.category.value == category]
        introduction += f"### [{label} · {len(group)} 种]({category}/)\n\n{question}。\n\n"
        introduction += "| 模式 | 解决的问题 |\n| --- | --- |\n"
        category_body = front_matter(label, question + "。", weight)
        category_body += f"[返回 Python 设计模式总览](../)\n\n{question}。下面每页都有 Python 主例子和两种写法对照。\n\n"
        category_body += "| 模式 | 解决的问题 |\n| --- | --- |\n"
        for index, pattern in enumerate(group, 1):
            name = {"builder": "建造者", "decorator": "装饰器"}.get(pattern.id, pattern.chinese_name)
            summary, approach, observation, boundary = GUIDES[pattern.id]
            title = f"{name} · {pattern.name}"
            introduction += f"| [{title}]({category}/{pattern.id}/) | {summary} |\n"
            category_body += f"| [{title}]({pattern.id}/) | {summary} |\n"
            code = main_example(pattern)
            output = example_output(code)
            resource_path = Path(category) / pattern.id
            pages[resource_path / "example.py"] = code.strip() + "\n"
            pages[resource_path / "output.txt"] = output + "\n"
            lesson = DESTINATION / category / pattern.id / "lesson.md"
            body = front_matter(title, summary, index * 10, ShowToc=not lesson.exists(), pythonVersion=PYTHON_VERSION)
            body += f"[总览](../../) / [{label}](../)\n\n"
            if lesson.exists():
                # The catalog owns code; the lesson owns explanation and its placement.
                lesson_body = lesson.read_text().strip()
                for marker in ("<!-- PRIMARY_EXAMPLE -->", "<!-- PRIMARY_OUTPUT -->"):
                    if lesson_body.count(marker) != 1:
                        raise ValueError(f"Expected one {marker} in {lesson}")
                lesson_body = lesson_body.replace("<!-- PRIMARY_EXAMPLE -->", fenced(code))
                lesson_body = lesson_body.replace("<!-- PRIMARY_OUTPUT -->", f"```text\n{output}\n```")
                body += lesson_body + "\n\n"
                body += "## 5. 按需对照与来源\n\n"
            else:
                body += "## 1. 要解决什么问题\n\n"
                if pattern.id == "builder":
                    body += "**使用心智模型：数据对象保存结果，Builder 组织逐步构建结果的过程。**\n\n"
                    body += "本例中，`Query` 保存表名、字段、筛选条件和数量限制；`QueryBuilder` 用 `from_table()`、`select()`、`where()`、`take()` 逐步填写它。\n\n"
                    body += "创建 Builder 时先创建 Query → 设置方法修改它，并返回 Builder 自己以便继续调用 → `build()` 交出这个 Query。这里不会执行数据库查询。\n\n"
                    body += "使用 dataclass 并不意味着必须配一个 Builder；也可以直接写 `Query(...)`。Builder 提供的是组织逐步配置过程的一种方式。\n\n"
                elif pattern.id == "prototype":
                    body += "**Prototype 是“基于已有实例创建新实例”的方式；底层仍然可以调用构造方法。**\n\n"
                    body += "**使用心智模型：用已有实例的字段值创建一个完整的新实例；指定的字段用新值，未指定的字段沿用原值。**\n\n"
                    body += "本例调用 `base_doc.clone_with(title=...)`，得到新实例 `custom_doc`。替换发生在新实例中，`base_doc.title` 保持原样；未指定的 `properties` 继续指向原来的字典，并未自动复制成独立字典。\n\n"
                elif pattern.id == "adapter":
                    body += "**使用心智模型：Adapter 是接口转换桥，复用旧服务，对外提供调用方需要的接口和数据格式。**\n\n"
                elif pattern.id == "bridge":
                    body += "**使用心智模型：把“画什么形状”和“采用什么绘制方式”分开；形状持有一个渲染器，两边可以独立扩展，再按共同接口组合。**\n\n"
                    body += "**组合的前提：**每个接入的 renderer 都必须提供兼容的 `draw_primitive(name: str) -> str`，并能处理上层传来的形状名称。方法名、参数、返回值和行为含义都要符合共同约定。\n\n"
                else:
                    body += f"**{summary}**\n\n"
                body += f"{pattern.problem}\n\n"
                body += f"## 2. 在 Python 中怎样表达\n\n{approach}\n\n"
                body += f"**运行前先观察：**{observation}\n\n"
                body += "## 3. Python 3.12 完整示例\n\n复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。\n\n"
                body += "采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。\n\n"
                body += fenced(code) + "\n\n"
                body += "运行输出：\n\n```text\n" + output + "\n```\n\n"
                walkthrough = DESTINATION / category / pattern.id / "walkthrough.md"
                if walkthrough.exists():
                    body += walkthrough.read_text().strip() + "\n\n"
                body += f"## 4. 使用边界\n\n{boundary}\n\n"
                body += "## 5. 按需对照\n\n"
            legacy = pattern.python310_code
            if pattern.id == "singleton":
                legacy = legacy.replace(
                    "Returns a process-wide singleton settings instance (thread-safe by GIL/lru_cache).",
                    "Cache settings for reuse; concurrent first calls may create multiple instances.",
                )
            body += '<details id="original-python-example">\n<summary>历史原例：Python 3.10 写法</summary>\n\n'
            body += "仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。\n\n"
            if pattern.id == "singleton":
                body += "此原例使用函数缓存，主例使用类属性。原例 docstring 中关于并发首次初始化的表述已修正，执行逻辑不变。\n\n"
            body += fenced(legacy) + "\n\n</details>\n\n"
            classic_id = ' id="classic-example"' if lesson.exists() else ""
            body += f"<details{classic_id}>\n<summary>传统面向对象写法</summary>\n\n"
            body += "观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。\n\n"
            body += fenced(pattern.classic_code) + "\n\n</details>\n\n"
            body += "<details>\n<summary>适用情况、收益与代价</summary>\n\n"
            body += "### 适用情况\n\n" + bullets(pattern.applicability) + "\n\n"
            body += "### 收益\n\n" + bullets(pattern.pros) + "\n\n"
            body += "### 代价\n\n" + bullets(pattern.cons) + "\n\n</details>\n\n"
            body += "<details>\n<summary>来源与版本</summary>\n\n"
            source_file = f"src/design_patterns/catalog/{category}/{pattern.id.replace('-', '_')}.py"
            body += f"代码与基础说明来自 [back_to_design_pattern / {pattern.id}]({UPSTREAM}/blob/{commit}/{source_file})，快照 `{commit[:12]}`。\n\n"
            body += "主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。"
            body += "\n\n原项目按 MIT 许可提供，见[许可全文](../../license.txt)。\n\n</details>\n"
            pages[Path(category) / pattern.id / "index.md"] = body
        introduction += "\n"
        pages[Path(category) / "_index.md"] = category_body
    introduction += f"## 资料来源\n\n示例来自 [back_to_design_pattern]({UPSTREAM}/tree/{commit})，保留原项目的 [MIT 许可](license.txt)。本站增加中文问题索引、观察点和使用边界。\n"
    pages[Path("_index.md")] = introduction
    return pages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT.parent / "back_to_design_pattern")
    parser.add_argument("--check", action="store_true", help="Check snapshots without writing")
    args = parser.parse_args()
    pages = render(args.source.resolve())
    stale = []
    for relative, content in pages.items():
        path = DESTINATION / relative
        if args.check:
            if not path.exists() or path.read_text() != content:
                stale.append(str(relative))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    if stale:
        raise SystemExit("Out-of-date pattern pages: " + ", ".join(stale))
    print(f"{'Checked' if args.check else 'Wrote'} {len(pages)} files (22 patterns).")


if __name__ == "__main__":
    main()
