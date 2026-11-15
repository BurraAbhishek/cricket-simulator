"""
URL configuration for fb14_cricket_t20_e25 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
# Index
from modules.index.index import index
# Data
from modules.profile.player import get_member
from modules.profile.team import get_team, get_lineup, get_result, get_result_page
from modules.index.team_progression import fetch_team_progression
# Replay
from modules.exportgame.export_completed_json import raw_match_data
from modules.index.summary import match_view
from modules.index.matchsummary import match_summary
from modules.index.commentary import get_commentary
from modules.index.scorecard import get_scorecard
from modules.index.partnership import get_partnerships
from modules.index.worms import get_worms
from modules.engine.wdlrenderer import get_analysis
from modules.engine.matchref.nomination import render_nomination
from modules.engine.matchref.matchreport import render_match_report
# stats
from modules.stat.highest_totals import render_max_totals
from modules.stat.highest_aggregates import render_max_aggregates
from modules.stat.highest_win1 import render_highest_win1
from modules.stat.highest_win2 import render_highest_win2
from modules.stat.highest_successful_chases import render_highest_successful_chases
from modules.stat.highest_scores import render_highest_score
from modules.stat.most_potm import render_stat_potm
from modules.stat.most_runs import render_most_runs
from modules.stat.most_runs import render_most_fours
from modules.stat.most_runs import render_most_sixes
from modules.stat.most_runs import render_most_50s
from modules.stat.most_runs import render_most_100s
from modules.stat.most_runs import render_most_200s
from modules.stat.most_runs import render_most_boundaries
from modules.stat.most_runs import render_max_strike_rate
from modules.stat.most_runs import render_max_batting_average
from modules.stat.most_wickets import render_most_wickets
from modules.stat.most_wickets import render_best_economy
from modules.stat.most_wickets import render_best_bowling_average
from modules.stat.best_bowl_figures import render_best_bowl_figures
from modules.stat.highest_partnership1 import render_highest_partnership1
from modules.stat.highest_partnership2 import render_highest_partnership2
# Live replay
from modules.replay.live import replayGame
from modules.replay.tv import watchReplayGameOnTV
from modules.replay.display.commentary import get_replay_commentary
from modules.replay.display.scorecard import get_replay_scorecard
from modules.replay.controllers.innings import nextReplayDelivery
# Live match
from modules.live.live import liveGame
from modules.live.tv import watchLiveGameOnTV
from modules.live.controllers.comment import addComment
from modules.exportgame.export_game import export_live_game
from modules.live.controllers.next_innings import live_next_innings
# Live commentary
from modules.live.display.commentary import get_live_commentary
from modules.live.display.scorecard import get_live_scorecard
# Autonomous Tournament
# from bin.mongoinserts.mongosetup import setup
from bin.mongoinserts.autotournament import play_from_match, play_only_match
from bin.mongoinserts.autotournament import render_autotournament_ui
# Simul
from modules.simul.index import init_simul, render_simul, simul_next, simul_previous


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index),
    path('member/<slug:id>', get_member),
    path('team/<slug:id>', get_team),
    path('team/<slug:id>/lineup', get_lineup),
    path('team/<slug:id>/result', get_result),
    path('team/<slug:id>/result/<slug:page>', get_result_page),
    path('teamprogression/<slug:id>', fetch_team_progression),
    path('matches/<slug:clas>/<slug:id>', raw_match_data),
    path('matchsummary/<slug:clas>/<slug:id>', match_summary),
    path('commentary/<slug:clas>/<slug:id>', get_commentary),
    path('wormgraph/<slug:clas>/<slug:id>', get_worms),
    path('analysis/<slug:clas>/<slug:id>', get_analysis),
    path('scorecard/<slug:clas>/<slug:id>/<int:innings>', get_scorecard),
    path('partnerships/<slug:clas>/<slug:id>/<int:innings>', get_partnerships),
    path('stats/', TemplateView.as_view(template_name="stat/index.html")),
    path('stats/highest-totals', render_max_totals),
    path('stats/highest-aggregates', render_max_aggregates),
    path('stats/biggest-win1', render_highest_win1),
    path('stats/biggest-win2', render_highest_win2),
    path('stats/highest-successful-chases', render_highest_successful_chases),
    path('stats/highest-scores', render_highest_score),
    path('stats/most-potm', render_stat_potm),
    path('stats/most-runs', render_most_runs),
    path('stats/most-fours', render_most_fours),
    path('stats/most-sixes', render_most_sixes),
    path('stats/most-boundaries', render_most_boundaries),
    path('stats/most-fifties', render_most_50s),
    path('stats/most-hundreds', render_most_100s),
    path('stats/most-double-hundreds', render_most_200s),
    path('stats/most-wickets', render_most_wickets),
    path('stats/best-economy-rates', render_best_economy),
    path('stats/best-bowling-figures', render_best_bowl_figures),
    path('stats/best-bowling-averages', render_best_bowling_average),
    path('stats/highest-strike-rates', render_max_strike_rate),
    path('stats/highest-batting-averages', render_max_batting_average),
    path('stats/highest-partnership-by-runs', render_highest_partnership1),
    path('stats/highest-partnership-by-wickets', render_highest_partnership2),
    path('replay/', replayGame),
    path('replay/tv', watchReplayGameOnTV),
    path('replay/next', nextReplayDelivery),
    path('replay/commentary', get_replay_commentary),
    path('replay/scorecard/<int:innings>', get_replay_scorecard),
    path('replay/<slug:clas>/<slug:id>', replayGame),
    path('live/', liveGame),
    path('live/tv/', watchLiveGameOnTV),
    path('live/addcomment/', addComment),
    path('live/export/', export_live_game),
    path('live/commentary/', get_live_commentary),
    path('live/scorecard/<int:innings>', get_live_scorecard),
    path('live/nextinnings', live_next_innings),
    path('play', render_autotournament_ui),
    path('play/from/<int:m_id>', play_from_match),
    path('play/only/<int:m_id>', play_only_match),
    path('simul', render_simul),
    path('simul/new', init_simul),
    path('simul/next', simul_next),
    path('simul/previous', simul_previous),
    path('summary/<slug:clas>/<slug:id>', match_view),
    path('nomination/<slug:clas>/<slug:id>/<int:index>', render_nomination),
    path('matchreport/<slug:clas>/<slug:id>', render_match_report),
]
