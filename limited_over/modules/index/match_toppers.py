from bin.models.role import Batter, Bowler


def get_inning_toppers_bat(game: dict, innings: int):
    batters: list[Batter] = []
    for i in game["innings"][innings]["batter_stats"]:
        batter = Batter(i.get("_id"))
        batter.load_from(i)
        batters.append(batter)
    batters.sort(key=lambda x: 0 if not x.dismissed else 1)
    batters.sort(key=lambda x: x.balls)
    batters.sort(key=lambda x: x.runs, reverse=True)
    return batters


def get_inning_toppers_bowl(game: dict, innings: int):
    bowlers: list[Bowler] = []
    for i in game["innings"][innings]["bowler_stats"]:
        bowler = Bowler(i.get("_id"))
        bowler.load_from(i)
        bowlers.append(bowler)
    bowlers.sort(key=lambda x: 0 if x.balls > 0 else 1)
    bowlers.sort(key=lambda x: x.runs / (1 + x.balls))
    bowlers.sort(key=lambda x: x.economy())
    bowlers.sort(key=lambda x: x.wickets, reverse=True)
    return bowlers
