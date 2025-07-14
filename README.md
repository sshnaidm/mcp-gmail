# Gmail AI Agent

This project provides an AI-powered assistant for managing your Gmail account. It uses LangChain agents to understand natural language queries, search your emails, and provide answers through a user-friendly chat interface.

## Features

- **Natural Language Email Search**: Ask questions like "Find emails from my boss this week" or "Summarize the last email from Acme Corp".
- **Interactive Chat UI**: A web-based chat interface powered by Gradio for easy interaction.
- **Pluggable LLMs**: Easily switch between different Large Language Models.
  - Google Gemini Pro
  - Locally-run models via Ollama (e.g., Qwen, Llama)
- **Secure Authentication**: Uses Google's OAuth 2.0 protocol to securely access your Gmail data. Your credentials are not stored in the code.
- **Tool-based Architecture**: Built with LangChain agents and tools, making it extensible.
- **Alternative Server**: Includes a `FastMCP` server to expose the Gmail search functionality as a standalone tool for other services.

## Prerequisites

- Python 3.8+
- A Google Account with a Gmail inbox.
- Ollama installed and running if you wish to use local models.

## Setup

### 1. Google Cloud Project & Credentials

To allow the application to read your emails, you need to authorize it with the Gmail API.

1. Go to the Google Cloud Console.
2. Create a new project.
3. Go to **APIs & Services > Library**, search for "Gmail API", and **Enable** it.
4. Go to **APIs & Services > OAuth consent screen**.
    - Choose **External** user type.
    - Fill in the required app information (app name, user support email, developer contact).
    - On the "Scopes" page, you don't need to add any scopes.
    - On the "Test users" page, add the Google account email address you want to use with the application.
5. Go to **APIs & Services > Credentials**.
    - Click **+ CREATE CREDENTIALS** and select **OAuth client ID**.
    - Select **Desktop app** for the Application type.
    - Give it a name (e.g., "Gmail Agent Client").
    - Click **Create**. A pop-up will show your Client ID and Client Secret. Click **DOWNLOAD JSON** to save the credentials file.
6. Rename the downloaded file to `credentials.json`.
7. Place the `credentials.json` file in a secure location. By default, the application looks for it at `~/.config/credentials.json`. You can also set the path using the `CREDENTIALS_FILE` environment variable.

    ```bash
    # Example:
    mkdir -p ~/.config
    mv /path/to/your/downloaded/credentials.json ~/.config/credentials.json
    ```

### 2. Clone & Install Dependencies

```bash
# Clone the repository
git clone <repository_url>
cd <repository_directory>

# Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install the required packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables (Optional)

If you are using Google Gemini, you need to set your API key.

```bash
export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
```

You can also specify a custom path for your credentials file:

```bash
export CREDENTIALS_FILE="/path/to/your/credentials.json"
```

## Usage

### Running the Gradio Chat Agent

The main application is the Gradio-based chat agent.

1. **Select your LLM**: Open `mailag.py` and `models.py`. In `mailag.py`, you can choose which LLM to use:

    ```python
    # in mailag.py
    from models import gemini, ollama

    llm = ollama # or llm = gemini
    ```

    In `models.py`, you can configure the specific model name (e.g., `qwen2:14b` for Ollama, `gemini-1.5-pro` for Gemini).

2. **Run the application**:

    ```bash
    python mailag.py
    ```

3. **First-time Authentication**: The first time you run the script, a browser window will open asking you to log in to your Google account and grant the application permission to read your emails. After you approve, a `token.json` file will be created in the project directory. This file stores your authorization token so you don't have to log in every time.

4. **Chat with your emails**: Open the Gradio URL printed in your terminal (usually `http://127.0.0.1:5007`) and start asking questions!

    **Example Prompts:**
    - `Find my last 3 emails`
    - `Search for emails from "some.sender@example.com" with the subject "Important Update"`
    - `What emails did I receive today?`

### Running the FastMCP Tool Server

This project also includes an alternative server that exposes the email search function as a tool using `FastMCP`. This is useful if you want to integrate the email search capability into another system.

```bash
python mcp_gmail.py
```

## Project Structure

- `mailag.py`: The main entry point for the Gradio chat application. It sets up the LangChain agent and the UI.
- `gmail.py`: Contains the core logic for authenticating with the Google API and fetching emails.
- `models.py`: Defines the LangChain LLM model configurations (Gemini, Ollama).
- `mcp_gmail.py`: An alternative entry point that runs a `FastMCP` server to expose the email search function as a tool.
- `requirements.txt`: A list of Python packages required for the project.
- `token.json`: (Generated on first run) Stores your OAuth access token. **Do not commit this file to version control.**
- `credentials.json`: (You provide this) Your Google Cloud OAuth client credentials. **Keep this file secure and do not commit it.**
