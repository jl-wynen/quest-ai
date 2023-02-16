from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type

from quest.core.ai import BaseAI

from . import _janlukas as jl

CREATOR = "JanDerGrosse"
WORLD_SHAPE = (1792, 960)


ENEMY_TEAM_NAME = {"red": "blue", "blue": "red"}


def make_world(team: str, index: int) -> jl.World:
    if index == 0:
        make_world.world[team] = jl.World(WORLD_SHAPE)
    return make_world.world[team]


make_world.world = {"red": None, "blue": None}


class Norne(BaseAI):
    def __init__(self, kind: str, index: int, **kwargs) -> None:
        super().__init__(creator=CREATOR, kind=kind, **kwargs)
        if not kwargs:
            return

        self.knight_index = index
        self.world = make_world(self.team, index)
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
    def step(self, info: dict, world: jl.World) -> tuple[State, tuple]:
        pass

    def reached_target(self) -> State:
        return self

    def make(self, cls: Type[State]) -> State:
        return cls(team=self.team, index=self.index)


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
        if (enemy_king := get_enemy_king(world, info)) is not None:
            world.enemy_king = enemy_king
            return self.make(Regicide), world.enemy_king
        return self, self.target

    def reached_target(self) -> State:
        return self.make(ScanEnemyZone)


class ScanEnemyZone(State):
    # Indexed by team of self and knight index
    TARGETS = {
        "red": ((1700, 860), (1700, 100), (1700, 100)),
        "blue": ((100, 860), (100, 100), (100, 100)),
    }

    def __init__(self, team: str, index: int) -> None:
        super().__init__(team=team, index=index)
        self.target = ScanEnemyZone.TARGETS[team][index]

    def step(self, info: dict, world: jl.World) -> tuple[State, tuple]:
        if (enemy_king := get_enemy_king(world, info)) is not None:
            world.enemy_king = enemy_king
            return self.make(Regicide), world.enemy_king
        return self, self.target

    def reached_target(self) -> State:
        return self


class Regicide(State):
    def step(self, info: dict, world: jl.World) -> tuple[State, tuple]:
        return self, world.enemy_king


class Waiter(BaseAI):
    def __init__(self, kind: str, index: int, *args, **kwargs) -> None:
        super().__init__(*args, creator=CREATOR, kind=kind, **kwargs)
        if not kwargs:
            return
        self.knight_index = index
        self.world = make_world(index)

    def run(self, t: float, dt: float, info: dict) -> None:
        self.stop = True
