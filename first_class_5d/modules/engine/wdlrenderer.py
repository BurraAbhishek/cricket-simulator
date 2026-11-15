from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from bin.models.team import Team
from bin.mongoinserts.load_games import fetch_game
from modules.index.summary import get_summary
from modules.engine.acpl import acpl


def get_wdl(request, clas, id):
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
    team1color = "inherit"
    team2color = "inherit"
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
    white_item = {
        "type": "bar",
        "fill": True,
        "lineTension": 0,
        "backgroundColor": "#aaa",
        "borderColor": "#aaa",
        "pointRadius": 0,
        "barPercentage": 1,
        "categoryPercentage": 1,
        "data": [i["white"] for i in eval_dataset]
    }
    draw_item = {
        "type": "bar",
        "fill": True,
        "lineTension": 0,
        "backgroundColor": "gold",
        "borderColor": "gold",
        "pointRadius": 0,
        "barPercentage": 1,
        "categoryPercentage": 1,
        "data": [i["draw"] for i in eval_dataset]
    }
    black_item = {
        "type": "bar",
        "fill": True,
        "lineTension": 0,
        "backgroundColor": "#111",
        "borderColor": "#111",
        "pointRadius": 0,
        "barPercentage": 1,
        "categoryPercentage": 1,
        "data": [i["black"] for i in eval_dataset]
    }
    kv_store = {
        "team1name": Team(game["team1"]).name(),
        "team2name": Team(game["team2"]).name(),
        "team1color": team1color,
        "team2color": team2color
    }
    datasets.append(white_item)
    datasets.append(draw_item)
    datasets.append(black_item)
    labels = [i for i in range(len(eval_dataset))]
    # acpl_vals = None
    acpl_vals = acpl(game)
    return render(
        request,
        "wdl.html",
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
