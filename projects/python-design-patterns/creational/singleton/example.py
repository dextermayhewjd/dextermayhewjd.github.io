"""
Singleton - Python 3.12+ Example: Generic Singleton Container & typing.Self
"""
from typing import Self


class ServiceRegistry:
    _instance: Self | None = None

    @classmethod
    def get_instance(cls) -> Self:
        if cls._instance is None:
            # 首次获取时创建，并把实例引用保存在类属性中。
            cls._instance = cls()
        return cls._instance

    def ping(self) -> str:
        return "pong"


if __name__ == "__main__":
    registry1 = ServiceRegistry.get_instance()
    registry2 = ServiceRegistry.get_instance()
    print(f"Registry shared: {registry1 is registry2}, response: {registry1.ping()}")
