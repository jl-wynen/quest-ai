from . import _janlukas as jl
from .state import (
    AngleGemGetter,
    DistanceGemGetter,
    Regicide,
    State,
    get_enemy_king,
    unstuck,
)


def rush(team: str, index: int) -> State:
    if index == 2:
        return CollectGems(team=team, index=index)
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
        self.gem_getter = AngleGemGetter(tolerance=0.8)

    @unstuck
    def step(self, *, info: dict, world: jl.World) -> tuple[State, tuple]:
        if (enemy_king := get_enemy_king(world, info)) is not None:
            world.enemy_king = enemy_king
            return self.next_state(Regicide, info=info, world=world)

        if self.index != 0:
            if (gem := self.gem_getter.get_gem(info, self.target, world)) is not None:
                return self, gem

        return self, self.target

    def reached_target(self, *, info: dict, world: jl.World) -> State:
        if self.gem_getter.getting_gem is not None:
            self.gem_getter.reached_target()
            return self
        return self.make(ScanEnemyZone)

    def cannot_go_there(self) -> tuple[State, tuple]:
        if self.gem_getter.getting_gem is not None:
            self.gem_getter.cannot_go_there()
            return self, self.target
        # just hope that this works
        return self.make(ScanEnemyZone), self.target


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
            return self.next_state(Regicide, info=info, world=world)
        return self, self.target

    def reached_target(self, *, info: dict, world: jl.World) -> State:
        if (enemy_king := get_enemy_king(world, info)) is not None:
            world.enemy_king = enemy_king
            return self.make(Regicide)
        return self


class CollectGems(State):
    GENERAL_TARGET = {"red": (1700, 480), "blue": (100, 480)}

    def __init__(self, team: str, index: int) -> None:
        super().__init__(team=team, index=index)
        self.gem_getter = DistanceGemGetter()
        self.target = CollectGems.GENERAL_TARGET[team]

    @unstuck
    def step(self, *, info: dict, world: jl.World) -> tuple[State, tuple]:
        if (enemy_king := get_enemy_king(world, info)) is not None:
            world.enemy_king = enemy_king
            return self.next_state(Regicide, info=info, world=world)

        if (gem := self.gem_getter.get_gem(info, self.target, world)) is not None:
            return self, gem

        return self, self.target

    def reached_target(self, *, info: dict, world: jl.World) -> State:
        if self.gem_getter.getting_gem is not None:
            self.gem_getter.reached_target()
            return self
        return self.make(ScanEnemyZone)

    def cannot_go_there(self) -> tuple[State, tuple]:
        if self.gem_getter.getting_gem is not None:
            self.gem_getter.cannot_go_there()
            return self, self.target
        # just hope that this works
        return self.make(ScanEnemyZone), self.target
