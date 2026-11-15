def get_inning_toppers_bat(game: dict, innings: int):
    batters: list = [] + game["innings"][innings]["batter_stats"]
    batters.sort(key=lambda x: 0 if not x["dismissed"] else 1)
    batters.sort(key=lambda x: x["balls"])
    batters.sort(key=lambda x: x["runs"], reverse=True)
    return batters


def get_inning_toppers_bowl(game: dict, innings: int):
    bowlers: list = [] + game["innings"][innings]["bowler_stats"]
    bowlers.sort(key=lambda x: 1 if x["balls"] <= 0 else 0)
    bowlers.sort(key=lambda x: x["runs"] / (1 + x["balls"]))
    bowlers.sort(key=lambda x: x["runs"] if x["balls"] <= 0 else x["runs"] / x["balls"])
    bowlers.sort(key=lambda x: x["wickets"], reverse=True)
    return bowlers
