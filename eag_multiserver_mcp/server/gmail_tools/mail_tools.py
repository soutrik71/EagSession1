from typing import Any, List, Dict, Optional
import os
import asyncio
import logging
import base64
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.header import decode_header
from base64 import urlsafe_b64decode
from email import message_from_bytes
import mimetypes

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def decode_mime_header(header: str) -> str:
    """Helper function to decode encoded email headers"""

    decoded_parts = decode_header(header)
    decoded_string = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            # Decode bytes to string using the specified encoding
            decoded_string += part.decode(encoding or "utf-8")
        else:
            # Already a string
            decoded_string += part
    return decoded_string


class GmailService:
    def __init__(
        self,
        creds_file_path: str,
        token_path: str,
        scopes: list[str] = ["https://www.googleapis.com/auth/gmail.modify"],
    ):
        logger.info(f"Initializing GmailService with creds file: {creds_file_path}")
        self.creds_file_path = creds_file_path
        self.token_path = token_path
        self.scopes = scopes
        self.token = self._get_token()
        logger.info("Token retrieved successfully")
        self.service = self._get_service()
        logger.info("Gmail service initialized")
        self.user_email = self._get_user_email()
        logger.info(f"User email retrieved: {self.user_email}")

    def _get_token(self) -> Credentials:
        """Get or refresh Google API token"""

        token = None

        if os.path.exists(self.token_path):
            logger.info("Loading token from file")
            token = Credentials.from_authorized_user_file(self.token_path, self.scopes)

        if not token or not token.valid:
            if token and token.expired and token.refresh_token:
                logger.info("Refreshing token")
                token.refresh(Request())
            else:
                logger.info("Fetching new token")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds_file_path, self.scopes
                )
                token = flow.run_local_server(port=0)

            with open(self.token_path, "w") as token_file:
                token_file.write(token.to_json())
                logger.info(f"Token saved to {self.token_path}")

        return token

    def _get_service(self) -> Any:
        """Initialize Gmail API service"""
        try:
            service = build("gmail", "v1", credentials=self.token)
            return service
        except HttpError as error:
            logger.error(f"An error occurred building Gmail service: {error}")
            raise ValueError(f"An error occurred: {error}")

    def _get_user_email(self) -> str:
        """Get user email address"""
        profile = self.service.users().getProfile(userId="me").execute()
        user_email = profile.get("emailAddress", "")
        return user_email

    async def send_email(
        self,
        recipient_id: str,
        subject: str,
        message: str,
        attachments: Optional[List[str]] = None,
    ) -> dict:
        """
        Creates and sends an email message with optional attachments.

        Args:
            recipient_id: Email address of the recipient
            subject: Email subject line
            message: Email body text
            attachments: List of file paths to attach (optional)

        Returns:
            Dictionary with status and message ID or error message
        """
        try:
            # Create multipart message
            email_message = MIMEMultipart()
            email_message["To"] = recipient_id
            email_message["From"] = self.user_email
            email_message["Subject"] = subject

            # Attach the text message
            email_message.attach(MIMEText(message, "plain"))

            # Process attachments if provided
            if attachments:
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        logger.warning(f"Attachment not found: {file_path}")
                        continue

                    # Guess the content type based on the file's extension
                    content_type, encoding = mimetypes.guess_type(file_path)

                    if content_type is None or encoding is not None:
                        # If type cannot be guessed, use a generic type
                        content_type = "application/octet-stream"

                    main_type, sub_type = content_type.split("/", 1)

                    with open(file_path, "rb") as fp:
                        attachment = MIMEBase(main_type, sub_type)
                        attachment.set_payload(fp.read())

                    # Encode in base64
                    base64.encodebytes(attachment.get_payload())

                    # Add headers
                    filename = os.path.basename(file_path)
                    attachment.add_header(
                        "Content-Disposition", "attachment", filename=filename
                    )
                    email_message.attach(attachment)

            # Encode the message
            encoded_message = base64.urlsafe_b64encode(
                email_message.as_bytes()
            ).decode()
            create_message = {"raw": encoded_message}

            # Send the message
            send_message = await asyncio.to_thread(
                self.service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute
            )

            logger.info(f"Message sent: {send_message['id']}")
            return {"status": "success", "message_id": send_message["id"]}

        except HttpError as error:
            logger.error(f"Error sending email: {error}")
            return {"status": "error", "error_message": str(error)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"status": "error", "error_message": str(e)}

    async def get_unread_emails(
        self, max_results: int = 10
    ) -> List[Dict[str, Any]] | str:
        """
        Retrieves unread messages from mailbox.

        Args:
            max_results: Maximum number of emails to retrieve

        Returns:
            List of message IDs or error message
        """
        try:
            user_id = "me"
            query = "in:inbox is:unread category:primary"

            response = (
                self.service.users()
                .messages()
                .list(userId=user_id, q=query, maxResults=max_results)
                .execute()
            )

            messages = []
            if "messages" in response:
                messages.extend(response["messages"])

            while "nextPageToken" in response and len(messages) < max_results:
                page_token = response["nextPageToken"]
                response = (
                    self.service.users()
                    .messages()
                    .list(
                        userId=user_id,
                        q=query,
                        pageToken=page_token,
                        maxResults=max_results - len(messages),
                    )
                    .execute()
                )

                if "messages" in response:
                    messages.extend(response["messages"])

            return messages

        except HttpError as error:
            return f"An HttpError occurred: {str(error)}"

    async def read_email(self, email_id: str) -> Dict[str, Any] | str:
        """
        Retrieves email contents including to, from, subject, body and attachments.

        Args:
            email_id: ID of the email to read

        Returns:
            Dictionary containing email metadata and content, or error message
        """
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=email_id, format="full")
                .execute()
            )
            email_metadata = {}

            # Get headers
            headers = msg["payload"]["headers"]
            for header in headers:
                name = header["name"].lower()
                if name in ["from", "to", "subject", "date"]:
                    email_metadata[name] = decode_mime_header(header["value"])

            # Process body and attachments
            parts = []
            attachments = []

            if "parts" in msg["payload"]:
                parts = msg["payload"]["parts"]
            else:
                parts = [msg["payload"]]

            body = self._process_parts(parts, attachments)
            email_metadata["body"] = body
            email_metadata["attachments"] = attachments

            logger.info(f"Email read: {email_id}")

            # Mark email as read
            await self.mark_email_as_read(email_id)

            return email_metadata

        except HttpError as error:
            return f"An HttpError occurred: {str(error)}"

    def _process_parts(self, parts, attachments, depth=0):
        """
        Process the email parts recursively to extract body and attachments.

        Args:
            parts: Email parts to process
            attachments: List to collect attachments
            depth: Current recursion depth

        Returns:
            String containing the email body text
        """
        if depth > 20:  # Prevent infinite recursion
            return ""

        body = ""

        for part in parts:
            mime_type = part.get("mimeType", "")

            # If this part has nested parts, process them recursively
            if "parts" in part:
                body += self._process_parts(part["parts"], attachments, depth + 1)

            # Handle text content
            elif mime_type.startswith("text/plain"):
                if "data" in part.get("body", {}):
                    text = base64.urlsafe_b64decode(part["body"]["data"]).decode()
                    body += text

            # Handle attachments
            elif "attachmentId" in part.get("body", {}):
                attachment = {
                    "id": part["body"]["attachmentId"],
                    "filename": part.get("filename", "unknown"),
                    "mimeType": mime_type,
                }
                attachments.append(attachment)

        return body

    async def download_attachment(self, email_id: str, attachment_id: str) -> dict:
        """
        Downloads an email attachment.

        Args:
            email_id: ID of the email containing the attachment
            attachment_id: ID of the attachment to download

        Returns:
            Dictionary containing attachment data and metadata
        """
        try:
            attachment = (
                self.service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=email_id, id=attachment_id)
                .execute()
            )

            file_data = base64.urlsafe_b64decode(attachment["data"])

            return {"data": file_data, "size": attachment["size"]}

        except HttpError as error:
            logger.error(f"Error downloading attachment: {error}")
            return {"error": str(error)}

    async def save_attachment(
        self, email_id: str, attachment_id: str, save_path: str
    ) -> str:
        """
        Downloads and saves an email attachment to disk.

        Args:
            email_id: ID of the email containing the attachment
            attachment_id: ID of the attachment to download
            save_path: Path where the attachment should be saved

        Returns:
            Success message or error message
        """
        try:
            attachment_data = await self.download_attachment(email_id, attachment_id)

            if "error" in attachment_data:
                return f"Error downloading attachment: {attachment_data['error']}"

            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)

            with open(save_path, "wb") as file:
                file.write(attachment_data["data"])

            return f"Attachment saved to {save_path}"

        except Exception as e:
            logger.error(f"Error saving attachment: {e}")
            return f"Error saving attachment: {str(e)}"

    async def mark_email_as_read(self, email_id: str) -> str:
        """
        Marks email as read given ID.

        Args:
            email_id: ID of the email to mark as read

        Returns:
            Success message or error message
        """
        try:
            self.service.users().messages().modify(
                userId="me", id=email_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()

            logger.info(f"Email marked as read: {email_id}")
            return "Email marked as read."

        except HttpError as error:
            return f"An HttpError occurred: {str(error)}"


async def test_email_service(creds_file_path: str, token_path: str):
    """
    Test function for the GmailService class.

    Args:
        creds_file_path: Path to the OAuth credentials file
        token_path: Path to store/retrieve OAuth tokens
    """
    gmail_service = GmailService(creds_file_path, token_path)

    # Example: Get unread emails
    unread = await gmail_service.get_unread_emails(max_results=5)
    print(f"Unread emails: {unread}")

    # If there are unread emails, read the first one
    if isinstance(unread, list) and unread:
        email_id = unread[0]["id"]
        email_content = await gmail_service.read_email(email_id)
        print(f"Email content: {email_content}")

        # If there are attachments, download the first one
        if isinstance(email_content, dict) and email_content.get("attachments"):
            attachment = email_content["attachments"][0]
            save_result = await gmail_service.save_attachment(
                email_id, attachment["id"], f"downloads/{attachment['filename']}"
            )
            print(save_result)

    # Example: Send an email with attachment
    # result = await gmail_service.send_email(
    #     "recipient@example.com",
    #     "Test Email with Attachment",
    #     "This is a test email with an attachment.",
    #     attachments=["path/to/file.pdf"]
    # )
    # print(f"Send result: {result}")


if __name__ == "__main__":
    asyncio.run(
        test_email_service(
            "./server/oauth.json",
            "./server/token.json",
        )
    )
