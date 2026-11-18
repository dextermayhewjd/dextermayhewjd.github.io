import asyncio
import inspect


def get_samples(num_samples):
    return list(range(num_samples))


async def get_samples_async(num_samples):
    return list(range(num_samples))


def get_samples_later(num_samples):
    # 普通函数也能返回协程对象；此时还没有执行协程函数体。
    return get_samples_async(num_samples)


async def exercise():
    for name, fn in [
        ("sync", get_samples),
        ("async", get_samples_async),
        ("later", get_samples_later),
    ]:
        # 先检查函数；True 表示识别为协程函数，这一步不调用它。
        print(name, "function", inspect.iscoroutinefunction(fn))
        result = fn(3)  # 调用一次：得到列表，或者得到尚未执行的协程对象。
        can_await = inspect.isawaitable(result)  # 再检查返回对象；不执行或等待它。
        print(name, "awaitable", can_await)  # True：可以 await；False：本例直接使用列表。
        if can_await:
            result = await result  # 执行并等待本例的协程对象，取得它返回的列表。
        print(name, "samples", result)


if __name__ == "__main__":
    asyncio.run(exercise())  # 运行一次实验，依次检查三个函数及其返回对象。
