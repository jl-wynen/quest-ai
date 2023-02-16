from . import _janlukas as jl
from .state import Regicide, State, get_enemy_king


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

    def step(self, *, info: dict, world: jl.World) -> tuple[State, tuple]:
        if (enemy_king := get_enemy_king(world, info)) is not None:
            world.enemy_king = enemy_king
            return self.next_state(Regicide, info=info, world=world)
        return self, self.target

    def reached_target(self, *, info: dict, world: jl.World) -> State:
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
