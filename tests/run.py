"""Run a test game."""

import random

import numpy as np
from janlukas import team as JanLukasTeam
from quest.core.manager import make_team
from quest.core.match import Match
from quest.players.templateAI_flag import team as TemplateTeam


def main() -> None:
    random.seed(123)
    np.random.seed(9982)

    match = Match(
        red_team=make_team(JanLukasTeam),
        blue_team=make_team(TemplateTeam),
        best_of=1,
        game_mode="flag",
    )
    match.play(speedup=1, show_messages=False)


if __name__ == "__main__":
    main()
