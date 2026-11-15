import csv
import io
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
"""
Input: Match json. isTest: is it a test match or not
"""

MODEL = "google/gemma-4-e2b"
KEY = "sk-proj-dummy-key"
ENDPOINT = "http://10.0.2.2:1234/v1"
SYSTEM = "system" # human if using Mistral7b


def encode_name(given_name: str):
    """
    Example: {{ A1.name }} -> ::A1_name::
    """
    return given_name.replace("{{ ", "::").replace(".name }}", "_name::")


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


def test():
    name_encoder = {}
    name_decoder = {}
    with open("final.json", "r") as file:
        game = json.load(file)
        if "nomination" not in game[0].keys():
            print("Missing Player Sheet, exiting")
            return
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
                        "bowling_team": innings["bowling_team"],
                        "batting_team": innings["batting_team"],
                        "over_number": ball["over"],
                        "ball_number": ball["ball"],
                        "bowler_name": str("::" + ball["bowler"] + "_name::"),
                        "batter_name": str("::" + ball["batter"] + "_name::"),
                        "commentary": new_commentary
                    }
                    result_content = commentary_rewrite(ball_metadata)
                    result = result_prefix + result_content
                    for key, value in name_decoder.items():
                        result = result.replace(key, value)
                    print(result)
                    ball["commentary"] = result
                    # return # safety valve
    with open("final1.json", "w+", encoding="utf-8") as file:
        json.dump(game, file, indent=4)


def test1():
    with open("final1.json", "r", encoding="utf-8") as file:
        game = json.load(file)
    with open("final1.json", "w+", encoding="utf-8") as file:
        json.dump(game, file, indent=4)



def commentary_rewrite(ball_data: dict):
    # Over by over

    commentator_model = ChatOpenAI(
        model=MODEL,
        openai_api_key=KEY,
        openai_api_base=ENDPOINT,
        temperature=0.75
    )

    commentator_prompt = ChatPromptTemplate.from_messages([
        (
            SYSTEM, (
                "You are an energetic, dramatic cricket commentator, commenting in Google Search style commentary."
                " Your task is to take the ball commentary provided and"
                " rewrite it into a Google Search style ball commentary."
                "\n\n"
                "CRITICAL HARD CODES:\n"
                "1. Keep the commentary to a single paragraph.\n"
                "2. Use the term batter instead of batsman.\n"
                "NOTE: All bowlers are sling pace bowlers. All dismissed batters tried to hit sixes and failed."
            )
        ),
        (
            "human", "Data: {ball_data}."
        )
    ])

    parser = StrOutputParser()

    chain = commentator_prompt | commentator_model | parser

    result = chain.invoke({
        "ball_data": ball_data
    })

    return result


def summarize_innings_prompt(innings_csv: str):

    extraction_model = ChatOpenAI(
        model=MODEL,
        openai_api_key=KEY,
        openai_api_base=ENDPOINT,
        temperature=0.0
    )

    commentator_model = ChatOpenAI(
        model=MODEL,
        openai_api_key=KEY,
        openai_api_base=ENDPOINT,
        temperature=0.75
    )

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
                "\n\n"
                "CRITICAL HARD CODES:\n"
                "1. You must use vivid adjectives, intense sports metaphors,"
                " and dramatic descriptions.\n"
                "2. You must ONLY use the exact names and numbers provided in"
                " the input text.\n"
                "3. You are strictly forbidden from altering any numerical"
                " statistics or introducing new events."
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


test2()
