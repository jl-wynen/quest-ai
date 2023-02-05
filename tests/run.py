"""Run a test game."""

from quest.core.match import Match
from quest.core.manager import make_team
from quest.players.templateAI_flag import team as TemplateTeam
from janlukas import team as JanLukasTeam

match = Match(red_team=make_team(JanLukasTeam),
              blue_team=make_team(TemplateTeam),
              best_of=1,
              game_mode='flag')
match.play(speedup=1, show_messages=False)
