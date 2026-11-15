import csv
import io
import json
from cloud_model import get_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
"""
Input: Match json. isTest: is it a test match or not
"""

MODEL = "google/gemma-4-e2b"
KEY = "sk-proj-dummy-key"
ENDPOINT = "http://10.0.2.2:1234/v1"
SYSTEM = "system" # human if using Mistral7b

IS_TEST = False


def tokenify_name(given_name: str):
    """
    Example: A1 -> ::A1_name::
    """
    return str("::" + given_name + "_name::")


def encode_name(given_name: str):
    """
    Example: {{ A1.name }} -> ::A1_name::
    """
    return given_name.replace("{{ ", "::").replace(".name }}", "_name::")


def unicode_punctuation_translate(text: str) -> str:
    map = {
        "\u2018": "'", # left single quote
        "\u2019": "'", # right single quote
        "\u201c": '"', # left double quote
        "\u201d": '"', # right double quote
        "\u2013": "-", # En-dash
        "\u2014": "—", # Em-dash
        "\u2026": "...", # Horizontal ellipsis
        "\u00a0": " ", # Space
        "\u2010": "-", # Hyphen
        "\u2011": "-", # Non-breaking hyphen
    }
    table = str.maketrans(map)
    return text.translate(table)


def result_text(outcome: str, batters: dict|None=None, dismissed_batter: str|None=None):
    if outcome == "0":
        return "NO RUN."
    if outcome == "4":
        return "FOUR! "
    if outcome == "6":
        return "SIX! "
    if outcome == "1+w":
        return "OUT! RUN OUT!"
    if outcome == "W":
        for b in batters:
            if b["_id"] == dismissed_batter:
                if b["dismissal"]["mode"] == "lbw":
                    return "OUT LBW!"
        return "OUT!"
    return ""


def get_innings_ordinals(game):
    names = []
    orders = {
        game["innings"][0]["batting_team"]: 0,
        game["innings"][0]["bowling_team"]: 0
    }
    for inning in game["innings"]:
        orders[inning["batting_team"]] += 1
        batting_team_inning_order = orders[inning["batting_team"]]
        if batting_team_inning_order == 1:
            names.append(tokenify_name(inning["batting_team"]) + "1st Innings")
        elif batting_team_inning_order == 2:
            names.append(tokenify_name(inning["batting_team"]) + "2nd Innings")
    return names


def test():
    name_encoder = {}
    name_decoder = {}
    additional_context = {
        "format": "",
        "overs": 20,
        "completed_innings": [],
        "chasing": False,
        "target": None,
        "inning_name": "",
        "toss": "",
        "captains": {}
    }
    data = []
    inning_names = ["1st Innings", "2nd Innings"]
    inning_number = 0
    with open("final.json", "r") as file:
        game = json.load(file)
        if "nomination" not in game[0].keys():
            print("Missing Player Sheet, exiting")
            return
        for i in game[0]["nomination"].keys():
            additional_context["captains"][i] = game[0]["nomination"][i]["captain"]
        if game[0]["isTest"] is True:
            additional_context["format"] = "5-Day Test"
            inning_names = get_innings_ordinals(game[0])
        else:
            if game[0]["overs"] == 20:
                additional_context["overs"] = 20
                additional_context["format"] = "T20"
            elif game[0]["overs"] == 50:
                additional_context["overs"] = 50
                additional_context["format"] = "50 Overs ODI"
            else:
                additional_context["overs"] = game[0]["overs"]
                additional_context["format"] = "Limited-Overs"
        for team in game[0]["nomination"].values():
            for player in team["default"]: # The starting 11
                d_name = str("{{ " + player + ".name }}")
                e_name = encode_name(d_name)
                name_encoder[d_name] = e_name
                name_decoder[e_name] = d_name
                name_encoder[d_name.upper()] = e_name.upper()
                name_decoder[e_name.upper()] = d_name.upper()
        for team in game[0]["nomination"].keys():
                d_name = str("{{ " + team + ".name }}")
                e_name = encode_name(d_name)
                name_encoder[d_name] = e_name
                name_decoder[e_name] = d_name
                name_encoder[d_name.upper()] = e_name.upper()
                name_decoder[e_name.upper()] = d_name.upper()
        for innings in game[0]["innings"]:
            additional_context["inning_name"] = inning_names[inning_number]
            print(inning_names[inning_number])
            for over in innings["data"]:
                for ball in over:
                    new_commentary = str(ball["commentary"])
                    for key, value in name_encoder.items():
                        new_commentary = new_commentary.replace(key, value)
                    result_prefix = str(
                        "{{ "
                        + ball["bowler"]
                        + ".name }}"
                        + " to "
                        + "{{ "
                        + ball["batter"]
                        + ".name }}"
                        + ", "
                        + result_text(ball["score"], innings["batter_stats"], ball["dismissed_batter"])
                        + " "
                    )
                    ball_metadata = {
                        "bowling_team": tokenify_name(innings["bowling_team"]),
                        "batting_team": tokenify_name(innings["batting_team"]),
                        "over_number": ball["over"],
                        "ball_number": ball["ball"],
                        "bowler_name": tokenify_name(ball["bowler"]),
                        "batter_name": tokenify_name(ball["batter"]),
                        "commentary": new_commentary
                    }
                    # result_content = new_commentary
                    result_content = commentary_rewrite(ball_metadata, additional_context)
                    result = str(result_content)
                    data.append(result)
                    for key, value in name_decoder.items():
                        result = result.replace(key, value)
                    print(result)
                    ball["commentary"] = result
                    # return # safety valve
            additional_context["completed_innings"].append({
                "name": inning_names[inning_number],
                "runs": innings.get("score", 0),
                "wickets": innings.get("wickets", 0),
                "balls": innings.get("balls", 0),
                "declared": innings.get("declared", False)
            })
            inning_number += 1
    with open("final1.json", "w+", encoding="utf-8") as file:
        json.dump(game, file, indent=4)


def test1():
    with open("final1.json", "r", encoding="utf-8") as file:
        game = json.load(file)
    with open("final1.json", "w+", encoding="utf-8") as file:
        json.dump(game, file, indent=4)


def completed_inning_summary(completed_innings: list):
    if len(completed_innings) == 0:
        return ""
    s = "\n\nCompleted Innings:\n"
    for i in completed_innings:
        s += i["name"] + ": "  + str(i["runs"])
        if i["wickets"] >= 10:
            s += " all out"
        else:
            s += "/" + str(i["wickets"])
            if i["declared"]:
                s += " dec"
        s += " ("
        s += str(i["balls"])
        s += " balls)\n"
    return s


def captain_summary(captains):
    s = ""
    for i in captains.keys():
        s += tokenify_name(i)
        s += " - "
        s += tokenify_name(captains[i])
        s += "\n"
    return s


def commentary_rewrite(ball_data: dict, additional_context: dict={}):
    # TODO: Over by over

    commentator_model = get_model()

    commentator_prompt = ChatPromptTemplate.from_messages([
        (
            SYSTEM, (
                "You are an energetic, dramatic cricket commentator, commenting in Google Search style commentary."
                " Your task is to take the ball commentary provided and"
                " rewrite it into a Google Search style ball commentary."
                "\n\n"
                "Match Format: {format}\nCurrent Innings: {curr_inning}{completed_innings}"
                "\n\n"
                "Captains:\n{captains}"
                "\n\n"
                "CRITICAL HARD CODES:\n"
                "1. Keep the commentary to a single paragraph.\n"
                "2. Use the term batter instead of batsman.\n"
                "3. Leave the first part (over, bowler, batter, outcome) as is."
            )
        ),
        (
            "human", "Data: {ball_data}."
        )
    ])

    parser = StrOutputParser()

    chain = commentator_prompt | commentator_model | parser

    result = chain.invoke({
        "ball_data": ball_data,
        "format": additional_context.get("format", "Limited-Overs"),
        "curr_inning": additional_context.get("inning_name", "1st Innings"),
        "completed_innings": completed_inning_summary(additional_context.get("completed_innings", [])),
        "captains": captain_summary(additional_context.get("captains", {}))
    })

    result = unicode_punctuation_translate(result)

    return result


def summarize_innings_prompt(innings_csv: str):

    extraction_model = get_model()

    commentator_model = get_model()

    extraction_prompt = ChatPromptTemplate.from_messages([
        (
            SYSTEM, (
                "You are a literal data verification script. Your only job is to compile a raw factual summary of the innings.\n"
                "Columns present in the given dataset:\n"
                "- over: The over being played. For example, over=1 refers to the first over.\n"
                "- ball: The ball being played. For example, ball=4 refers to the 4th ball of the over.\n"
                "- bowler: The ID of the bowler.\n"
                "- batter: The ID of the batter facing the delivery.\n"
                "- score: The outcome of the ball. Either of 0-6, W (dismissal), wd (wide), nb (no-ball).\n"
                "- dismissed batter: The dismissed batter. If left blank, no batter was dismissed in that ball."
            )
        ),
        (
            "human", "Generate a factual summary from this data: {dataset_csv}"
        )
    ])

    commentator_prompt = ChatPromptTemplate.from_messages([
        (
            SYSTEM, (
                "You are an energetic, dramatic cricket radio commentator."
                " Your task is to take the boring factual summary provided and"
                " rewrite it into a thrilling end-of-innings broadcast wrap-up"
                " commentary."
            )
        ),
        (
            "human", "Factual Anchor (Do not alter numbers):\n{factual_anchor}"
        )
    ])

    parser = StrOutputParser()

    chain1 = extraction_prompt | extraction_model | parser

    result1 = chain1.invoke({
        "dataset_csv": innings_csv
    })

    print(result1)
    print("Summarization complete, rewriting")

    chain2 = commentator_prompt | commentator_model | parser

    result = chain2.invoke({
        "factual_anchor": result1
    })

    return result

def innings_to_csv(ball_data: list[list[dict]]):
    output = io.StringIO()
    headers = ['over', 'ball', 'bowler', 'batter', 'outcome', 'dismissed batter']
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(headers)
    for over in ball_data:
        for ball in over:
            writer.writerow([
                ball.get("over"),
                ball.get("ball"),
                "_" + ball.get("bowler") + "_",
                "_" + ball.get("batter") + "_",
                ball.get("score"),
                ball.get("dismissed_batter")
            ])
    return output.getvalue()


def test2():
    with open("final.json", "r") as file:
        game = json.load(file)
    c = innings_to_csv(game[0]["innings"][1]["data"])
    s = summarize_innings_prompt(c)
    print(s)


test()
