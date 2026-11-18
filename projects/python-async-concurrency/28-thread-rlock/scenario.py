import threading


cart = []
lock = threading.RLock()  # 约定购物车的访问都遵守这同一把锁。


def add_item(name):
    with lock:  # 单独调用 add_item 时，也要保护购物车更新。
        cart.append(name)


def add_bundle():
    with lock:  # 把加入两个商品视为一次完整更新。
        add_item("keyboard")  # 当前线程进入 add_item，再次取得同一把锁。
        add_item("mouse")  # 上一次内层已退出；外层仍持锁，再完成第二次添加。


if __name__ == "__main__":
    add_bundle()
    print(cart)
