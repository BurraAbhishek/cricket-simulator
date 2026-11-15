from bin.models.team import Team
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.rating.fsmosca.glicko2 import Glicko2


def rate_game(team1, team2, winner, margin=""):
    env = Glicko2(tau=0.5)
    r1 = env.create_rating(
        team1["rating_glicko2"]["rating"],
        team1["rating_glicko2"]["rd"],
        team1["rating_glicko2"]["vol"]
    )
    r2 = env.create_rating(
        team2["rating_glicko2"]["rating"],
        team2["rating_glicko2"]["rd"],
        team2["rating_glicko2"]["vol"]
    )
    p = [None, None]
    if winner == team1["_id"]:
        p[0], p[1] = env.rate_1vs1(r1, r2, drawn=False)
    elif winner == team2["_id"]:
        p[1], p[0] = env.rate_1vs1(r2, r1, drawn=False)
    elif margin.lower() == "double forfeit":
        _, p[0] = env.rate_1vs1(r2, r1, drawn=False)
        _, p[1] = env.rate_1vs1(r1, r2, drawn=False)
    else:
        p[0], p[1] = env.rate_1vs1(r1, r2, drawn=True)
    if can_change_rating(team1["_id"]):
        team1["rating_glicko2"] = {
            "rating": p[0].mu,
            "rd": p[0].phi,
            "vol": p[0].sigma
        }
    if can_change_rating(team2["_id"]):
        team2["rating_glicko2"] = {
            "rating": p[1].mu,
            "rd": p[1].phi,
            "vol": p[1].sigma
        }


def can_change_rating(team_id):
    # Teams with no rating change
    # Either because (good) tournament is unrated
    # or (good) they are extremely stable and won against lower rated
    # or (bad) they violated the Terms of Service.
    # or (bot) they are fixed-rating bots
    # good (1)
    if TOURNAMENT_SETTINGS["rated"] is False:
        return False
    # good (4)
    if Team(team_id).ai():
        return False
    # can change
    return True
