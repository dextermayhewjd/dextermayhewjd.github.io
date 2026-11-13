## 1. 本页只先弄清一件事

**运行版本：Python 3.12。主例使用本地项目的 `PYTHON312_CODE`。**

**调用方提供创建按钮的函数，Dialog 保存它，需要按钮时调用它，再使用返回的按钮。**

当前例子使用 `HTMLButton` 和泛型 `Dialog`。创建函数、可调用接口、继承和类型参数各自承担不同职责，可以分别展开复习。

## 2. 主例：Python 3.12 原例 {#create-button-path}

下面保留本地原例的类、方法、类型参数和调用方式，只补充关键行中文注释。[下载完整示例](/projects/python-design-patterns/creational/factory-method/example.py)。

<!-- PRIMARY_EXAMPLE -->

输出：

<!-- PRIMARY_OUTPUT -->

**本例范围：**`Button` 保存 `label`，`HTMLButton` 继承它并重写 `render()`。`render()` 返回 HTML 字符串，不会自行在屏幕上绘制按钮。

## 3. 从卡住的地方进入

先看主例，再按实际疑问展开对应知识块。

| 当前疑问 | 对应知识块 | 读完要能判断 |
| --- | --- | --- |
| 函数名与函数调用有什么不同？ | [A · 函数对象与调用](#function-value) | 传出去的是函数还是按钮 |
| `_factory` 保存后为什么还能调用？ | [B · 函数的交接](#function-handoff) | 哪一步真正创建按钮 |
| Dialog 为什么接收一个创建函数？ | [C · 工厂职责](#factory-role) | 创建规则与使用流程怎样分开 |
| `Factory[T]` 和 `Dialog[T: Button]` 怎么读？ | [D · 可调用接口与类型参数](#callable-annotation) | 参数、返回类型和类型约束是什么 |
| lambda 的零、一、多个参数怎么写？ | [E · lambda](#lambda-expression) | 谁在何时调用这个短函数 |
| HTMLButton 与 `@override` 是什么关系？ | [F · 继承与方法重写](#inheritance-override) | 运行时调用了哪个 render |

### 3.1 知识点：按需展开 {#factory-callable}

块内片段复用上面的完整主例。为了单独观察函数传递，A、B 会把主例的 lambda 展开成具名函数；这些辅助片段不会替换主例。

<details id="function-value">
<summary>A · 函数对象与调用：f 和 f() 分别是什么？</summary>

**一句结论：**函数可以作为值传递；给函数加调用括号，才执行它并取得结果。

下面的具名函数与主例的 `lambda: HTMLButton("Submit")` 表达同一创建规则：

```python
def make_html_button() -> HTMLButton:
    return HTMLButton("Submit")  # 调用时才创建按钮。

saved = make_html_button  # 保存函数，尚未创建按钮。
button = saved()  # 调用函数，得到 HTMLButton 实例。
```

**检查自己：**`saved` 和 `button` 分别保存什么？

</details>

<details id="function-handoff">
<summary>B · 函数的交接：为什么 self._factory() 能调用？</summary>

**前置：**[A · 函数对象与调用](#function-value)。

**一句结论：**构造函数把传入的函数保存到 `_factory`，`render()` 再通过这个属性调用它。

```python
html_dialog = Dialog(make_html_button)  # 传入 A 中的函数，没有调用它。
print(html_dialog._factory is make_html_button)  # True：保存的仍是该函数。
print(html_dialog.render())  # render 内部调用 _factory()，然后调用按钮的 render()。
```

`Dialog(make_html_button())` 会先创建按钮再传入；本例期望的是可调用的创建函数，直接传入按钮实例会在之后的 `_factory()` 处报错。

**检查自己：**创建 Dialog 的时候，是否已经执行了创建按钮的函数？

</details>

<details id="factory-role">
<summary>C · 工厂职责：为什么把创建按钮交给函数？</summary>

**前置：**[B · 函数的交接](#function-handoff)。

**一句结论：**调用方选择创建哪种按钮，Dialog 统一使用创建出来的按钮。

| 位置 | 职责 |
| --- | --- |
| `lambda: HTMLButton("Submit")` | 规定如何创建具体按钮 |
| `Dialog.__init__` | 保存这个创建函数 |
| `Dialog.render` | 调用创建函数，再调用返回按钮的 render |

主例使用函数注入创建行为；经典 GoF 工厂方法使用创建者子类重写创建方法，组织方式见文末的[传统写法](/projects/python-design-patterns/creational/factory-method/#classic-example)。不能只凭存在一个创建函数，就认为已经展示了经典模式的全部结构。

**检查自己：**改用返回 `Button("OK")` 的创建函数时，Dialog 的使用流程是否需要变化？

</details>

<details id="callable-annotation">
<summary>D · Callable、Factory[T] 和 Dialog[T: Button] 怎么读？</summary>

**前置：**[A · 函数对象与调用](#function-value)。

`Callable[[], Button]` 描述“调用时不传参数，返回 Button 实例”的可调用对象。

| 类型注解 | 参数 | 返回值 |
| --- | --- | --- |
| `Callable[[int], Button]` | 一个整数 | Button 实例 |
| `Callable[[str], Button]` | 一个字符串 | Button 实例 |
| `Callable[[int, str], Button]` | 整数、字符串两个参数 | Button 实例 |
| `Callable[[Any], Button]` | 一个参数，不限定具体类型 | Button 实例 |
| `Callable[[], Button]` | 零个参数 | Button 实例 |
| `Callable[..., Button]` | 不描述具体参数列表 | Button 实例 |
| `Callable[[int], Any]` | 一个整数 | 不限定返回值类型 |

`Any` 需要 `from typing import Any`。它不表示零个参数，也不表示任意数量的参数；`...` 也不会改变实际函数能接收哪些参数。

主例用 Python 3.12 的类型参数写成：

```python
type Factory[T] = Callable[[], T]
```

`Factory[HTMLButton]` 就表示无参数、返回 HTMLButton 的创建函数。`T` 是类型参数，不是按钮实例。

`class Dialog[T: Button]` 表示 T 的上界是 Button，因此 T 可以是 Button 或它的子类。`factory: Factory[T]` 将工厂返回类型与这个 Dialog 的 T 关联起来。这些注解用于类型表达与检查，不会自动创建或转换对象。

**检查自己：**`Factory[HTMLButton]` 的参数有几个，返回什么？

</details>

<details id="lambda-expression">
<summary>E · lambda：先看无参数、一个参数、多个参数</summary>

**一句结论：**`lambda` 创建短函数，调用时返回一个表达式的结果。

| 参数形式 | 函数写法 | 调用与结果 |
| --- | --- | --- |
| 无参数 | `f = lambda: 10` | `f()` 返回 10 |
| 一个参数 | `f = lambda x: x * 2` | `f(3)` 返回 6 |
| 多个参数 | `f = lambda x, y: x + y` | `f(2, 3)` 返回 5 |

**无参数：留到以后创建。**

```python
factory = lambda: HTMLButton("Submit")  # 此刻只创建函数。
button = factory()  # 现在才创建按钮。
print(button.render())
```

输出：

```text
<button>Submit</button>
```

**一个参数：提供排序规则。**

```python
items = [("苹果", 5), ("香蕉", 3)]
result = sorted(items, key=lambda item: item[1])  # sorted 逐项调用函数，取得价格。
print(result)
```

输出：

```text
[('香蕉', 3), ('苹果', 5)]
```

**多个参数：计算并返回。**

```python
add = lambda x, y: x + y
print(add(2, 3))  # 把 2、3 交给 x、y，再计算表达式。
```

输出：

```text
5
```

共同规则：冒号前声明参数，冒号后只能是一个表达式，调用时自动返回表达式结果。具名 def 仍然适合多步骤逻辑、重复使用和需要清楚命名的操作。

回到主例，`Dialog(lambda: HTMLButton("Submit"))` 先把函数交给 Dialog，之后由 `render()` 里的 `_factory()` 调用它。

</details>

<details id="inheritance-override">
<summary>F · 继承与 @override：为什么得到 HTML 字符串？</summary>

**一句结论：**HTMLButton 继承 Button 的字段，并提供自己的 render 实现。

`HTMLButton("Submit")` 仍能通过构造参数设置继承的 label。调用这个实例的 `render()` 时，执行的是 HTMLButton 中的版本，因此得到 `<button>Submit</button>`。

`@override` 在 Python 3.12 中用于标记“这个方法应当重写父类方法”，供类型检查器核对。真正决定方法查找的是继承关系，装饰器本身不会创建继承关系。

</details>

## 4. 用一句话总结 {#factory-in-one-sentence}

**工厂把“对象怎么创建”封装在创建入口里，让使用者通过这个入口取得对象，再完成自己的工作。**

对应主例：调用方传入创建 HTMLButton 的函数 → Dialog 保存到 `_factory` → `render()` 调用工厂取得按钮 → 调用按钮自己的 `render()` 得到 HTML 字符串。
