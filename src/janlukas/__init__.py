from functools import partial

from .ai import Norne, Waiter  # noqa: F401

team = {
    "Verðandi": partial(Norne, kind="healer", index=0),
    "Skuld": partial(Norne, kind="healer", index=1),
    "Urðr": partial(Norne, kind="healer", index=2),
}
