### 3.1 为什么 `factory()` 可以直接调用？ {#factory-callable}

这里先沿用你已经指出的 `match` 分支，补上一个关系：**函数也可以作为值保存到变量或对象属性中，以后再调用。** `factory` 只是这个属性的名字，没有特殊语法。

主例子里的三个分支都执行 `Button(...)`：创建的是**同一个 `Button` 类的不同实例**，只是字段不同，并没有分别定义 WindowsButton、WebButton 和 MobileButton。

#### 先把 lambda 展开成普通 def

下面是对主例子这一行的等价展开片段，复用上方完整示例中的 `Button`、`create_button` 和 `Dialog`：

```python
# 原写法：把一个无参数函数传给 Dialog，此刻还不创建按钮。
win_dialog = Dialog(lambda: create_button("windows"))
```

可以改写为：

```python
def make_windows_button() -> Button:
    # 调用这个函数时，才把固定的 "windows" 交给 create_button。
    return create_button("windows")


win_dialog = Dialog(make_windows_button)  # 传入函数本身，这里没有调用它。
```

`lambda: create_button("windows")` 创建了一个不接收参数的函数。它的函数体等到这个函数被调用时才执行；固定的 `"windows"` 已经写在函数体中。

#### `Callable[[], Button]` 描述了什么？

`Callable` 的常见形式是 `Callable[[参数类型, ...], 返回类型]`。

| 注解的一部分 | 本例的意思 |
| --- | --- |
| `Callable` | 这是一个可以被调用的值，本例中就是函数 |
| `[]` | 调用时不需要传入参数 |
| `Button` | 调用后返回一个 `Button` 实例 |
| `\| None = None` | 也允许不传工厂；默认值为 `None`，构造函数随后选择默认的 Web 工厂 |

`[]` 描述的是参数列表，不表示这个函数返回列表。这个类型注解也不会自动制造一个函数；真正的函数对象来自传入的 `lambda` 或 `def`。

注意下面两个函数的签名不同：

| 函数 | 怎样调用 | 对应类型 |
| --- | --- | --- |
| `create_button` | `create_button("windows")` | `Callable[[str], Button]` |
| `make_windows_button` | `make_windows_button()` | `Callable[[], Button]` |

因此，本例不能直接把需要参数的 `create_button` 当成无参数工厂使用。`lambda` 或上面展开的 `def` 把具体类别提前固定，留下一个无参数入口。

#### 从传入函数跟到 `render_window`

构造函数保存函数对象：

```python
self.factory = factory  # 在传入普通函数的这条路径中，保存的就是那个函数。
```

之后，方法里的两行分两步执行：

```python
button = self.factory()  # 调用保存的函数，拿到它返回的 Button 实例。
return f"Dialog rendering: {button.render()}"  # 调用该实例的方法，拼出窗口描述字符串。
```

本次调用沿着下面这条路径推进：

1. `Dialog(make_windows_button)` 保存函数；此时还没有执行 `make_windows_button`。
2. `win_dialog.render_window()` 开始执行窗口的处理流程。
3. `self.factory()` 调用保存的 `make_windows_button`。
4. 函数内部执行 `create_button("windows")`，得到 `Button(label="OK", action="windows_click")`。
5. `button.render()` 得到字符串 `[OK -> windows_click]`。
6. `render_window()` 最后返回 `Dialog rendering: [OK -> windows_click]`。

这里的 `render()` 只是读取字段并返回字符串；不会绘制真实窗口，也不会执行 `action` 中写着的动作。

#### 为什么保存函数，而不是立刻保存一个按钮？

直接保存一个已经创建的按钮当然也能满足一些需求。本例选择保存创建函数，是让 `Dialog` **在需要按钮时再调用创建入口**，而调用方决定这个入口怎样创建按钮。这样 `render_window` 只需要知道“调用工厂会得到一个有 `render` 方法的按钮”。

| 表达式 | 得到或传递的是什么 |
| --- | --- |
| `make_windows_button` | 函数对象，可以留到以后调用 |
| `make_windows_button()` | 立即调用后得到的 `Button` 实例 |
| `Dialog(make_windows_button)` | 符合本例接口，把函数交给 Dialog 保存 |
| `Dialog(make_windows_button())` | 把按钮实例传给期望函数的位置；之后执行 `self.factory()` 时会因该实例不可调用而报错 |

另一个可观察的结果是：本例每次调用 `render_window()` 都会再次调用工厂；由于这个工厂每次执行 `Button(...)`，就会重新创建按钮。**是否复用对象取决于工厂实现，Callable 本身不负责缓存。**

可以先检查一个区别：`Dialog(make_windows_button)` 执行完以后，创建按钮的工作已经发生了吗？判断依据是调用括号究竟加在 `Dialog` 后，还是 `make_windows_button` 后。
