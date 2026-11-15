from math import exp
from statistics import stdev, harmonic_mean
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from bin.models.team import Team
from bin.mongoinserts.load_games import fetch_game
from modules.index.summary import get_summary


def get_analysis(request, clas, id):
    game = fetch_game(clas, id)
    if game is None:
        raise PermissionDenied
    summary = get_summary(game)
    eval_start = game.get("prediction", {"white": 0.5, "black": 0.5, "eval_verbose": "0.0"})
    eval_start["inning"] = 0
    eval_start["id"] = "start"
    eval_start["inning_verbose"] = "Starting Position"
    eval_dataset = [eval_start]
    datasets = []
    team1color = Team(game["team1"]).get("color")
    team2color = Team(game["team2"]).get("color")
    for i0, i in enumerate(game["innings"]):
        for j in i["data"]:
            for k in j:
                l = dict(k["evaluation"])
                l["inning"] = i0
                if i0 == 0:
                    l["inning_verbose"] = "1st Innings, Ball " + k["_id"]
                if i0 == 1:
                    l["inning_verbose"] = "2nd Innings, Ball " + k["_id"]
                l["id"] = k["_id"]
                eval_dataset.append(l)
    if game["winner"] is None or game["winner"] == "":
        color = "#0F0"
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


def acpl(game):
    evals = {
        "white": {
            "name": Team(game["team1"]).name(),
            "inaccuracy": 0,
            "mistake": 0,
            "blunder": 0,
            "acpl": 0,
            "inaccuracy_balls": [],
            "mistake_balls": [],
            "blunder_balls": [],
            "accuracy": 1,
            "accuracypercent": 100,
            "acpl": 0
        },
        "black": {
            "name": Team(game["team2"]).name(),
            "inaccuracy": 0,
            "mistake": 0,
            "blunder": 0,
            "acpl": 0,
            "inaccuracy_balls": [],
            "mistake_balls": [],
            "blunder_balls": [],
            "accuracy": 1,
            "accuracypercent": 100,
            "acpl": 0
        }
    }
    blunder_thresholds = [0.01, 0.05, 0.1]
    blunder_thresholds.sort()
    previous_white = game["prediction"]["white"]
    previous_black = game["prediction"]["black"]
    ball = 0
    white_cpl = 0
    black_cpl = 0
    white_loss = []
    black_loss = []
    white_accuracy = []
    black_accuracy = []
    white_weight = []
    black_weight = []
    for i, e in enumerate(game["innings"]):
        for j in e["data"]:
            for k in j:
                ball_id = {
                    "inning": i,
                    "over": k["over"],
                    "ball_id": k["ball"]
                }
                white_loss.append(max(0, previous_white, k["evaluation"]["white"]))
                black_loss.append(max(0, previous_black, k["evaluation"]["black"]))
                white_accuracy.append(lossByWinPercents(previous_white, k["evaluation"]["white"]))
                black_accuracy.append(lossByWinPercents(previous_black, k["evaluation"]["black"]))
                if previous_white > k["evaluation"]["white"]:
                    white_weight.append(stdev([100 * previous_white, 100 * k["evaluation"]["white"]]))
                else:
                    white_weight.append(0)
                if previous_black > k["evaluation"]["black"]:
                    black_weight.append(stdev([100 * previous_black, 100 * k["evaluation"]["black"]]))
                else:
                    black_weight.append(0)
                if previous_white - k["evaluation"]["white"] >= blunder_thresholds[2]:
                    evals["white"]["blunder"] += 1
                    evals["white"]["blunder_balls"].append(ball_id)
                elif previous_white - k["evaluation"]["white"] >= blunder_thresholds[1]:
                    evals["white"]["mistake"] += 1
                    evals["white"]["mistake_balls"].append(ball_id)
                elif previous_white - k["evaluation"]["white"] >= blunder_thresholds[0]:
                    evals["white"]["inaccuracy"] += 1
                    evals["white"]["inaccuracy_balls"].append(ball_id)
                if previous_black - k["evaluation"]["black"] >= blunder_thresholds[2]:
                    evals["black"]["blunder"] += 1
                    evals["black"]["blunder_balls"].append(ball_id)
                elif previous_black - k["evaluation"]["black"] >= blunder_thresholds[1]:
                    evals["black"]["mistake"] += 1
                    evals["black"]["mistake_balls"].append(ball_id)
                elif previous_black - k["evaluation"]["black"] >= blunder_thresholds[0]:
                    evals["black"]["inaccuracy"] += 1
                    evals["black"]["inaccuracy_balls"].append(ball_id)
                previous_white = k["evaluation"]["white"]
                previous_black = k["evaluation"]["black"]
                if k["legal_delivery"]:
                    ball += 1
                    if k["dismissed_batter"] is not None and k["dismissed_batter"] != "" and k["score_int"] < 1:
                        if e["batting_team"] == game["team1"]:
                            white_cpl += 7
                        elif e["batting_team"] == game["team2"]:
                            black_cpl += 7
                    else:
                        if e["batting_team"] == game["team1"]:
                            white_cpl += max(0, 6 - k["score_int"])
                            black_cpl += 1 + k["score_int"]
                        elif e["batting_team"] == game["team2"]:
                            black_cpl += max(0, 6 - k["score_int"])
                            white_cpl += 1 + k["score_int"]
    # Max ACPL = 2000.
    if ball > 0:
        # evals["white"]["acpl"] = mean(white_loss) * 10000
        # evals["black"]["acpl"] = mean(black_loss) * 10000
        evals["white"]["acpl"] = (white_cpl * 2000) / (ball * 7)
        evals["black"]["acpl"] = (black_cpl * 2000) / (ball * 7)
    white_acc_list = []
    black_acc_list = []
    if sum(white_weight) > 0:
        for i in range(len(white_accuracy)):
            white_acc_list.append(white_accuracy[i] * white_weight[i] / sum(white_weight))
    else:
        white_acc_list = [i / len(white_accuracy) for i in white_accuracy]
    if sum(black_weight) > 0:
        for i in range(len(black_accuracy)):
            black_acc_list.append(black_accuracy[i] * black_weight[i] / sum(black_weight))
    else:
        black_acc_list = [i / len(black_accuracy) for i in black_accuracy]
    white_hmean = max(0, harmonic_mean([i + (10 ** -7) for i in white_accuracy]) - (10 ** -7))
    black_hmean = max(0, harmonic_mean([i + (10 ** -7) for i in black_accuracy]) - (10 ** -7))
    evals["white"]["accuracy"] = (sum(white_acc_list) + white_hmean) * (2000 - evals["white"]["acpl"]) / 4000
    evals["black"]["accuracy"] = (sum(black_acc_list) + black_hmean) * (2000 - evals["black"]["acpl"]) / 4000
    evals["white"]["accuracypercent"] = evals["white"]["accuracy"] * 100
    evals["black"]["accuracypercent"] = evals["black"]["accuracy"] * 100
    evals["w1"] = white_hmean
    evals["b1"] = black_hmean
    # evals["w"] = white_acc_list
    # evals["b"] = black_acc_list
    return evals


def lossByWinPercents(before, after):
    if after >= before:
        return 1
    winDiff = before - after
    factor = 103.1668 * exp(-4 * winDiff) - 3.1668
    if factor >= 100:
        return 1
    if factor <= 0:
        return 0
    return factor / 100

