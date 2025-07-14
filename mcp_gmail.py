"""This module provides a FastMCP tool for fetching emails from Gmail."""
import os

from fastmcp import FastMCP
from pydantic import Field, ValidationError

from gmail import get_emails

# Initialize FastMCP server
mcp = FastMCP(
    name="gmail_mails",
    instructions="Fetch emails from Gmail using the Gmail API and search mails query.",
)


@mcp.tool(
    name="List Available Tools",
    description="List all available tools.",
)
def list_tools() -> str:
    """List all available tools."""
    return mcp.list_tools()  # type: ignore # pylint: disable=no-member


@mcp.tool(
    name="Get Emails from Gmail",
    description="""
    Fetch Gmail emails using a query. Filter, emails per page, paginate, full body or snippet.
    Input should be a JSON object with the following fields:
    - `gmail_query`: The search query to filter emails (default: "to:me in:Inbox").
       Dates can be specified in the query in the format "YYYY-MM-DD", i.e. "after:2023-01-01 before:2023-01-31".
    - `count`: Number of emails to fetch per page (default: 100).
    - `page`: Page number for pagination (default: 1).
    - `full_body`: If True, fetches the full body of the email; if False, fetches only the snippet (default: False).
    Output will be a formatted string containing the details of the fetched emails.
    Doesn't require any additional setup or authentication.
    """,
)
def get_emails_tool(
    # Define the parameters for the tool
    gmail_query: str = Field(
        default="to:me in:inbox",
        description="Gmail query to filter emails. Default is 'to:me in:inbox'.",
    ),
    count: int = Field(
        default=100,
        description="Number of emails to fetch per page.",
    ),
    page: int = Field(
        default=1,
        description="Page number for pagination.",
    ),
    full_body: bool = Field(
        default=False,
        description="If True, fetches the full body of the email. If False, fetches only the snippet.",
    ),
) -> str:
    """Fetches emails based on the provided query."""
    if not isinstance(gmail_query, str):
        raise ValidationError("gmail_query must be a string.")
    if not isinstance(count, int):
        try:
            count = int(count)
        except ValueError as exc:
            raise ValidationError("count must be an integer.") from exc
    if not isinstance(page, int):
        try:
            page = int(page)
        except ValueError as exc:
            raise ValidationError("page must be an integer.") from exc
    if not isinstance(full_body, bool):
        try:
            full_body = bool(full_body)
        except ValueError as exc:
            raise ValidationError("full_body must be a boolean.") from exc
    try:
        return get_emails(gmail_query, count, page, full_body)
    except ValidationError as e:
        return f"Validation error: {e}"


if __name__ == "__main__":
    if not os.getenv("CREDENTIALS_FILE"):
        raise ValueError("CREDENTIALS_FILE environment variable is not set for the server to run.")
    # Run the FastMCP server
    mcp.run()
