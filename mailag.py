#!/usr/bin/env python3

import datetime
import gradio as gr
from gmail import get_emails

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import PromptTemplate

from models import gemini, ollama


# pylint: disable=unused-import
# flake8: noqa: F401
llm = ollama  # or gemini
# llm = gemini  # Uncomment to use Gemini model

print("LLM initialized:", llm)


AI_SYSTEM_PROMPT = """
You are helpful AI assistant that helps with managing mails, docs, calendar, and other tasks.
You are able to use tools to answer questions and perform actions.
You have access to the following tools:
1. **gmail_search**: Search for emails in Gmail.
    Input: {"query": "in:inbox subject:meeting"}
    Input: {"query": "from:user in:inbox", count: 50, page: 1, full_body: True}
    Input: {"query": "to:me", count: 50}
    Output: The list of emails matching the query with snippets or full text.
2. **get_todays_date**: Get today's date in YYYY-MM-DD format.
    Input: {}
    Output: The current date in YYYY-MM-DD format.
"""


def gmail_search_tool(query: str, count: int = 50, page: int = 1, full_body: bool = False) -> str:
    """
    Search for emails in Gmail based on the provided query.

    Args:
        query (str): The search query to filter emails.

    Returns:
        str: A formatted string containing the search results.
    """
    if not isinstance(count, int):
        try:
            count = int(count)
        except ValueError:
            raise Exception("count must be an integer.")
    if not isinstance(page, int):
        try:
            page = int(page)
        except ValueError:
            raise Exception("page must be an integer.")
    if not isinstance(full_body, bool):
        try:
            full_body = bool(full_body)
        except ValueError:
            raise Exception("full_body must be a boolean.")

    # Call the get_emails function with the provided query
    return get_emails(gmail_query=query, count=count, page=page, full_body=full_body)


tools = [
    Tool(
        name="gmail_search",
        func=gmail_search_tool,
        description=(
            "Search for emails in Gmail."
            "Input should be a JSON object with a 'query' field containing the search query."
            "Output will be a list of emails matching the query with snippets or full text."
        ),
    ),
    Tool(
        name="get_todays_date",
        func=lambda x: datetime.datetime.now().strftime("%Y-%m-%d"),
        description=(
            "Get today's date in YYYY-MM-DD format."
            "This tool does not require any input and returns the current date."
        ),
    ),
]


# Use ReAct agent instead of OpenAI functions agent
# prompt = hub.pull("hwchase17/react")

prompt = PromptTemplate.from_template(
    """
You are a helpful email assistant that can search Gmail and provide summaries.

You have access to the following tools:
{tools}

Tool names: {tool_names}

When answering questions, follow this format EXACTLY:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: When you have enough information to answer the question, you MUST end with:
Thought: I now know the final answer
Final Answer: [your complete answer here]

Question: {input}
{agent_scratchpad}
"""
)

# Create the ReAct agent (compatible with Gemini)
agent = create_react_agent(llm, tools, prompt)

# agent = create_openai_functions_agent(llm, tools, prompt)
# Create the Agent Executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=4,  # Prevent infinite loops
    max_execution_time=180,  # Limit execution time to 180 seconds
    # early_stopping_method="generate",  # Changed to "generate" for better final answer handling
    early_stopping_method="force",
    return_intermediate_steps=True,  # This helps with debugging
)


def chat(message, history):
    """
    Alternative implementation using invoke instead of stream
    """
    try:
        start = datetime.datetime.now()
        print(f"DEBUG: Starting calculation at {start}")
        # Convert gradio history to langchain format
        chat_history = []
        for h in history:
            if h["role"] == "user":
                chat_history.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                chat_history.append(AIMessage(content=h["content"]))

        # Prepare input for the agent
        agent_input = {"input": message, "chat_history": chat_history}

        # Get the response directly
        response = agent_executor.invoke(agent_input)

        # Extract the final output
        if isinstance(response, dict) and "output" in response:
            final_answer = response["output"]
        else:
            final_answer = str(response)
        end = datetime.datetime.now()
        total = round((end - start).total_seconds(), 2)
        yield final_answer + f"\n\nTotal time: {total} seconds"

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(f"DEBUG: Exception occurred: {e}")
        yield error_msg


with gr.Blocks() as demo:

    gr.ChatInterface(
        chat,
        type="messages",
        save_history=True,
    )

demo.launch(server_port=5007)
