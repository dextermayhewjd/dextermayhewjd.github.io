"""
State - Python 3.12+ Example: PEP 695 Generic Finite State Machine
"""
from typing import Self

type TransitionTable[S, E] = dict[tuple[S, E], S]


class StateMachine[S, E]:
    def __init__(self, initial_state: S, transitions: TransitionTable[S, E]) -> None:
        self.state = initial_state
        self._transitions = transitions

    def trigger(self, event: E) -> Self:
        key = (self.state, event)
        if key in self._transitions:
            # 按当前状态和事件查表，将状态改为目标状态。
            self.state = self._transitions[key]
        else:
            raise ValueError(f"Invalid transition from {self.state} with event {event}")
        return self


if __name__ == "__main__":
    table: TransitionTable[str, str] = {
        ("locked", "coin"): "unlocked",
        ("unlocked", "push"): "locked",
    }
    turnstile = StateMachine("locked", table)
    turnstile.trigger("coin")
    print(f"State after coin: {turnstile.state}")
    turnstile.trigger("push")
    print(f"State after push: {turnstile.state}")
