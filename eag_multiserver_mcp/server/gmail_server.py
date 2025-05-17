from mcp.server.fastmcp import FastMCP, Context
from gmail_tools.mail_tools import GmailService
import logging
import os
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("gmail-tools")


@mcp.tool()
async def send_email(
    recipient_id: str,
    subject: str,
    message: str,
    ctx: Context,
) -> str:
    """
    Send an email with optional attachment using Gmail API.
    The tool is to be used when the user wants to send an email to someone.

    Args:
        recipient_id: Email address of the recipient and gmail would be used to send the email to the user
        subject: Email subject line and the subject of the email
        message: Basic message with only elaborating the subject line with some salutations
        ctx: MCP context for logging

    Returns:
        String with the result of the email sending operation
    """
    try:
        await ctx.info(f"Starting email sending process to: {recipient_id}")

        # Define paths for credentials and token
        creds_file_path = "./server/oauth.json"
        token_path = "./server/token.json"

        # Validate credentials file
        if not os.path.exists(creds_file_path):
            await ctx.error(f"Credentials file not found: {creds_file_path}")
            return f"Error: OAuth credentials file not found at {creds_file_path}"

        # Validate token file
        if not os.path.exists(token_path):
            await ctx.error(f"Token file not found: {token_path}")
            return f"Error: Token file not found at {token_path}. Please run authentication first."

        # Check for attachments in the outputs directory
        attachments = []

        # Create outputs directory if it doesn't exist
        outputs_dir = os.path.join(os.getcwd(), "server", "outputs")
        os.makedirs(outputs_dir, exist_ok=True)

        # Find latest file in outputs directory
        files = glob.glob(os.path.join(outputs_dir, "*.txt"))
        attachment_path = None

        if files:
            # Sort files by modification time (newest first)
            files.sort(key=os.path.getmtime, reverse=True)
            attachment_path = files[0]
            attachment_path = os.path.normpath(attachment_path)
            await ctx.info(f"Using latest file as attachment: {attachment_path}")
            attachments.append(attachment_path)
        else:
            await ctx.info("No attachment files found in outputs directory")

        # Initialize Gmail service
        await ctx.info(
            f"Initializing Gmail service with credentials from: {creds_file_path}"
        )
        gmail_service = GmailService(creds_file_path, token_path)
        await ctx.info(f"Authenticated as: {gmail_service.user_email}")

        # Send the email
        await ctx.info(f"Sending email to {recipient_id} with subject: {subject}")
        result = await gmail_service.send_email(
            recipient_id=recipient_id,
            subject=subject,
            message=message,
            attachments=attachments if attachments else None,
        )

        # Process result
        if result["status"] == "success":
            success_message = (
                f"Email sent successfully! Message ID: {result['message_id']}"
            )
            await ctx.info(success_message)

            # Format successful output
            output = []
            output.append("Email sent successfully!")
            output.append(f"Recipient: {recipient_id}")
            output.append(f"Subject: {subject}")
            output.append(f"Message ID: {result['message_id']}")

            if attachments:
                output.append(f"Attachment: {attachment_path}")

            # Confirmation file path
            confirmation_file = os.path.join(
                os.getcwd(), "server", "outputs", "email_confirmation.txt"
            )
            output.append(f"\nConfirmation saved to: {confirmation_file}")

            return "\n".join(output)
        else:
            error_message = f"Failed to send email: {result['error_message']}"
            await ctx.error(error_message)
            return error_message

    except Exception as e:
        error_msg = f"An error occurred while sending email: {str(e)}"
        await ctx.error(error_msg)
        return error_msg


# @mcp.tool()
# async def test_gmail_connection(
#     ctx: Context,
# ) -> str:
#     """
#     Test the Gmail API connection and authentication.

#     Args:
#         ctx: MCP context for logging

#     Returns:
#         String with the test results
#     """
#     try:
#         await ctx.info("Testing Gmail API connection...")

#         # Define paths for credentials and token
#         creds_file_path = "./server/oauth.json"
#         token_path = "./server/token.json"

#         # Validate credentials file
#         if not os.path.exists(creds_file_path):
#             await ctx.error(f"Credentials file not found: {creds_file_path}")
#             return f"Error: OAuth credentials file not found at {creds_file_path}"

#         # Initialize Gmail service
#         await ctx.info(
#             f"Initializing Gmail service with credentials from: {creds_file_path}"
#         )
#         gmail_service = GmailService(creds_file_path, token_path)

#         # Format successful output
#         output = []
#         output.append("Gmail API connection test successful!")
#         output.append(f"Using credentials from: {creds_file_path}")
#         output.append(f"Using token from: {token_path}")
#         output.append(f"Authenticated as: {gmail_service.user_email}")

#         # Test retrieving unread emails
#         await ctx.info("Testing retrieval of unread emails...")
#         unread = await gmail_service.get_unread_emails(max_results=3)

#         if isinstance(unread, list):
#             output.append(f"\nFound {len(unread)} unread emails")
#             if unread:
#                 output.append("Connection is working properly!")
#             else:
#                 output.append("No unread emails found, but connection is working.")
#         else:
#             output.append(f"\nError getting unread emails: {unread}")

#         return "\n".join(output)

#     except Exception as e:
#         error_msg = f"An error occurred while testing Gmail connection: {str(e)}"
#         await ctx.error(error_msg)
#         return error_msg


if __name__ == "__main__":
    print("Starting gmail server")
    mcp.run(transport="stdio")
