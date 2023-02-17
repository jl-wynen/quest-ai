"""Run a test game."""

import random

import numpy as np
from quest.core.manager import make_team
from quest.core.match import Match
from quest.players.templateAI_king import team as TemplateTeam

from janlukas import team as JanLukasTeam


def main() -> None:
    # random.seed(123)
    # np.random.seed(9982)
    random.seed(3)
    np.random.seed(3)

    match = Match(
        # red_team=make_team(TemplateTeam),
        # blue_team=make_team(JanLukasTeam),
        red_team=make_team(JanLukasTeam),
        blue_team=make_team(TemplateTeam),
        best_of=1,
        game_mode="king",
    )
    match.play(speedup=1, show_messages=False)


if __name__ == "__main__":
    main()
