---
title: "Python 设计模式"
description: "统一使用 Python 3.12，从实际问题理解 22 种模式与可运行示例。"
weight: 18
hideMeta: true
---

## 先看问题，再看模式

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

### [创建型 · 5 种](creational/)

怎样创建和配置对象。

| 模式 | 解决的问题 |
| --- | --- |
| [工厂方法 · Factory Method](creational/factory-method/) | 把创建对象的选择放到一个入口里。 |
| [抽象工厂 · Abstract Factory](creational/abstract-factory/) | 一次选择一整套相互匹配的对象。 |
| [建造者 · Builder](creational/builder/) | 把复杂对象的配置和构造组织清楚。 |
| [原型 · Prototype](creational/prototype/) | 基于已有对象，复制并调整少量状态。 |
| [单例 · Singleton](creational/singleton/) | 让调用方复用同一个实例。 |

### [结构型 · 7 种](structural/)

怎样连接接口和组合对象。

| 模式 | 解决的问题 |
| --- | --- |
| [适配器 · Adapter](structural/adapter/) | 把现有接口转换为调用方期待的接口。 |
| [桥接 · Bridge](structural/bridge/) | 让两个变化维度可以独立组合。 |
| [组合 · Composite](structural/composite/) | 用一致的方式处理单个元素和嵌套容器。 |
| [装饰器 · Decorator](structural/decorator/) | 在现有行为外面逐层添加功能。 |
| [外观 · Facade](structural/facade/) | 为一组子系统提供一个方便的调用入口。 |
| [享元 · Flyweight](structural/flyweight/) | 让大量对象共享可复用的状态。 |
| [代理 · Proxy](structural/proxy/) | 在访问真实对象时加入控制。 |

### [行为型 · 10 种](behavioral/)

怎样分配行为和协调协作。

| 模式 | 解决的问题 |
| --- | --- |
| [责任链 · Chain of Responsibility](behavioral/chain-of-responsibility/) | 让请求依次经过多个可选择处理的环节。 |
| [命令 · Command](behavioral/command/) | 把一次操作保存成以后可以执行的值。 |
| [迭代器 · Iterator](behavioral/iterator/) | 逐个产生元素，让调用方不必了解内部结构。 |
| [中介者 · Mediator](behavioral/mediator/) | 把多个参与者之间的协作集中到一个中间角色。 |
| [备忘录 · Memento](behavioral/memento/) | 保存状态快照，以便以后恢复。 |
| [观察者 · Observer](behavioral/observer/) | 一次状态变化，通知多个订阅者。 |
| [状态 · State](behavioral/state/) | 让同一个对象在不同状态下响应不同。 |
| [策略 · Strategy](behavioral/strategy/) | 保持调用流程不变，替换其中的算法。 |
| [模板方法 · Template Method](behavioral/template-method/) | 固定处理步骤，把可变化的步骤留给调用方。 |
| [访问者 · Visitor](behavioral/visitor/) | 针对一组对象类型增加新的操作。 |

## 资料来源

示例来自 [back_to_design_pattern](https://github.com/dextermayhewjd/back_to_design_pattern/tree/42e623b8f6d94ec44884f45131e7f15570009577)，保留原项目的 [MIT 许可](license.txt)。本站增加中文问题索引、观察点和使用边界。
