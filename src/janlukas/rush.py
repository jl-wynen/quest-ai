from . import _janlukas as jl
from .state import (
    AngleGemGetter,
    DistanceGemGetter,
    Regicide,
    State,
    get_enemy_king,
    unstuck,
)


def rush(team: str, index: int, low_start: bool) -> State:
    if index == 2:
        return CollectGems(team=team, index=index, low_start=low_start)
    return TravelAcross(team=team, index=index, low_start=low_start)


class TravelAcross(State):
    # Indexed by team of self and knight index
    TARGETS = {
        "red": ((1700, 100), (1700, 480), (1700, 860)),
        "blue": ((100, 100), (100, 480), (100, 860)),
    }

    TARGET_HIGH = {"red": (1700, 860), "blue": (100, 860)}
    TARGET_CENTRE = {"red": (1700, 480), "blue": (100, 480)}
    TARGET_LOW = {"red": (1700, 100), "blue": (100, 100)}

    def __init__(self, team: str, index: int, low_start: bool) -> None:
        super().__init__(team=team, index=index)
        self.low_start = low_start
        if index == 1:
            self.target = TravelAcross.TARGET_CENTRE[team]
        elif low_start:
            if index == 0:
                self.target = TravelAcross.TARGET_LOW[team]
            else:
                self.target = TravelAcross.TARGET_HIGH[team]
        else:
            if index == 0:
                self.target = TravelAcross.TARGET_HIGH[team]
            else:
                self.target = TravelAcross.TARGET_LOW[team]

        self.gem_getter = AngleGemGetter(tolerance=0.2 if index == 0 else 0.8)

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
        return self.make(ScanEnemyZone, low_start=self.low_start)

    def cannot_go_there(self) -> tuple[State, tuple]:
        if self.gem_getter.getting_gem is not None:
            self.gem_getter.cannot_go_there()
            return self, self.target
        # just hope that this works
        return self.make(ScanEnemyZone, low_start=self.low_start), self.target


class ScanEnemyZone(State):
    # Indexed by team of self and knight index
    TARGET_HIGH = {"red": (1700, 860), "blue": (100, 860)}
    TARGET_LOW = {"red": (1700, 100), "blue": (100, 100)}

    def __init__(self, team: str, index: int, low_start: bool) -> None:
        super().__init__(team=team, index=index)
        if low_start:
            if index == 2:
                self.target = ScanEnemyZone.TARGET_LOW[team]
            else:
                self.target = ScanEnemyZone.TARGET_HIGH[team]
        else:
            if index == 2:
                self.target = ScanEnemyZone.TARGET_HIGH[team]
            else:
                self.target = ScanEnemyZone.TARGET_LOW[team]

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
    # indexed by team and low_start
    GENERAL_TARGET = {
        "red": {True: (1700, 860), False: (1700, 100)},
        "blue": {True: (100, 860), False: (100, 100)},
    }

    def __init__(self, team: str, index: int, low_start: bool) -> None:
        super().__init__(team=team, index=index)
        self.gem_getter = DistanceGemGetter()
        self.target = CollectGems.GENERAL_TARGET[team][low_start]
        self.low_start = low_start

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
        return self.make(ScanEnemyZone, low_start=self.low_start), self.target
