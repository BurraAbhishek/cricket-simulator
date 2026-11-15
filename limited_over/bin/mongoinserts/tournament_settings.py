TOURNAMENT_SETTINGS = {
    "theme": "dark", # only dark is supported
    "test": False, # Is it test tournament or not
    "groupstage": True, # Only True is supported.
    "overs": 20, # not valid for test matches
    "decision": 2, # 1 - bat first in R1, 2 - field first in R1.
    "rated": True, # are games rated or unrated
    "knockout": 2, # 1 for only final, 2 for semifinal and final, etc.
    "thirdplace": True, # 3rd-place Playoff
    "year": 2025, # Tournament year
    "series_games": 1, # number of double round robin iterations
    "milestone": True, # Special milestone rendering in commentary
    "bots": False, # bots present/absent in tournament.
    "bot_group": False, # if True, Normal Group1 and BOT Group2
    "bot_order": -1, # 1 - increasing, -1 - decreasing
    "team_flag": True, # to show or not to show team flags
    "table_flag": True, # flags in groupstage table, team flag
    "avatar": 2, # 0 - default, 1 - no background, 2 - face only
    "replay_interval": 0, # interval in ms. 0 to disable
    "tv_widgets": True, # To show additional insights in TV or not
    "debug": False, # if True, safe mode with no existing games

    "batting_order_render": False, # if True, strict rendering
    "show_rating_chart": True, # Show the rating chart
    "show_stat_rating": True, # Show rating in individual stats

    "scoring": "{score}/{wickets}",

    # Parody only - Titles similar to rating titles.
    "player_title": True,
    "team_title": False,
    "bot_title": False
}
