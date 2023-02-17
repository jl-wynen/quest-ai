"""Run a test game."""

from quest.core.manager import make_team
from quest.core.match import Match
from quest.players.templateAI_king import team as TemplateTeam

from janlukas import team as JanLukasTeam


def main() -> None:
    match = Match(
        red_team=make_team(JanLukasTeam),
        blue_team=make_team(TemplateTeam),
        best_of=1,
        game_mode="king",
    )
    match.play(speedup=2, show_messages=False)


if __name__ == "__main__":
    main()
