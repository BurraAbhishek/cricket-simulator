from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from bin.models.team import Team
from bin.mongoinserts.load_games import fetch_game
from modules.index.summary import get_summary
from modules.engine.acpl import acpl


def get_analysis(request, clas, id):
    game = fetch_game(clas, id)
    if game is None:
        raise PermissionDenied
    summary = get_summary(game)
    eval_start = game.get("prediction", {"white": 1/3, "draw": 1/3, "black": 1/3, "eval_verbose": "0.0"})
    eval_start["inning"] = 0
    eval_start["inning_verbose"] = "Starting Position"
    eval_start["id"] = "start"
    eval_dataset = [eval_start]
    datasets = []
    team1color = Team(game["team1"]).get("color")
    team2color = Team(game["team2"]).get("color")
    for i0, i in enumerate(game["innings"]):
        for j in i["data"]:
            for k in j:
                l = dict(k["evaluation"])
                l["inning"] = i0
                if i0 < 2:
                    l["inning_verbose"] = Team(i["batting_team"]).name() + " 1st Innings"
                else:
                    l["inning_verbose"] = Team(i["batting_team"]).name() + " 2nd Innings"
                l["id"] = k["_id"]
                eval_dataset.append(l)
    if game["winner"] is None or game["winner"] == "":
        color = "#FFD700"
    else:
        color = Team(game["winner"]).get("color")
    dataset_item = {
        "type": "line",
        "fill": False,
        "lineTension": 0,
        "backgroundColor": color,
        "borderColor": color,
        "pointRadius": 0,
        "data": [i["white"] - i["black"] for i in eval_dataset]
    }
    kv_store = {
        "team1name": Team(game["team1"]).name(),
        "team2name": Team(game["team2"]).name(),
        "team1color": team1color,
        "team2color": team2color
    }
    datasets.append(dataset_item)
    labels = [i for i in range(len(eval_dataset))]
    # acpl_vals = None
    acpl_vals = acpl(game)
    return render(
        request,
        "analysis.html",
        {
            "summary": summary,
            "clas": clas,
            "id": id,
            "worm_labels": labels,
            "worm_data": datasets,
            "worm_data_all": eval_dataset,
            "team1color": team1color,
            "team2color": team2color,
            "kv_store": kv_store,
            "acpl": acpl_vals
        }
    )
