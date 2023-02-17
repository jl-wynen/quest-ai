from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np

from . import _janlukas as jl


def unstuck(func):
    previous_pos = np.array([-1, -1])

    def step(self, *, info: dict, world: jl.World) -> tuple[State, tuple]:
        pos = info["me"]["position"]
        if not np.array_equal(pos, previous_pos):
            previous_pos[...] = pos
            return func(self, info=info, world=world)
        return self, {"red": (1790, 480), "blue": (10, 480)}[self.team]

    return step


def get_enemy_king(world: jl.World, info: dict) -> tuple[float, float] | None:
    if (king := world.enemy_king) is not None:
        return king
    for enemy in info["enemies"]:
        if enemy["name"] == "King":
            return enemy["x"], enemy["y"]
    return None


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

    def cannot_go_there(self) -> tuple[State, tuple]:
        return self, (896, 480)


class Regicide(State):
    """Go directly to the enemy King and stop there."""

    def step(self, *, info: dict, world: jl.World) -> tuple[State, tuple]:
        return self, world.enemy_king


class AngleGemGetter:
    def __init__(self, tolerance) -> None:
        self.getting_gem: tuple | None = None
        self.tolerance = tolerance
        self.forbidden: tuple | None = None

    def get_gem(
        self, info: dict, current_target: np.ndarray, world: jl.World
    ) -> tuple | None:
        if self.getting_gem is not None:
            return self.getting_gem

        gems = info["gems"]
        if not gems:
            return None

        pos = info["me"]["position"]
        gems = np.c_[gems["x"], gems["y"]]

        v = current_target - pos
        gv = gems - pos
        angles = np.arccos(
            np.dot(gv, v) / np.linalg.norm(v) / np.linalg.norm(gv, axis=1)
        )
        gem_index = np.argmin(angles)
        # Limiting the distance to make sure that the world has been updated
        # around the gem so that we don't try to walk into a wall.
        if abs(angles[gem_index]) < self.tolerance:
            closest_gem = gems[gem_index]
            if self.forbidden is not None and np.array_equal(
                closest_gem, self.forbidden
            ):
                return None
            closest_gem = tuple(closest_gem)
            if not world.is_accessible(closest_gem):
                return None
            self.getting_gem = closest_gem
            return closest_gem

        return None

    def reached_target(self) -> None:
        self.getting_gem = None

    def cannot_go_there(self):
        self.forbidden = self.getting_gem
        self.getting_gem = None


class DistanceGemGetter:
    def __init__(self) -> None:
        self.getting_gem: tuple | None = None
        self.forbidden: tuple | None = None

    def get_gem(
        self, info: dict, current_target: np.ndarray, world: jl.World
    ) -> tuple | None:
        if self.getting_gem is not None:
            return self.getting_gem

        gems = info["gems"]
        if not gems:
            return None

        pos = info["me"]["position"]
        gems = np.c_[gems["x"], gems["y"]]

        distances = np.linalg.norm(gems - pos, axis=1)
        gem_index = np.argmin(distances)
        closest_gem = gems[gem_index]
        if self.forbidden is not None and np.array_equal(closest_gem, self.forbidden):
            return None
        closest_gem = tuple(closest_gem)
        if not world.is_accessible(closest_gem):
            return None
        self.getting_gem = closest_gem
        return closest_gem

    def reached_target(self) -> None:
        self.getting_gem = None

    def cannot_go_there(self):
        self.forbidden = self.getting_gem
        self.getting_gem = None
