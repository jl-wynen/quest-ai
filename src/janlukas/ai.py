from quest.core.ai import BaseAI

from . import _janlukas as jl

CREATOR = "JanDerGrosse"
WORLD_SHAPE = (1792, 960)


def make_world(index: int) -> jl.World:
    if index == 0:
        make_world.world = jl.World(WORLD_SHAPE)
    return make_world.world


make_world.world = None


class Norne(BaseAI):
    def __init__(self, kind: str, index: int, *args, **kwargs) -> None:
        super().__init__(*args, creator=CREATOR, kind=kind, **kwargs)
        if not kwargs:
            return
        self.knight_index = index
        self.world = make_world(index)
        self.path = jl.Path(self.world)
        self.tick = -10

        self.path.set_target((1600, 500))

    def run(self, t: float, dt: float, info: dict) -> None:
        self.tick += 1
        me = info["me"]
        pos = tuple(me["position"])
        view_radius = me["view_radius"]

        if self.tick % 10 == self.knight_index + 1:
            self.world.incorporate(info["local_map"], pos, view_radius)
            self.path.recompute_in_one_turn()

        if (
            to := self.path.next(pos, self.world, speed=me["speed"], dt=dt)
        ) is not None:
            self.stop = False
            self.goto = to
        else:
            t = tuple(map(int, info["flags"]["red"]))
            self.path.set_target(t)
            self.stop = True


class Waiter(BaseAI):
    def __init__(self, kind: str, index: int, *args, **kwargs) -> None:
        super().__init__(*args, creator=CREATOR, kind=kind, **kwargs)
        if not kwargs:
            return
        self.knight_index = index
        self.world = make_world(index)

    def run(self, t: float, dt: float, info: dict) -> None:
        self.stop = True
