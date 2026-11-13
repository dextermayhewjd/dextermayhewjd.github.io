"""Builder - Python 3.12, preserving the ServerConfig teaching scenario."""

from dataclasses import dataclass, field
from typing import Self


@dataclass(kw_only=True)
class ServerConfig:
    host: str = "localhost"
    port: int = 8080
    ssl_enabled: bool = False
    workers: int = 4
    middlewares: list[str] = field(default_factory=list)
    timeout: float | None = 30.0


class ServerConfigBuilder:
    def __init__(self) -> None:
        self._config = ServerConfig()

    def with_host(self, host: str) -> Self:
        self._config.host = host
        return self  # Self 表示返回当前建造者类型，继续链式调用。

    def with_port(self, port: int) -> Self:
        self._config.port = port
        return self

    def enable_ssl(self) -> Self:
        self._config.ssl_enabled = True
        return self

    def add_middleware(self, name: str) -> Self:
        self._config.middlewares.append(name)
        return self

    def build(self) -> ServerConfig:
        return self._config  # 交出已有配置，不复制或重置。


if __name__ == "__main__":
    cfg1 = ServerConfig(host="0.0.0.0", port=443, ssl_enabled=True)
    print(f"Direct kw_only config: {cfg1}")
    cfg2 = (
        ServerConfigBuilder()
        .with_host("api.internal")
        .with_port(9000)
        .add_middleware("auth")
        .add_middleware("rate_limiter")
        .build()
    )
    print(f"Fluent built config: {cfg2}")
