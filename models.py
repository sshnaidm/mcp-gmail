"""This module initializes and configures the language models."""

from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.0,
    top_p=0.0,
)


# ollama based model
ollama = ChatOllama(model="qwen3:14b", temperature=0.0, top_p=0.0, num_ctx=40960)
