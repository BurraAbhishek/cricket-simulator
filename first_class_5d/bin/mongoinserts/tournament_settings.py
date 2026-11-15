TOURNAMENT_SETTINGS = {
    "theme": "dark", # only dark is supported
    "test": True, # Is it test tournament or not
    "groupstage": True, # Only True is supported.
    "rated": True, # are games rated or unrated
    "knockout": 2, # 1 for only final, 2 for semifinal and final, etc.
    "thirdplace": True, # 3rd-place Playoff
    "year": 2025, # Tournament year
    "groupstage_scores": 0, # 0 for score, 1 for tiebreak score
    "series_games": 1, # number of round robin iterations
    "milestone": True, # Special milestone rendering in commentary
    "bots": False, # bots present/absent in tournament.
    "bot_group": False, # if True, Normal Group1 and BOT Group2
    "bot_order": -1, # 1 - increasing, -1 - decreasing
    "team_flag": True, # to show or not to show team flags
    "table_flag": True, # flags in groupstage table, team flag
    "avatar": 2, # 0 - default, 1 - no background, 2 - face only
    "replay_interval": 10, # interval in ms. 0 to disable
    "tv_widgets": True, # To show additional insights in TV or not
    "debug": False, # if True, only Final is shown. Use for new event

    "batting_order_render": False, # if True, strict rendering
    "show_rating_chart": True, # Show the rating chart
    "show_stat_rating": True, # Show rating in individual stats

    "scoring": {
        "format": "{score}/{wickets}{declaration}",
        "declaration": " dec",
        "show_last_wicket": "", # "0", "0/10", "0 All out", "10-0", "All out 0"
    },

    # Parody only - Titles similar to rating titles.
    "player_title": True,
    "team_title": False,
    "bot_title": False,

    # Parody only - simulation metrics
    "end_of_day_seconds": 28800, # Minimum 28800 (8 hours), Maximum 86400 (24 hours)
    "draw_handling": 1, # 0 for separate draw (LC0), 1 for black-white (Stockfish)
    "simul_interval": 40000, # interval in ms. 0 to disable. 40000 for realtime
}
