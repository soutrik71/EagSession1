import os
import asyncio
import logging
import base64
from email.message import EmailMessage
from email.header import decode_header
from base64 import urlsafe_b64decode
from email import message_from_bytes
import webbrowser
import sys
import html2text

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
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
        self.service: Resource = self._get_service()
        logger.info("Gmail service initialized")
        self.user_email = self._get_user_email()
        logger.info(f"User email retrieved: {self.user_email}")
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.body_width = 0  # Don't wrap text

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

    def _get_service(self) -> Resource:
        """Initialize Gmail API service"""
        try:
            service = build("gmail", "v1", credentials=self.token)
            return service
        except HttpError as error:
            logger.error(f"An error occurred building Gmail service: {error}")
            raise ValueError(f"An error occurred: {error}")

    def _get_user_email(self) -> str:
        """Get user email address"""
        try:
            profile = self.service.users().getProfile(userId="me").execute()
            user_email = profile.get("emailAddress", "")
            return user_email
        except HttpError as error:
            logger.error(f"Error getting user email: {error}")
            raise ValueError(f"Error getting user email: {error}")

    async def send_email(
        self,
        recipient_id: str,
        subject: str,
        message: str,
    ) -> dict:
        """Creates and sends an email message"""
        try:
            message_obj = EmailMessage()
            message_obj.set_content(message)

            message_obj["To"] = recipient_id
            message_obj["From"] = self.user_email
            message_obj["Subject"] = subject

            encoded_message = base64.urlsafe_b64encode(message_obj.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            send_message = await asyncio.to_thread(
                self.service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute
            )
            logger.info(f"Message sent: {send_message['id']}")
            return {"status": "success", "message_id": send_message["id"]}
        except HttpError as error:
            return {"status": "error", "error_message": str(error)}

    async def open_email(self, email_id: str) -> str:
        """Opens email in browser given ID."""
        try:
            url = f"https://mail.google.com/#all/{email_id}"
            webbrowser.open(url, new=0, autoraise=True)
            return "Email opened in browser successfully."
        except HttpError as error:
            return f"An HttpError occurred: {str(error)}"

    async def get_unread_emails(self) -> list[dict[str, str]] | str:
        """Retrieves unread messages from mailbox."""
        try:
            user_id = "me"
            query = "in:inbox is:unread category:primary"

            response = await asyncio.to_thread(
                self.service.users().messages().list(userId=user_id, q=query).execute
            )
            messages = []
            if "messages" in response:
                messages.extend(response["messages"])

            while "nextPageToken" in response:
                page_token = response["nextPageToken"]
                response = await asyncio.to_thread(
                    self.service.users()
                    .messages()
                    .list(userId=user_id, q=query, pageToken=page_token)
                    .execute
                )
                messages.extend(response["messages"])
            return messages

        except HttpError as error:
            return f"An HttpError occurred: {str(error)}"

    async def read_email(self, email_id: str) -> dict[str, str] | str:
        """Retrieves email contents including to, from, subject, and contents."""
        try:
            msg = await asyncio.to_thread(
                self.service.users()
                .messages()
                .get(userId="me", id=email_id, format="raw")
                .execute
            )
            email_metadata = {}

            # Decode the base64URL encoded raw content
            raw_data = msg["raw"]
            decoded_data = urlsafe_b64decode(raw_data)

            # Parse the RFC 2822 email
            mime_message = message_from_bytes(decoded_data)

            # Extract the email body
            body = None
            if mime_message.is_multipart():
                for part in mime_message.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
                    elif content_type == "text/html" and body is None:
                        # Only use HTML if we haven't found plain text
                        html_content = part.get_payload(decode=True).decode()
                        body = self.html_converter.handle(html_content)
            else:
                content_type = mime_message.get_content_type()
                payload = mime_message.get_payload(decode=True).decode()
                if content_type == "text/html":
                    body = self.html_converter.handle(payload)
                else:
                    body = payload

            email_metadata["content"] = body if body else "No content found"

            # Extract metadata
            email_metadata["subject"] = decode_mime_header(
                mime_message.get("subject", "")
            )
            email_metadata["from"] = mime_message.get("from", "")
            email_metadata["to"] = mime_message.get("to", "")
            email_metadata["date"] = mime_message.get("date", "")

            logger.info(f"Email read: {email_id}")

            # We want to mark email as read once we read it
            await self.mark_email_as_read(email_id)

            return email_metadata
        except HttpError as error:
            return f"An HttpError occurred: {str(error)}"

    async def trash_email(self, email_id: str) -> str:
        """Moves email to trash given ID."""
        try:
            self.service.users().messages().trash(userId="me", id=email_id).execute()
            logger.info(f"Email moved to trash: {email_id}")
            return "Email moved to trash successfully."
        except HttpError as error:
            return f"An HttpError occurred: {str(error)}"

    async def mark_email_as_read(self, email_id: str) -> str:
        """Marks email as read given ID."""
        try:
            self.service.users().messages().modify(
                userId="me", id=email_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            logger.info(f"Email marked as read: {email_id}")
            return "Email marked as read."
        except HttpError as error:
            return f"An HttpError occurred: {str(error)}"

    async def get_recent_emails(
        self, max_results: int = 5
    ) -> list[dict[str, str]] | str:
        """Retrieves recent messages from inbox."""
        try:
            user_id = "me"
            query = "in:inbox"  # Get all inbox emails

            response = await asyncio.to_thread(
                self.service.users()
                .messages()
                .list(userId=user_id, q=query, maxResults=max_results)
                .execute
            )
            messages = []
            if "messages" in response:
                messages.extend(response["messages"])
            return messages

        except HttpError as error:
            return f"An HttpError occurred: {str(error)}"


async def main():
    try:
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = os.path.join(script_dir, "credentials.json")
        token_path = os.path.join(script_dir, "token.json")

        if not os.path.exists(creds_path):
            print("Error: credentials.json file not found!")
            print(f"Please place your Gmail API credentials file at: {creds_path}")
            print("To get credentials:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Create a project and enable Gmail API")
            print("3. Create OAuth 2.0 credentials")
            print("4. Download credentials as JSON")
            print("5. Save as credentials.json in the script directory")
            sys.exit(1)

        gmail_service = GmailService(creds_file_path=creds_path, token_path=token_path)

        # Get recent emails
        print("\nFetching 5 most recent emails...")
        recent_emails = await gmail_service.get_recent_emails(5)

        if isinstance(recent_emails, list) and recent_emails:
            print(f"\nFound {len(recent_emails)} recent emails")

            # Read each email
            for i, email in enumerate(recent_emails, 1):
                print(f"\nReading email {i} of {len(recent_emails)}...")
                email_content = await gmail_service.read_email(email["id"])

                if isinstance(email_content, dict):
                    print("\n" + "=" * 50)
                    print(f"Email #{i}:")
                    print(f"From: {email_content['from']}")
                    print(f"Subject: {email_content['subject']}")
                    print(f"Date: {email_content['date']}")
                    print("\nContent:")
                    print(email_content["content"])
                    print("=" * 50)
                else:
                    print(f"Error reading email {i}: {email_content}")
        else:
            print("No emails found or error occurred")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
