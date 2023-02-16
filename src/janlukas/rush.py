import numpy as np

from . import _janlukas as jl
from .state import Regicide, State, get_enemy_king, unstuck


def rush(team: str, index: int) -> State:
    return TravelAcross(team=team, index=index)


class TravelAcross(State):
    # Indexed by team of self and knight index
    TARGETS = {
        "red": ((1700, 100), (1700, 860), (1700, 480)),
        "blue": ((100, 100), (100, 860), (100, 480)),
    }

    def __init__(self, team: str, index: int) -> None:
        super().__init__(team=team, index=index)
        self.target = TravelAcross.TARGETS[team][index]
        self.getting_gem: tuple | None = None

    @unstuck
    def step(self, *, info: dict, world: jl.World) -> tuple[State, tuple]:
        if (enemy_king := get_enemy_king(world, info)) is not None:
            world.enemy_king = enemy_king
            return self.next_state(Regicide, info=info, world=world)

        if self._get_gem(info) is not None:
            return self, self.getting_gem

        return self, self.target

    def reached_target(self, *, info: dict, world: jl.World) -> State:
        if self.getting_gem is not None:
            self.getting_gem = None
            return self
        return self.make(ScanEnemyZone)

    def _get_gem(self, info: dict) -> tuple[State, tuple] | None:
        if self.getting_gem is not None:
            return self, self.getting_gem

        gems = info["gems"]
        if not gems:
            return None

        pos = info["me"]["position"]
        gems = np.c_[gems["x"], gems["y"]]

        v = self.target - pos
        gv = gems - pos
        angles = np.arccos(
            np.dot(gv, v) / np.linalg.norm(v) / np.linalg.norm(gv, axis=1)
        )
        gem_index = np.argmin(angles)
        if abs(angles[gem_index]) < 0.78:
            closest_gem = gems[gem_index]
            self.getting_gem = tuple(closest_gem)
            return self, tuple(closest_gem)

        return None


class ScanEnemyZone(State):
    # Indexed by team of self and knight index
    TARGETS = {
        "red": ((1700, 860), (1700, 100), (1700, 100)),
        "blue": ((100, 860), (100, 100), (100, 100)),
    }

    def __init__(self, team: str, index: int) -> None:
        super().__init__(team=team, index=index)
        self.target = ScanEnemyZone.TARGETS[team][index]

    @unstuck
    def step(self, *, info: dict, world: jl.World) -> tuple[State, tuple]:
        if (enemy_king := get_enemy_king(world, info)) is not None:
            world.enemy_king = enemy_king

            x = self.next_state(Regicide, info=info, world=world)
            return x
        return self, self.target

    def reached_target(self, *, info: dict, world: jl.World) -> State:
        if (enemy_king := get_enemy_king(world, info)) is not None:
            world.enemy_king = enemy_king
            return self.make(Regicide)
        return self
