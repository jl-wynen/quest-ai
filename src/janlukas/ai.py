from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type

from quest.core.ai import BaseAI

from . import _janlukas as jl

CREATOR = "JanDerGrosse"
WORLD_SHAPE = (1792, 960)


ENEMY_TEAM_NAME = {"red": "blue", "blue": "red"}


def make_world(index: int) -> jl.World:
    if index == 0:
        make_world.world = jl.World(WORLD_SHAPE)
    return make_world.world


make_world.world = None


class Norne(BaseAI):
    def __init__(self, kind: str, index: int, **kwargs) -> None:
        super().__init__(creator=CREATOR, kind=kind, **kwargs)
        if not kwargs:
            return

        self.knight_index = index
        self.world = make_world(index)
        self.path = jl.Path(self.world)
        self.tick = -10

        self.state = TravelAcross(team=self.team, index=index)

    def run(self, t: float, dt: float, info: dict) -> None:
        self.tick += 1
        me = info["me"]
        pos = tuple(me["position"])
        view_radius = me["view_radius"]

        if self.tick % 10 == self.knight_index + 1:
            self.world.incorporate(info["local_map"], pos, view_radius)
            self.path.recompute_in_one_turn()

        self.state, target = self.state.step(info, self.world)
        self.path.set_target(target)
        if (
            to := self.path.next(pos, self.world, speed=me["speed"], dt=dt)
        ) is not None:
            self.stop = False
            self.goto = to
        else:
            self.stop = True
            self.state = self.state.reached_target()


class State(ABC):
    def __init__(self, team: str, index: int) -> None:
        self.team = team
        self.index = index

    @abstractmethod
    def step(self, info: dict, world: jl.World) -> tuple[State, tuple]:
        pass

    def reached_target(self) -> State:
        return self

    def make(self, cls: Type[State]) -> State:
        return cls(team=self.team, index=self.index)

    def enemy_flag(self, info: dict) -> tuple[float, float] | None:
        if (enemy_flag := info["flags"].get(ENEMY_TEAM_NAME[self.team])) is not None:
            return tuple(enemy_flag)
        return None


class TravelAcross(State):
    # Indexed by team of self and knight index
    TARGETS = {
        "red": ((1700, 100), (1700, 860), (1700, 480)),
        "blue": ((100, 100), (100, 860), (100, 480)),
    }

    def __init__(self, team: str, index: int) -> None:
        super().__init__(team=team, index=index)
        self.target = TravelAcross.TARGETS[team][index]

    def step(self, info: dict, world: jl.World) -> tuple[State, tuple]:
        if (enemy_flag := self.enemy_flag(info)) is not None:
            world.enemy_flag = enemy_flag
            return self.make(Regicide), world.enemy_flag
        return self, self.target

    def reached_target(self) -> State:
        return self.make(ScanEnemyZone)


class ScanEnemyZone(State):
    # Indexed by team of self and knight index
    TARGETS = {
        "red": ((1700, 860), (1700, 100), (1700, 480)),
        "blue": ((100, 860), (100, 100), (100, 480)),
    }

    def __init__(self, team: str, index: int) -> None:
        super().__init__(team=team, index=index)
        self.target = ScanEnemyZone.TARGETS[team][index]

    def step(self, info: dict, world: jl.World) -> tuple[State, tuple]:
        if (enemy_flag := self.enemy_flag(info)) is not None:
            world.enemy_flag = enemy_flag
            return self.make(Regicide), world.enemy_flag
        return self, self.target

    def reached_target(self) -> State:
        return self


class Regicide(State):
    def step(self, info: dict, world: jl.World) -> tuple[State, tuple]:
        return self, world.enemy_flag


class Waiter(BaseAI):
    def __init__(self, kind: str, index: int, *args, **kwargs) -> None:
        super().__init__(*args, creator=CREATOR, kind=kind, **kwargs)
        if not kwargs:
            return
        self.knight_index = index
        self.world = make_world(index)

    def run(self, t: float, dt: float, info: dict) -> None:
        self.stop = True
