from functools import partial

from .ai import Knight, Waiter  # noqa: F401

team = {
    "Ni": partial(Knight, kind="warrior", index=0),
    "Rabbit of Caerbannoch": partial(Knight, kind="warrior", index=1),
    "Tim": partial(Knight, kind="healer", index=2),
}
