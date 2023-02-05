import pytest

from janlukas.ai import jl


@pytest.mark.parametrize("target", ((3, 4), (1, 2), (0, 0), (9, 4), (9, 0), (4, 0)))
def test_path(target):
    world = jl.World((10, 5))
    path = jl.Path()
    path.set_target(target)
    pos = (2, 1)
    for _ in range(100):
        pos = path.next(pos, world, speed=1.0, dt=1.0)
        if pos is None:
            raise AssertionError("Failed to find path")
        if pos == target:
            break
    else:
        raise AssertionError("Did not reach target")


def test_path_start_at_target_does_nothing():
    world = jl.World((10, 5))
    path = jl.Path()
    path.set_target((2, 3))
    pos = (2, 3)
    assert path.next(pos, world, speed=1.0, dt=1.0) is None
