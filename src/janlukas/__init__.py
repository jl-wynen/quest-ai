from functools import partial

from .ai import Norne, Waiter

team = {
    "Verðandi": partial(Norne, kind="healer", index=0),
    "Skuld": partial(Waiter, kind="healer", index=1),
    "Urðr": partial(Waiter, kind="healer", index=2),
}
