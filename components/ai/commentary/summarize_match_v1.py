import csv
import io
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
"""
Input: Match json. isTest: is it a test match or not
"""

MODEL = "llama"
KEY = "sk-proj-dummy-key"
ENDPOINT = "http://10.0.2.2:1234/v1"
SYSTEM = "system" # human if using Mistral7b


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


def test():
    with open("final.json", "r") as file:
        game = json.load(file)
    c = innings_to_csv(game[0]["innings"][0]["data"])
    s = summarize_innings_prompt(c)
    print(s)


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


test()
