import matplotlib.pyplot as plt
import numpy as np

from janlukas.ai import jl


def make_world() -> jl.World:
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

    local_map = np.repeat(np.repeat(local_map, 3, axis=0), 3, axis=1)

    world = jl.World(local_map.shape)
    world.incorporate(local_map, knight_pos=(nx // 2, ny // 2), view_range=max(nx, ny))
    return world


def find_path(
    world: jl.World, start: tuple[int, int], end: tuple[int, int]
) -> list[tuple[int, int]]:
    path = jl.Path(world)
    path.set_target(end)
    res = [start]
    while (n := path.next(res[-1], world, speed=1.0, dt=1.0)) is not None:
        res.append(n)
    return res


def path_length(path: list[tuple[int, int]]) -> float:
    a = path[0]
    length = 0.0
    for b in path[1:]:
        length += np.linalg.norm([a[0] - b[0], a[1] - b[1]])
        a = b
    return length


def main() -> None:
    world = make_world()
    # 1  (A*: 51.7, theta*: 50.7)
    # path = find_path(world, (1 * 3, 8 * 3), (13 * 3, 3 * 3))
    # 2  (A*: 61.6, theta*: 60.7)
    # path = find_path(world, (6, 1), (52, 22))
    # 3  (A*: 69.8, theta*: 63.5)
    path = find_path(world, (2, 33), (52, 13))
    print("length", path_length(path))

    grid = world.get_map()
    fig, ax = plt.subplots()
    ax.imshow(grid.T[::-1], interpolation="none")

    x = []
    y = []
    for p in path:
        x.append(p[0])
        y.append(grid.shape[1] - 1 - p[1])
    ax.plot(x, y, ls="-", marker=".")

    ax.set_xticks(np.arange(-0.5, grid.shape[0] + 0.5), minor=True)
    ax.set_yticks(np.arange(-0.5, grid.shape[1] + 0.5), minor=True)
    ax.grid(which="minor", color="k", linestyle="-", linewidth=0.5)

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
