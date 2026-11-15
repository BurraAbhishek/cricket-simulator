def tokenify_name(given_name: str):
    """
    Example: A1 -> ::A1_name::
    """
    return str("::" + given_name + "_name::")


def encode_name(given_name: str):
    """
    Example: {{ A1.name }} -> ::A1_name::
    """
    return given_name.replace("{{ ", "::").replace(".name }}", "_name::").replace(".NAME }}", "_NAME::")


def get_fall_of_wicket(fow: dict):
    bowler_name = tokenify_name(fow["bowler"])
    fielder_name = tokenify_name(fow["fielder"])
    if fow["mode"] == "b":
        return "b " + bowler_name
    elif fow["mode"] == "c":
        if fow["bowler"] == fow["fielder"]:
            return "c & b " + bowler_name
        else:
            return "c " + fielder_name + " b " + bowler_name
    elif fow["mode"] == "lbw":
        return "lbw b " + bowler_name
    elif fow["mode"] == "st":
        return "st " + fielder_name + " b " + bowler_name
    return "b " + bowler_name


def parse_batters(bat_stats: list):
    s = "Batting (All):\n"
    for bat in bat_stats:
        s += tokenify_name(bat["_id"])
        s += " "
        s += str(bat["runs"])
        if not bat["dismissed"]:
            s += "*"
        s += " ("
        s += str(bat["balls"])
        s += ") ["
        s += str(bat["scoring"][4])
        s += "x4, "
        s += str(bat["scoring"][6])
        s += "x6] - "
        if bat["dismissed"]:
            s += get_fall_of_wicket(bat["dismissal"])
        else:
            s += "not out"
        s += "\n"
    return s


def parse_bowlers(bowl_stats: list):
    s = "Bowling (All):\n"
    for bowl in bowl_stats:
        s += tokenify_name(bowl["_id"])
        s += " "
        s += str(bowl["balls"] // 6)
        s += "."
        s += str(bowl["balls"] % 6)
        s += "-"
        s += str(bowl["maidens"])
        s += "-"
        s += str(bowl["runs"])
        s += "-"
        s += str(bowl["wickets"])
        s += "\n"
    return s


def parse_partnerships(partnerships: list):
    s = "Partnerships (All):\n"
    for i, e in enumerate(partnerships, start=1):
        s += tokenify_name(e["p1"])
        s += " & "
        s += tokenify_name(e["p2"])
        s += " "
        s += str(e["p1_runs"] + e["p2_runs"] + e["extra"])
        s += " runs ("
        s += str(e["p1_balls"] + e["p2_balls"])
        s += " balls) for the "
        s += str(i)
        s += "st" if i == 1 else ("nd" if i == 2 else ("rd" if i == 3 else "th"))
        s += " wicket\n"
    return s


def format_score(score, wickets, declared=False, max_wickets=10):
    settings = {
        "format": "{score}/{wickets}{declaration}",
        "declaration": " dec",
        "show_last_wicket": " all out"
    }
    if wickets >= max_wickets:
        settings["format"] = settings["format"].replace(
            "/{wickets}{declaration}",
            settings["show_last_wicket"]
        )
    declaration = ""
    if declared:
        declaration = settings["declaration"]
    return str(settings["format"]).format(
        score=score,
        wickets=wickets,
        declaration=declaration
        )


def parse_total(innings: dict):
    s = "Total: "
    s += format_score(innings["score"], innings["wickets"], innings.get("declared", False))
    s += " ("
    s += str(innings["balls"] // 6)
    s += "."
    s += str(innings["balls"] % 6)
    s += " overs) | RR: "
    try:
        s += str(int(innings["score"] * 600 / innings["balls"]) / 100)
    except ZeroDivisionError:
        s += "-"
    s += " | Extras: "
    s += str(innings["extras"]["total"])
    s += "\n"
    return s


def parse_commentary(innings_data: list[list[dict]]):
    s = ""
    for over in innings_data:
        for ball in over:
            s += str(ball["over"] - 1)
            s += "."
            s += str(ball["ball"])
            s += " "
            s += encode_name(ball["commentary"])
            s += "\n"
    return s
