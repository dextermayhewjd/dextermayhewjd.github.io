"""
Memento - Python 3.12+ Example: PEP 695 Generic Snapshot History
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GameState:
    level: int
    score: int
    health: int


class History[S]:
    def __init__(self) -> None:
        self._checkpoints: list[S] = []

    def save(self, state: S) -> None:
        # 保存这一份状态对象；当前状态随后可以换成新对象。
        self._checkpoints.append(state)

    def rollback(self) -> S | None:
        return self._checkpoints.pop() if self._checkpoints else None


if __name__ == "__main__":
    history: History[GameState] = History()
    current = GameState(level=1, score=100, health=100)
    history.save(current)

    current = GameState(level=2, score=250, health=50)
    print(f"Level 2: {current}")

    prev = history.rollback()
    print(f"Rolled back to: {prev}")
