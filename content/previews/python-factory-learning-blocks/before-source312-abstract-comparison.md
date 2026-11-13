### 3.1 和上一节的工厂究竟有什么不同？ {#factory-comparison}

对比[上一节的 Python 示例](/projects/python-design-patterns/creational/factory-method/)：**上节替换“创建按钮”的入口；本节替换“创建一套按钮和复选框”的工厂。**

| 产品种类 | 暗色产品族：DarkThemeFactory | 亮色产品族：LightThemeFactory |
| --- | --- | --- |
| 按钮 Button | 创建暗色按钮 | 创建亮色按钮 |
| 复选框 Checkbox | 创建暗色复选框 | 创建亮色复选框 |

**行是产品种类，列是一套配套方案。** `get_factory("dark")` 选中暗色这一列，再通过同一个工厂的两个创建方法，分别获得 Button 和 Checkbox 实例。换成 `"light"`，使用方的两个方法调用不变。

判断是否需要抽象工厂，看的是**多种相关产品是否需要随同一套方案一起切换**。共有 `theme` 字段只是本例的表达方式；普通工厂也可以按主题创建按钮。

**一句话：抽象工厂把一组配套产品的创建规则组织在一起，让调用方可以整体更换这套创建方案。**
