"""This module provides the language models."""

import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", temperature=0.0, top_p=0.0, google_api_key=os.getenv("GEMINI_API_KEY")
)


# ollama based model
ollama = ChatOllama(model="qwen3:14b", temperature=0.0, top_p=0.0, num_ctx=40960)
