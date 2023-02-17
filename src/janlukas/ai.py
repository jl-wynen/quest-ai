from __future__ import annotations

from quest.core.ai import BaseAI

from . import _janlukas as jl
from .rush import rush

CREATOR = "JanDerGrosse"
WORLD_SHAPE = (1792, 960)


ENEMY_TEAM_NAME = {"red": "blue", "blue": "red"}


def make_world(team: str, index: int) -> jl.World:
    if index == 0:
        make_world.world[team] = jl.World(WORLD_SHAPE)
    return make_world.world[team]


make_world.world = {"red": None, "blue": None}


class Knight(BaseAI):
    def __init__(self, kind: str, index: int, **kwargs) -> None:
        super().__init__(creator=CREATOR, kind=kind, **kwargs)
        if not kwargs:
            return

        self.knight_index = index
        self.world = make_world(self.team, index)
        self.path = jl.Path(self.world)
        self.tick = -10

        self.state = None

    def run(self, t: float, dt: float, info: dict) -> None:
        self.tick += 1
        me = info["me"]
        pos = tuple(me["position"])
        view_radius = me["view_radius"]

        if self.state is None:
            self.state = rush(
                team=self.team,
                index=self.knight_index,
                low_start=pos[1] < WORLD_SHAPE[1] // 2,
            )

        if self.tick % 10 == self.knight_index + 1:
            self.world.incorporate(info["local_map"], pos, view_radius)
            self.path.recompute_in_one_turn()

        self.state, target = self.state.step(info=info, world=self.world)
        self.path.set_target(target)

        to = self.find_path(target, pos, speed=me["speed"], dt=dt)

        if to is not None:
            self.stop = False
            self.goto = to
        else:
            self.stop = True
            self.state = self.state.reached_target(info=info, world=self.world)

    def find_path(
        self, target: tuple, pos: tuple, speed: float, dt: float, _iter: int = 0
    ) -> tuple | None:
        if _iter == 5:
            return None  # give up
        try:
            return self.path.next(pos, self.world, speed=speed, dt=dt)
        except ValueError:
            print(f"{self.team}.{self.knight_index}: target unreachable: {target}")
        except RuntimeError:
            print(
                f"{self.team}.{self.knight_index}: "
                f"failed to find path from {pos} to {target}"
            )
        self.state, target = self.state.cannot_go_there()
        self.path.set_target(target)
        return self.find_path(target, pos, speed, dt, _iter + 1)


class Waiter(BaseAI):
    def __init__(self, kind: str, index: int, *args, **kwargs) -> None:
        super().__init__(*args, creator=CREATOR, kind=kind, **kwargs)
        if not kwargs:
            return
        self.knight_index = index
        self.world = make_world(self.team, index)

    def run(self, t: float, dt: float, info: dict) -> None:
        self.stop = True
