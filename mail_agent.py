#!/usr/bin/env python3
"""This module provides a Gradio chat interface for an AI email assistant."""
import datetime

try:
    from logging_config import setup_logging

    logger = setup_logging(__name__)
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

import gradio as gr
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate

import mcp_gmail

# pylint: disable=unused-import
from models import gemini, ollama

logger.info("mail_agent module initialized")


# flake8: noqa: F401
llm = gemini  # ollama  # or gemini, or any other model you want to use
# llm = gemini  # Uncomment to use Gemini model

print("LLM initialized:", llm)

AI_SYSTEM_PROMPT = """
You are helpful AI assistant that helps with managing mails, docs, calendar, and other tasks.
You are able to use tools to answer questions and perform actions.
You have access to the following tools:
1. **list_tools**: List the available tools.
    Input: {}
    Output: The list of available tools.
2. **gmail_search**: Search for emails in Gmail.
    Input: {"query": "in:inbox subject:meeting"}
    Input: {"query": "from:user in:inbox", count: 50, page: 1, full_body: True}
    Input: {"query": "to:me", count: 50}
    Output: The list of emails matching the query with snippets or full text.
3. **get_todays_date**: Get today's date in YYYY-MM-DD format.
    Input: {}
    Output: The current date in YYYY-MM-DD format.
"""

# Access the underlying functions from the FunctionTool objects
# The @mcp.tool decorator wraps functions in FunctionTool objects
# We need to access the actual function using the .fn attribute
tools = [
    Tool(name="list_tools", func=mcp_gmail.list_tools.fn, description=mcp_gmail.list_tools.description),
    Tool(name="get_emails_tool", func=mcp_gmail.get_emails_tool.fn, description=mcp_gmail.get_emails_tool.description),
    Tool(name="send_email_tool", func=mcp_gmail.send_email_tool.fn, description=mcp_gmail.send_email_tool.description),
    Tool(name="get_today_date", func=mcp_gmail.get_today_date.fn, description=mcp_gmail.get_today_date.description),
]

# Use ReAct agent instead of OpenAI functions agent
# prompt = hub.pull("hwchase17/react")

prompt = PromptTemplate.from_template(
    """
You are a helpful email assistant that can search Gmail and provide summaries.

You have access to the following tools:
{tools}

Tool names: {tool_names}

Previous conversation history:
{chat_history}

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

Remember the context from our previous conversation when answering.

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
    Chat function for the agent executor.
    Args:
        message (str): The message to send to the agent.
        history (list): The history of the conversation.
    Returns:
        str: The response from the agent.
    """
    try:
        start = datetime.datetime.now()
        print(f"DEBUG: Starting calculation at {start}")
        print(f"DEBUG: Received history with {len(history) if history else 0} messages")

        # Convert gradio history to a formatted string for the prompt
        chat_history_str = ""
        if history:
            for h in history:
                if h["role"] == "user":
                    chat_history_str += f"Human: {h['content']}\n"
                elif h["role"] == "assistant":
                    chat_history_str += f"Assistant: {h['content']}\n"
            chat_history_str = chat_history_str.strip()
            print(f"DEBUG: Formatted chat history:\n{chat_history_str[:200]}...")  # Show first 200 chars
        else:
            chat_history_str = "No previous conversation."
            print("DEBUG: No previous conversation history")

        # Prepare input for the agent
        agent_input = {"input": message, "chat_history": chat_history_str}
        print(f"DEBUG: Agent input prepared with message: {message[:100]}...")

        # Get the response directly
        response = agent_executor.invoke(agent_input)

        # Extract the final output
        if isinstance(response, dict) and "output" in response:
            final_answer = response["output"]
        else:
            final_answer = str(response)
        print(f"DEBUG: Response: {response}")
        end = datetime.datetime.now()
        total = round((end - start).total_seconds(), 2)
        yield final_answer + f"\n\nTotal time: {total} seconds"

    except (ValueError, TypeError) as e:
        error_msg = f"❌ Error: {str(e)}"
        print(f"DEBUG: Exception occurred: {e}")
        yield error_msg


with gr.Blocks() as demo:

    gr.ChatInterface(
        chat,
        type="messages",
        save_history=True,
    )

demo.launch(server_port=5000)
