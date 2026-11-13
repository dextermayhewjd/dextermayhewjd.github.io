"""
Decorator - Python 3.12+ Example: PEP 695 Generic Decorator with ParamSpec
"""
from collections.abc import Callable
import functools


def logged[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling: {func.__name__}")
        # 保持原参数调用被包装函数，并保存它的返回结果。
        res = func(*args, **kwargs)
        print(f"Finished: {func.__name__}")
        return res
    return wrapper


@logged
def greet(name: str) -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    msg = greet("World")
    print(msg)
