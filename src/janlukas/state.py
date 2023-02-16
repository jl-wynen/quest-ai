from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from . import _janlukas as jl


class State(ABC):
    def __init__(self, team: str, index: int) -> None:
        self.team = team
        self.index = index

    @abstractmethod
    def step(self, *, info: dict, world: jl.World) -> tuple[State, tuple]:
        pass

    def reached_target(self, *, info: dict, world: jl.World) -> State:
        return self

    def make(self, cls: type, **kwargs) -> State:
        return cls(team=self.team, index=self.index, **kwargs)

    def next_state(
        self, cls: type, info: dict, world: jl.World, **kwargs
    ) -> Tuple[State, tuple]:
        state = self.make(cls, **kwargs)
        return state.step(info=info, world=world)


class Regicide(State):
    """Go directly to the enemy King and stop there."""

    def step(self, *, info: dict, world: jl.World) -> tuple[State, tuple]:
        return self, world.enemy_king


def get_enemy_king(world: jl.World, info: dict) -> tuple[float, float] | None:
    if (king := world.enemy_king) is not None:
        return king
    for enemy in info["enemies"]:
        if enemy["name"] == "King":
            return enemy["x"], enemy["y"]
    return None
