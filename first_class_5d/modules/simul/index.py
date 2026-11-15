import json
from urllib.parse import urlencode
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.staticfiles import finders
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.simul.forms.games import GameSelection
from modules.simul.models.structure import Simul
from modules.simul.common.timer import time_to_verbose


USE_CLOCK = True
CLOCK_INTERVAL = 40


def make_simul(new_data):
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "simul.json"
    f = open(new_location, "w+")
    f.write('{}')
    f.close()
    with open(new_location, "w+") as f:
        json.dump(new_data, f, indent=4)


def get_simul():
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "simul.json"
    try:
        f = open(new_location)
        f.close()
    except FileNotFoundError:
        return HttpResponseRedirect("/simul/new")
    f = open(new_location, "r")
    x = json.load(f)
    f.close()
    return x


def render_simul(request):
    evalbar_width = 80
    simul_data = get_simul()
    try:
        if USE_CLOCK:
            simul = Simul(simul_data["games"], simul_data["clock"])
            clock = simul_data["clock"]
            stop_condition = bool(clock >= simul.max_clock)
        else:
            simul = Simul(simul_data["games"], simul_data["curr_position"])
            clock = simul_data["curr_position"]
            stop_condition = True
    except KeyError:
        return HttpResponseRedirect("/simul/new")
    playing = False
    evaluation = True
    if request is not None:
        playing = request.GET.get("playing", False)
        evaluation = request.GET.get("evaluation", True)
        if playing == "False" or playing == "false":
            playing = False
        if evaluation == "False" or evaluation == "false":
            evaluation = False
    params = fetch_params(request)
    simul_api_data = simul.render_data(playing)
    for i in simul_api_data:
        white_own = i["eval"]["white"] + (0.5 * i["eval"]["draw"])
        black_own = i["eval"]["black"] + (0.5 * i["eval"]["draw"])
        i["eval"]["white_width"] = str(white_own * evalbar_width) + "vw"
        i["eval"]["black_width"] = str(black_own * evalbar_width) + "vw"
    interval = TOURNAMENT_SETTINGS.get("simul_interval", 0)
    automate = interval > 0 and not stop_condition
    return render(
        request,
        "simul_homepage.html",
        {
            "data": simul_api_data,
            "clock": time_to_verbose(clock),
            "hide_evaluation": not evaluation,
            "params": params,
            "simul_automate": automate,
            "simul_interval": interval
        }
    )


def init_simul(request):
    if request.method == "POST":
        form = GameSelection(request.POST)
        if form.is_valid():
            games = []
            for i in form.cleaned_data["games"]:
                games.append(json.loads(i))
            simul = {
                "games": games,
                "curr_position": 0,
                "clock": 0
            }
            make_simul(simul)
            return HttpResponseRedirect("/simul")
    return render(
        request,
        "simul_form.html",
        {
            "title": "New Simul",
            "form": GameSelection(),
        }
    )


def simul_next(request):
    simul_data = get_simul()
    params = fetch_params(request)
    if USE_CLOCK:
        try:
            simul = Simul(simul_data["games"], simul_data["clock"])
        except KeyError:
            return HttpResponseRedirect("/simul/new")
        if simul_data["clock"] < simul.max_clock:
            simul_data["clock"] += CLOCK_INTERVAL
        else:
            simul_data["clock"] = simul.max_clock
    else:
        try:
            simul = Simul(simul_data["games"], simul_data["curr_position"])
        except KeyError:
            return HttpResponseRedirect("/simul/new")
        if simul_data["curr_position"] < simul.max_position:
            simul_data["curr_position"] += 1
        else:
            simul_data["curr_position"] = simul.max_position
    make_simul(simul_data)
    return HttpResponseRedirect("/simul" + params)


def simul_previous(request):
    simul_data = get_simul()
    params = fetch_params(request)
    if USE_CLOCK:
        if simul_data["clock"] > 0:
            simul_data["clock"] -= CLOCK_INTERVAL
        if simul_data["clock"] < 0:
            simul_data["clock"] = 0
    else:
        if simul_data["curr_position"] > 0:
            simul_data["curr_position"] -= 1
    make_simul(simul_data)
    return HttpResponseRedirect("/simul" + params)


def fetch_params(request):
    if request is None:
        return ""
    params = ""
    if (
        request.GET.get("playing") is not None 
        or request.GET.get("evaluation") is not None
    ):
        params = "?" + urlencode(request.GET)
    return params
