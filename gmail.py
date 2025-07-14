import base64
import json
import os
import logging
import ast

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = os.environ.get("CREDENTIALS_FILE", os.path.expanduser("~/.config/credentials.json"))

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler("gmail.log"),
        # logging.StreamHandler() # Uncomment to see logs in console as well
    ],
)
logger = logging.getLogger(__name__)


def get_message_body(payload: dict) -> str:
    """
    Parses a message payload to find the 'text/plain' part and decodes it.
    This function will recursively search through multipart messages.
    """
    logger.debug(f"Parsing message part with mimeType: {payload.get('mimeType')}")
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"]["data"]
                logger.debug("Found text/plain part, decoding body.")
                return base64.urlsafe_b64decode(data).decode("utf-8")
            # Recursive call for nested multipart messages
            if "parts" in part:
                body = get_message_body(part)
                if body:
                    return body
    # Handle simple, non-multipart messages
    elif "body" in payload and "data" in payload["body"]:
        data = payload["body"]["data"]
        logger.debug("Found body in non-multipart message, decoding.")
        return base64.urlsafe_b64decode(data).decode("utf-8")
    logger.debug("No text/plain part found in this payload section.")
    return ""  # Return empty string if no plain text part is found


def get_emails(gmail_query: str = "to:me in:Inbox", count: int = 50, page: int = 1, full_body: bool = False):
    """Fetches emails based on the provided query.
    Args:
        gmail_query (str): Gmail query to filter emails. Default is 'to:me in:inbox'.
        count (int): Number of emails to fetch per page. Default is 100.
        page (int): Page number for pagination. Default is 1.
        full_body (bool): If True, fetches the full body of the email. If False, fetches only the snippet.
    Returns:
        str: A formatted string containing emails details.
    """
    logger.info(
        f"Starting get_emails with gmail_query='{gmail_query}' count='{count}' "
        f"page='{page}', full_body='{full_body}'"
    )
    if gmail_query.strip().startswith("{") and gmail_query.strip().endswith("}"):
        # params = json.loads(gmail_query.strip())
        # Fix JSON/Python boolean parsing
        try:
            logger.debug("Parsing gmail_query as JSON.")
            params = json.loads(gmail_query.strip().replace("True", "true").replace("False", "false"))
        # gmail_query = gmail_query.replace("true", "True").replace("false", "False")
        except json.JSONDecodeError as e:
            logger.debug(f"Parsing gmail_query as JSON failed: {e}")
            params = ast.literal_eval(gmail_query.strip().strip().replace("true", "True").replace("false", "False"))
        query = params.get("query", "to:me in:Inbox")
        count = params.get("count", count)
        page = params.get("page", page)
        full_body = params.get("full_body", False)
    else:
        query = gmail_query
    logger.info(f"Fetching emails with query='{query}', count={count}, page={page}, full_body={full_body}")
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists("token.json"):
        logger.info("Found token.json, loading credentials.")
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Credentials expired, refreshing token.")
            creds.refresh(Request())
        else:
            logger.info("No valid credentials found, starting OAuth flow.")
            # YOU MUST HAVE your credentials.json file from Google Cloud here
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            logger.info("Saving new credentials to token.json.")
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail service built successfully.")

        # Get a list of messages
        logger.info(f"Executing search with query: {query}")
        results = service.users().messages().list(userId="me", q=query).execute()

        messages = results.get("messages", [])

        if not messages:
            logger.warning(f"No messages found for query: {query}")
            return f"No messages found for query: {query}"
        else:
            logger.info(f"Found {len(messages)} messages for query: {query}")
            result = f"Found {len(messages)} messages for query: {query}\n"
            result += "--- Email Report ---\n"
            for message in messages[(page - 1) * count: page * count]:
                logger.debug(f"Fetching details for message ID: {message['id']}")
                msg = service.users().messages().get(userId="me", id=message["id"]).execute()
                headers = msg["payload"]["headers"]
                headers_dict = {header["name"]: header["value"] for header in headers}
                result += "#" * 10 + f" Message ID: {msg['id']} " + "#" * 10
                result += f"\nFrom: {headers_dict.get('From', 'Unknown Sender')}\n"
                result += f"Subject: {headers_dict.get('Subject', 'No Subject')}\n"
                if full_body:
                    body = get_message_body(msg["payload"])
                    result += f"Mail body: {body}\n"
                else:
                    result += f"Snippet: {msg.get('snippet', 'No snippet available')}\n"
            return result
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return f"An error occurred while fetching emails: {e}"


# Example usage:
# print(get_emails("to:me in:inbox", count=5, page=1, full_body=False))
# print(get_emails("Gemini OR 'Gemini API keys' OR Copilot OR 'Gemini CLI'", count=50, page=1, full_body=False))
