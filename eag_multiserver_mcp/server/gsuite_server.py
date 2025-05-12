from mcp.server.fastmcp import FastMCP, Context
from gsuite_tools.gsheet_builder import create_gsheet_from_json
import logging
import os
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("gsuite-tools")


@mcp.tool()
async def create_gsheet(
    json_path: str,
    ctx: Context,
    email: str,
) -> str:
    """
    Create a Google Sheet from a JSON file containing search results and save it in a text file.
    This tool is to be triggered whenever the user wants to create a Google Sheet from a JSON file.

    Args:
        json_path: Path to the JSON file to convert to a Google Sheet
        ctx: MCP context for logging
        email: Email address to share the Google Sheet with and gmail would be used to send the sheet to the user

    Returns:
        String with the URL of the created Google Sheet
    """
    try:
        await ctx.info(f"Starting Google Sheet creation from: {json_path}")

        # Normalize path if needed
        json_path = os.path.normpath(json_path)

        # Validate JSON file exists
        if not os.path.exists(json_path):
            await ctx.error(f"JSON file not found: {json_path}")
            return f"Error: JSON file not found at {json_path}"

        # Hardcoded values
        credentials_path = "./server/credentials.json"
        sheet_prefix = "F1_Report"
        save_url_folder = "./server/outputs"

        # Validate credentials file
        credentials_path = os.path.normpath(credentials_path)
        if not os.path.exists(credentials_path):
            await ctx.error(f"Credentials file not found: {credentials_path}")
            return f"Error: Credentials file not found at {credentials_path}"

        # Log parameters
        await ctx.info(f"Using credentials from: {credentials_path}")
        await ctx.info(f"Sheet prefix: {sheet_prefix}")
        await ctx.info("Using EMAIL environment variable for sharing")

        # Create Google Sheet
        await ctx.info("Creating Google Sheet, this might take a moment...")
        sheet_url = create_gsheet_from_json(
            json_path=json_path,
            credentials_path=credentials_path,
            email=email,
            sheet_prefix=sheet_prefix,
            save_url_to_folder=save_url_folder,
        )

        # Format successful output
        await ctx.info(f"Google Sheet created successfully: {sheet_url}")

        output = []
        output.append("Google Sheet creation successful!")
        output.append(f"Source JSON: {json_path}")
        output.append(f"Sheet URL: {sheet_url}")
        output.append(
            "\nYou can access and share this Google Sheet using the URL above."
        )

        # Check if sheet was shared via EMAIL env var
        email_env = os.getenv("EMAIL")
        if email_env:
            output.append(f"The sheet has been shared with: {email_env}")
        else:
            output.append("Note: No EMAIL environment variable was set.")
            output.append("The sheet has not been shared automatically.")

        # Add information about saved URL file
        url_file_path = os.path.join(
            save_url_folder,
            f"gsheet_url_{os.path.basename(json_path).replace('.json', '')}.txt",
        )
        if os.path.exists(url_file_path):
            output.append(f"\nSheet URL also saved to: {url_file_path}")

        await ctx.info("Google Sheet creation process completed")
        return "\n".join(output)

    except Exception as e:
        error_msg = f"An error occurred while creating Google Sheet: {str(e)}"
        await ctx.error(f"Google Sheet creation error: {str(e)}")
        return error_msg


if __name__ == "__main__":
    print("Starting gsuite server")
    mcp.run(transport="stdio")
