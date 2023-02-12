import timeit

import numpy as np

from janlukas.ai import jl


def make_world(n_repeat: int) -> jl.World:
    nx = 18
    ny = 12
    local_map = np.zeros((nx, ny), dtype="int64")
    for p in (
        (3, 0),
        (3, 1),
        (3, 3),
        (3, 4),
        (3, 5),
        (2, 5),
        (0, 5),
        (4, 5),
        (5, 5),
        (6, 5),
        (4, 6),
        (4, 7),
        (4, 9),
        (4, 10),
        (4, 11),
        (8, 5),
        (9, 5),
        (10, 5),
        (10, 4),
        (10, 3),
        (10, 2),
        (10, 0),
        (10, 6),
        (10, 7),
        (10, 8),
        (10, 9),
        (10, 11),
        (11, 6),
        (12, 6),
        (14, 6),
        (15, 6),
        (17, 6),
        (17, 0),
        (16, 0),
        (15, 0),
        (17, 1),
        (16, 1),
        (15, 1),
        (17, 2),
        (16, 2),
        (15, 2),
    ):
        local_map[p] = 1

    local_map = np.repeat(np.repeat(local_map, n_repeat, axis=0), n_repeat, axis=1)

    world = jl.World(local_map.shape)
    world.incorporate(local_map, knight_pos=(nx // 2, ny // 2), view_range=max(nx, ny))
    return world


def main() -> None:
    n_repeat = 40
    start = (1 * n_repeat, 11 * n_repeat)
    target = (17 * n_repeat, 4 * n_repeat)
    world = make_world(n_repeat)
    pathfinder = jl.Path(world)
    code = """
pathfinder.set_target(target)
pathfinder.next(start, world, speed=1.0, dt=1.0)
    """

    n = 10
    t = timeit.timeit(
        code,
        number=n,
        globals={
            "pathfinder": pathfinder,
            "start": start,
            "target": target,
            "world": world,
        },
    )
    print(f"Time: {t / n:.4f}s")


# 913eb18: 0.1299s  (OG)
#        : 0.1433s  (factor out costs)
#        : 0.1110s  (Array2 in costs)
#        : 0.0763s  (Array2 in costs + parents)

if __name__ == "__main__":
    main()
