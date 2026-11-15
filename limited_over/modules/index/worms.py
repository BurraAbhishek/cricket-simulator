from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from bin.models.team import Team
from bin.mongoinserts.load_games import fetch_game
from modules.index.summary import get_summary


def get_worms(request, clas, id):
    game = fetch_game(clas, id)
    if game is None:
        raise PermissionDenied
    summary = get_summary(game)
    datasets = []
    datapoints = []
    max_balls = 0
    team1color = "inherit"
    team2color = "inherit"
    for k, i in enumerate(game["innings"]):
        team = Team(i["batting_team"])
        color = team.get("color")
        color_match = bool(
            Team(i["batting_team"]).get("color")
            == Team(i["bowling_team"]).get("color")
        )
        if k == 0:
            team1color = color
            if color_match:
                color = "#eee"
                team1color = "#eee"
        elif k == 1:
            team2color = color
            if color_match:
                color = "#d2a47c"
                team2color = "#d2a47c"
        name = team.get("name")
        progression = []
        wickets = []
        ball = 0
        score = 0
        wicket = 0
        progression.append({
            "ball": 0,
            "score": 0,
            "wicket": 0,
            "dismissed": False,
            "scoreText": " " + name + ": 0/0"
        })
        for j in i["data"]:
            for k in j:
                dismissed = bool(False if len(k["dismissed_batter"]) < 1 else True)
                if k["legal_delivery"]:
                    ball += 1
                score += k["score_int"]
                wicket += int(0 if len(k["dismissed_batter"]) < 1 else 1)
                if k["legal_delivery"]:
                    progression.append({
                        "ball": ball,
                        "score": score,
                        "wicket": wicket,
                        "dismissed": dismissed,
                        "scoreText": " " + name + ": " + str(score) + "/" + str(wicket)
                    })
                elif k["_id"] == i["data"][-1][-1]["_id"]:
                    progression[-1] = {
                        "ball": ball,
                        "score": score,
                        "wicket": wicket,
                        "dismissed": dismissed,
                        "scoreText": " " + name + ": " + str(score) + "/" + str(wicket)
                    }
                if dismissed:
                    wickets.append(
                        {
                            "x": ball,
                            "y": score
                        }
                    )
        dataset_item = {
            "type": "line",
            "fill": False,
            "lineTension": 0,
            "backgroundColor": color,
            "borderColor": color,
            "pointRadius": 0,
            "data": [i["score"] for i in progression]
        }
        wickets_item = {
            "type": "scatter",
            "fill": False,
            "lineTension": 0,
            "backgroundColor": color,
            "pointRadius": 5,
            "data": wickets
        }
        datapoints.append(progression)
        datasets.append(dataset_item)
        datasets.append(wickets_item)
        max_balls = max(max_balls, ball)
    labels = [i for i in range(max_balls + 1)]
    return render(
        request,
        "worms.html",
        {
            "summary": summary,
            "clas": clas,
            "id": id,
            "worm_labels": labels,
            "worm_data": datasets,
            "worm_data_all": datapoints,
            "team1color": team1color,
            "team2color": team2color
        }
    )
