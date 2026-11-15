from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from bin.models.llms import BaseCricketLLMOptions
from modules.index.match_toppers import get_inning_toppers_bat, get_inning_toppers_bowl


def get_potm_data(game: dict):
    data = []
    target_inning = 1
    if game["isTest"]:
        data.append("Format: Test Match")
        target_inning = 3
    else:
        data.append(
            "Format: "
            + str(game["overs"])
            + " overs"
        )
    if game["winner"] is None or game["winner"] == "":
        data.append("Result: " + game["margin"])
    else:
        data.append(
            "Result: "
            + game["winner"]
            + " won by "
            + game["margin"]
        )
    data.append("")
    follow_on = game.get("follow_on", False)
    for iterator, innings in enumerate(game["innings"]):
        if iterator == 0:
            innings_id = "1st"
        elif iterator == 1:
            innings_id = "2nd"
        elif iterator == 2:
            innings_id = "3rd"
        else:
            innings_id = str(iterator + 1) + "th"
        innings_name = str(
            "["
            + innings_id
            + " Innings: "
            + innings["batting_team"]
            + " Batting"
            + str(" (Following on)" if follow_on and iterator == 2 else "")
            + "]"
        )
        data.append(innings_name)
        if iterator == target_inning:
            data.append(
                "- Target: "
                + str(game["target"])
            )
        score_total = str(
            "- Total: "
            + str(innings["score"])
            + str(" all out" if innings["wickets"] >= 10 else "/" + str(innings["wickets"]))
            + str(" dec (" if innings.get("declared", False) else " (")
            + str(innings["balls"])
            + str(" ball)" if innings["balls"] == 1 else " balls)")
        )
        data.append(score_total)
        bat_toppers = get_inning_toppers_bat(game, iterator)[:2]
        for i, e in enumerate(bat_toppers, start=1):
            top_str = str(
                "- Top Batter "
                + str(i)
                + ": "
                + e.id()
                + " - "
                + str(e.runs)
                + str(" (" if e.dismissed else "* (")
                + str(e.balls)
                + str(" ball)" if e.balls == 1 else " balls)")
            )
            data.append(top_str)
        bowl_toppers = get_inning_toppers_bowl(game, iterator)[:2]
        for i, e in enumerate(bowl_toppers, start=1):
            top_str = str(
                "- Top "
                + innings["bowling_team"]
                + " Bowler "
                + str(i)
                + ": "
                + e.id()
                + " - "
                + str(e.wickets)
                + "/"
                + str(e.runs)
                + " ("
                + str(e.balls)
                + str(" ball)" if e.balls == 1 else " balls)")
            )
            data.append(top_str)
        data.append("")
    return data


def get_potm(data_list: list[str]):
    llm_options = BaseCricketLLMOptions()
    llm = ChatOpenAI(
        model=llm_options.model,
        openai_api_key=llm_options.api_key,
        openai_api_base=llm_options.endpoint,
        temperature=0.15
    )
    prompt_template = ChatPromptTemplate.from_messages([
        (llm_options.system_identifier, (
            "You are the official cricket match adjudicator.\n"
            "Your sole job is to review the provided match summary"
            " and select the Player of the Match.\n\n"
            "CRITICAL RULES:\n"
            "1. Calculate the dominance score of each listed performance based on how it changed the match.\n"
            "2. Whichever player has the highest dominance score is Player of the Match.\n"
            "3. Bowlers figures are expressed in wickets/runs (balls).\n"
            "4. Assume all given data to be true.\n"
            "5. For each innings, only the top batting and bowling performances are listed.\n"
            "6. Select precisely one Player of the Match. It should be a player, not a team."
        )),
        ("user", "Here is the match summary:\n{flat_scorecard}")
    ])
    output_parser = StrOutputParser()
    chain = prompt_template | llm | output_parser
    response = chain.invoke({
        "flat_scorecard": "\n".join(data_list)
    })
    return response
