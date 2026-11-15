from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI


@lru_cache(maxsize=4)
def get_model() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        project="cricket-simulator-v1",
        location="global",
        vertexai=True
    )