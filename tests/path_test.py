import pytest

from janlukas.ai import jl


@pytest.mark.parametrize("start", ((3, 4), (1, 2), (0, 0), (9, 4), (9, 0), (4, 0)))
@pytest.mark.parametrize("target", ((3, 4), (1, 2), (0, 0), (9, 4), (9, 0), (4, 0)))
def test_path_reaches_target(start, target):
    if start == target:
        return
    world = jl.World((10, 5))
    path = jl.Path()
    path.set_target(target)
    pos = start
    for _ in range(100):
        pos = path.next(pos, world, speed=1.0, dt=1.0)
        if pos is None:
            raise AssertionError("Failed to find path")
        if pos == target:
            break
    else:
        raise AssertionError("Did not reach target")


@pytest.mark.parametrize("pos", ((3, 4), (1, 2), (0, 0), (9, 4), (9, 0), (4, 0)))
def test_path_start_at_target_does_nothing(pos):
    world = jl.World((10, 5))
    path = jl.Path()
    path.set_target(pos)
    assert path.next(pos, world, speed=1.0, dt=1.0) is None


@pytest.mark.parametrize("start", ((3, 4), (1, 2), (0, 0), (9, 4), (9, 0), (4, 0)))
@pytest.mark.parametrize("target", ((3, 4), (1, 2), (0, 0), (9, 4), (9, 0), (4, 0)))
def test_smoothing_on_empty_world_give_length_1_path(start, target):
    if start == target:
        return
    world = jl.World((10, 5))
    path = jl.Path()
    path.set_target(target)
    assert path.next(start, world, speed=1.0, dt=1.0) == target
