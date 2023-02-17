from __future__ import annotations

import numpy as np
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
        self._handle_messages(info["friends"])

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

    def _handle_messages(self, friends: list[dict]) -> None:
        for friend in friends:
            if (king := _parse_messages(friend["message"])) is not None:
                if (self.team == "red" and king[0] > WORLD_SHAPE[1] // 2) or (
                    self.team == "blue" and king[0] < WORLD_SHAPE[0] // 2
                ):
                    self.world.enemy_king = king

            if (king := self.world.enemy_king) is not None:
                self.message = {"king": king}


class Waiter(BaseAI):
    def __init__(self, kind: str, index: int, *args, **kwargs) -> None:
        super().__init__(*args, creator=CREATOR, kind=kind, **kwargs)
        if not kwargs:
            return
        self.knight_index = index
        self.world = make_world(self.team, index)

    def run(self, t: float, dt: float, info: dict) -> None:
        self.stop = True


def _parse_messages(message) -> tuple | None:
    if message is None:
        return None
    if (king := _get_king_message(message)) is not None:
        if isinstance(king, (tuple, list)) and len(king) == 2:
            return float(king[0]), float(king[1])
        if isinstance(king, np.ndarray) and king.shape == (2,):
            return float(king[0]), float(king[1])

    return None


def _get_king_message(message):
    if isinstance(message, dict):
        for k in (
            "enemy_king",
            "enemy king",
            "enemy-king",
            "king",
            "enemy_flag",
            "enemy flag",
            "enemy-flag",
            "flag",
        ):
            if (king := message.get(k)) is not None:
                return king
    elif isinstance(message, (tuple, list, np.ndarray)):
        return message
    return None
