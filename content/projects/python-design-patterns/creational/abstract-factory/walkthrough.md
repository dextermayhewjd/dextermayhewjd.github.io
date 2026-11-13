### 3.1 和上一节的工厂究竟有什么不同？ {#factory-comparison}

对比[上一节的 Python 示例](/projects/python-design-patterns/creational/factory-method/)：**上节给 Dialog 一个创建按钮的函数；本节给 build_ui 一个能创建两种产品的工厂对象。**

| 本节的对象或函数 | 创建或返回什么 |
| --- | --- |
| `StandardFactory.create_button()` | `Button(label="Standard")` |
| `StandardFactory.create_checkbox()` | `Checkbox(checked=True)` |
| `build_ui(StandardFactory())` | 通过同一工厂取得 `(Button, Checkbox)` 两个实例 |

`Factory[B, C]` 说明工厂提供两种创建方法，B、C 是返回产品的类型参数；`ComponentPair[B, C]` 表示两个产品组成的元组。

判断是否需要抽象工厂，看的是**多种相关产品是否需要采用同一套创建方案**，并不要求它们有共同字段。这个原例只有 StandardFactory，展示了统一创建产品对的接口结构；它没有实际演示两种产品族的切换，完整对照见文末传统写法。

**一句话：抽象工厂把一组配套产品的创建规则组织在一起，让调用方可以整体更换这套创建方案。**

### 3.2 看不懂类型写法时，先分开三个角色 {#abstract-factory-types}

**Factory 约定接口，StandardFactory 实现创建，build_ui 接收工厂实例并使用它。** 原来的 GUIFactory 也是 Protocol；新版增加的是类型参数，不是取消了具体工厂。

<details id="abstract-factory-roles">
<summary>A · Factory、StandardFactory 和小写 factory 分别是什么？</summary>

| 名称 | 本例中的角色 |
| --- | --- |
| `Factory[B, C]` | Protocol：约定需要提供两个创建方法，以及它们的返回类型 |
| `StandardFactory` | 具体类：方法内部执行 `Button(...)` 和 `Checkbox(...)` |
| `factory` | `build_ui` 的参数名：本次接收的是 `StandardFactory()` 实例 |

Protocol 中的方法体是 `...`，没有写具体创建步骤。真正的步骤在 StandardFactory 的方法里。

#### 先只理解 Protocol，暂时固定返回类型

下面只是拆解概念的对照片段，不替换上面的 Python 3.12 原例：

```python
class Factory(Protocol):
    def create_button(self) -> Button: ...
    def create_checkbox(self) -> Checkbox: ...
```

它是一份接口清单：能作为 Factory 使用的对象，需要提供这两个方法，分别返回 Button 和 Checkbox 实例。这里写的是返回实例的类型，不是要求方法返回类本身。

StandardFactory 没有显式继承 Factory，但它提供了相符的方法结构，因此可以满足这个 Protocol 的类型约定。这里不是运行时自动继承或自动生成方法。

**协议负责描述要求，具体工厂负责实现要求。** Protocol 并非工厂专属，也不强制每个工厂类都加一段这样的前缀。它可供类型检查器核对接口；这些注解不会自动完成创建或运行时校验。

原例中的 B、C 是再加上的泛型类型参数，用来保留具体产品类型。Protocol 可以不用泛型，泛型也可以用于普通类和函数；理解接口清单后再读 B 块即可。

</details>

<details id="abstract-product-types">
<summary>B · 为什么 B: Button、C: Checkbox 写在参数前面的方括号中？</summary>

**普通函数参数没有被搬到前面：它们仍在圆括号里。** 前面的方括号另行声明类型参数，是 Python 3.12 的泛型语法；只有需要这种泛型表达时才写，不是所有函数或工厂都必须写。

以原函数头为例：

```python
def build_ui[B: Button, C: Checkbox](factory: Factory[B, C]) -> ComponentPair[B, C]:
    ...  # 此处只展示声明结构；完整函数体见主例。
```

| 位置 | 声明什么 | 本例中的意思 |
| --- | --- | --- |
| `[B: Button, C: Checkbox]` | 两个类型参数 B、C | B 表示某种按钮类型，C 表示某种复选框类型 |
| `(factory: Factory[B, C])` | 一个普通函数参数 factory | 实际调用时传入工厂对象 |
| `-> ComponentPair[B, C]` | 返回值的类型关系 | 结果里的按钮、复选框对应前面同一组 B、C |

`B: Button` 给 B 设置类型上界：它可以是 Button，也可以是 Button 的子类。C 同理。这里没有声明名叫 B、C 的普通对象参数，也不会在运行时自动创建两个对象。

因此调用仍然是 `build_ui(StandardFactory())`，只传入一个工厂实例。类型检查器根据 StandardFactory 两个方法的返回类型，把本次调用理解为返回 Button 和 Checkbox 的组合；调用方不需要再把 B、C 作为普通参数传进去。

#### Protocol 类的方括号也是声明类型参数

```python
class Factory[B: Button, C: Checkbox](Protocol):
    def create_button(self) -> B: ...
    def create_checkbox(self) -> C: ...
```

类名后的 `[B: Button, C: Checkbox]` 同样声明两个类型参数；这里圆括号里的 `(Protocol)` 是基类，不是构造函数参数。

可以把这个接口读成：“一个能创建 B 类型按钮和 C 类型复选框的工厂。”`Factory[Button, Checkbox]` 则把两个类型位置指定为 Button、Checkbox。它是类型表达，不会创建工厂实例。

Factory 类和 build_ui 函数各自声明自己的 B、C，它们不是同一组全局变量。函数参数注解 `Factory[B, C]` 把函数里的类型参数与工厂接口的两个类型位置关联起来。

#### 方括号要区分“定义时起名字”和“使用时填类型”

| 写法 | 方括号在做什么 |
| --- | --- |
| `class Factory[B: Button, C: Checkbox](Protocol)` | 定义接口时，给两个类型位置起名 B、C，并约束其上界 |
| `Factory[Button, Checkbox]` | 使用接口时，向这两个位置填入具体类型 Button、Checkbox |
| `def build_ui[B: Button, C: Checkbox](...)` | 定义函数自己的两个类型参数 |
| 函数签名中的 `Factory[B, C]` | 使用接口时，填入当前函数的两个类型参数，把关系连起来 |

这些方括号里的内容都不是要求工厂实例拥有名为 B、C 的字段。

`Button(label="Standard")` 中的 `"Standard"` 是字段值，`Checkbox(checked=True)` 中的 `True` 也是字段值；它们不是名为 StandardButton 或 CheckedCheckbox 的新类型。

</details>

<details id="abstract-build-ui-signature">
<summary>C · 为什么输入工厂与输出元组都写 B、C？</summary>

把原签名分成三部分，它们在使用同一组函数类型参数：

| 部分 | 意思 |
| --- | --- |
| `build_ui[B: Button, C: Checkbox]` | 先起两个类型名字：B 是某种按钮类型，C 是某种复选框类型 |
| `factory: Factory[B, C]` | 输入要求：工厂的 create_button 返回 B 类型实例，create_checkbox 返回 C 类型实例 |
| `-> ComponentPair[B, C]` | 输出约定：元组第一项是同一个 B 类型，第二项是同一个 C 类型 |

**反复写 B、C，是为了保留“输入工厂能创建什么类型，输出就是什么类型”的对应关系。** 它没有要求 factory 拥有 B、C 两个属性，也没有声明额外的运行时参数。

`type ComponentPair[B, C] = tuple[B, C]` 只是给二元组类型起了别名。因此返回类型 `ComponentPair[B, C]` 可以读作 `tuple[B, C]`，它本身不会创建产品。

真正执行的是函数体这一行：

```python
return factory.create_button(), factory.create_checkbox()  # 调用两次创建方法，再组成元组。
```

本次 `build_ui(StandardFactory())` 得到 `(Button(label="Standard"), Checkbox(checked=True))`；外层的 `b, c = ...` 将两个实例分别交给 b 和 c。

对这次调用，依据 StandardFactory 的方法签名，类型检查器可以将函数的 B 理解为 Button、C 理解为 Checkbox：输入是这种工厂，输出是 `tuple[Button, Checkbox]`。实际运行仍然只传入一个 StandardFactory 实例，然后执行上面两次方法调用。

</details>
