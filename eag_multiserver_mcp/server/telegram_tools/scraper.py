from telethon import TelegramClient, functions
import os
import sys
import logging
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Client parameters
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUM = os.getenv("PHONE_NUM")
SESSION_STRING = os.getenv("SESSION_STRING")
SESSION_NAME = os.getenv("SESSION_NAME", "Session")

# Setup logging
logger = logging.getLogger("telegram_scraper")
logger.setLevel(logging.ERROR)  # Set to ERROR for production, INFO for debugging

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s - %(filename)s:%(lineno)d"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

if not (API_ID and API_HASH):
    raise ValueError("API_ID and API_HASH must be set in .env file")


def log_message(message):
    """Log a message to stderr instead of stdout"""
    print(message, file=sys.stderr)


# Global client instance - will be initialized on first connect
telegram_client = None


async def connect_telegram(api_id=API_ID, api_hash=API_HASH, phone_num=PHONE_NUM):
    """Connect to Telegram API"""
    global telegram_client

    # If client already exists and is connected, return it
    if telegram_client is not None and telegram_client.is_connected():
        return telegram_client

    log_message("Connecting to Telegram...")

    # Use string session if available, otherwise use file-based session
    if SESSION_STRING:
        telegram_client = TelegramClient(
            StringSession(SESSION_STRING), api_id, api_hash
        )
    else:
        telegram_client = TelegramClient(SESSION_NAME, api_id, api_hash)

    try:
        # Start the client
        await telegram_client.start(phone=phone_num)

        # Verify the connection
        if not telegram_client.is_connected():
            log_message("Could not connect to Telegram servers.")
            return None

        if not await telegram_client.is_user_authorized():
            log_message("First time login. Sending code request...")
            await telegram_client.send_code_request(phone_num)
            while True:
                code = input("Enter the code you received: ")
                try:
                    await telegram_client.sign_in(phone_num, code)
                    break
                except Exception as e:
                    if "password" in str(e).lower():
                        pw = input(
                            "Two-step verification is enabled. Enter your password: "
                        )
                        await telegram_client.sign_in(password=pw)
                        break
                    else:
                        log_message(f"Error: {e}")
                        return None
    except Exception as e:
        log_message(f"Error connecting to Telegram: {e}")
        logger.exception("Failed to connect to Telegram")
        return None

    log_message("Successfully connected to Telegram!")

    # Print session string for future use if using a new session
    if not SESSION_STRING and isinstance(telegram_client.session, StringSession):
        session_str = telegram_client.session.save()
        log_message("Your session string (save this in .env as SESSION_STRING):")
        log_message(session_str)

    return telegram_client


async def disconnect_telegram(client=None):
    """Disconnect from Telegram API"""
    global telegram_client
    if client is None:
        client = telegram_client

    if client is not None and client.is_connected():
        try:
            await client.disconnect()
            log_message("Disconnected from Telegram")
        except Exception as e:
            log_message(f"Error disconnecting from Telegram: {e}")
            logger.exception("Failed to disconnect from Telegram")


async def get_messages(chat_link, limit=100, client=None):
    """
    Get messages from a chat/channel

    Args:
        chat_link (str): The link to the chat/channel (e.g., 'https://t.me/channel_name')
        limit (int): Maximum number of messages to retrieve (default: 100)
        client (TelegramClient, optional): An existing Telegram client. If None, a new connection will be made.

    Returns:
        list: List of dictionaries containing message information
    """
    global telegram_client

    # Determine if we should use provided client, existing global client, or create a new one
    should_disconnect = False

    if client is None:
        if telegram_client is not None and telegram_client.is_connected():
            client = telegram_client
        else:
            client = await connect_telegram()
            should_disconnect = True

    if client is None:
        log_message("Failed to get a valid Telegram client")
        return []

    try:
        # Extract username from chat link if it's a full URL
        if chat_link.startswith("https://t.me/"):
            chat_name = chat_link.split("https://t.me/")[1]
        else:
            chat_name = chat_link

        # Get the chat entity
        try:
            chat = await client.get_entity(chat_name)
        except ValueError:
            # Try resolving username first
            try:
                result = await client(
                    functions.contacts.ResolveUsernameRequest(username=chat_name)
                )
                if result.peer:
                    chat = await client.get_entity(result.peer)
                else:
                    log_message(f"Could not resolve username: {chat_name}")
                    return []
            except Exception as resolve_err:
                log_message(f"Error resolving username: {resolve_err}")
                return []

        # Get messages
        messages = await client.get_messages(chat, limit=limit)

        # Process messages
        message_list = []
        for msg in messages:
            try:
                message_info = {
                    "id": msg.id,
                    "text": msg.text or "[Media/No text]",
                    "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "sender": (
                        getattr(msg.sender, "first_name", "Unknown")
                        if msg.sender
                        else "Unknown"
                    ),
                    "username": (
                        getattr(msg.sender, "username", None) if msg.sender else None
                    ),
                }

                # Add more metadata as needed
                if msg.media:
                    message_info["has_media"] = True
                    message_info["media_type"] = type(msg.media).__name__

                message_list.append(message_info)
            except Exception as msg_err:
                log_message(f"Error processing message {msg.id}: {msg_err}")
                logger.exception(f"Error processing message {msg.id}")

        return message_list

    except Exception as e:
        log_message(f"Error getting messages: {e}")
        logger.exception("Failed to get messages")
        return []

    finally:
        # Only disconnect if we created a new connection
        if should_disconnect and client and client.is_connected():
            await client.disconnect()


async def get_chat_info(chat_link, client=None):
    """
    Get information about a chat/channel/user

    Args:
        chat_link (str): The link to the chat/channel (e.g., 'https://t.me/channel_name')
        client (TelegramClient, optional): An existing Telegram client. If None, a new connection will be made.

    Returns:
        dict: Dictionary containing chat information
    """
    global telegram_client

    # Determine if we should use provided client, existing global client, or create a new one
    should_disconnect = False

    if client is None:
        if telegram_client is not None and telegram_client.is_connected():
            client = telegram_client
        else:
            client = await connect_telegram()
            should_disconnect = True

    if client is None:
        return None

    try:
        # Extract username from chat link if it's a full URL
        if chat_link.startswith("https://t.me/"):
            chat_name = chat_link.split("https://t.me/")[1]
        else:
            chat_name = chat_link

        # Get the chat entity
        try:
            entity = await client.get_entity(chat_name)
        except ValueError:
            # Try resolving username first
            try:
                result = await client(
                    functions.contacts.ResolveUsernameRequest(username=chat_name)
                )
                if result.peer:
                    entity = await client.get_entity(result.peer)
                else:
                    log_message(f"Could not resolve username: {chat_name}")
                    return None
            except Exception as resolve_err:
                log_message(f"Error resolving username: {resolve_err}")
                return None

        # Extract chat info
        chat_info = {"id": entity.id, "type": "unknown"}

        from telethon.tl.types import User, Chat, Channel

        if isinstance(entity, User):
            chat_info["type"] = "user"
            chat_info["first_name"] = entity.first_name
            if entity.last_name:
                chat_info["last_name"] = entity.last_name
            if entity.username:
                chat_info["username"] = entity.username
            chat_info["is_bot"] = getattr(entity, "bot", False)

        elif isinstance(entity, Chat):
            chat_info["type"] = "group"
            chat_info["title"] = entity.title
            chat_info["participants_count"] = (
                entity.participants_count
                if hasattr(entity, "participants_count")
                else None
            )

        elif isinstance(entity, Channel):
            chat_info["type"] = (
                "channel" if getattr(entity, "broadcast", False) else "supergroup"
            )
            chat_info["title"] = entity.title
            if entity.username:
                chat_info["username"] = entity.username

            # Try to get participants count
            try:
                participants = await client.get_participants(entity, limit=0)
                chat_info["participants_count"] = participants.total
            except Exception as part_err:
                logger.warning(f"Could not get participant count: {part_err}")

        return chat_info

    except Exception as e:
        log_message(f"Error getting chat info: {e}")
        logger.exception("Failed to get chat info")
        return None

    finally:
        # Only disconnect if we created a new connection
        if should_disconnect:
            await client.disconnect()


async def search_messages(chat_link, query, limit=100, client=None):
    """
    Search for messages in a chat

    Args:
        chat_link (str): The link to the chat/channel
        query (str): Search query
        limit (int): Maximum number of messages to retrieve
        client (TelegramClient, optional): An existing Telegram client

    Returns:
        list: List of dictionaries containing message information
    """
    global telegram_client

    # Determine if we should use provided client, existing global client, or create a new one
    should_disconnect = False

    if client is None:
        if telegram_client is not None and telegram_client.is_connected():
            client = telegram_client
        else:
            client = await connect_telegram()
            should_disconnect = True

    if client is None:
        return []

    try:
        # Extract username from chat link if it's a full URL
        if chat_link.startswith("https://t.me/"):
            chat_name = chat_link.split("https://t.me/")[1]
        else:
            chat_name = chat_link

        # Get the chat entity
        try:
            chat = await client.get_entity(chat_name)
        except ValueError:
            # Try resolving username first
            try:
                result = await client(
                    functions.contacts.ResolveUsernameRequest(username=chat_name)
                )
                if result.peer:
                    chat = await client.get_entity(result.peer)
                else:
                    log_message(f"Could not resolve username: {chat_name}")
                    return []
            except Exception as resolve_err:
                log_message(f"Error resolving username: {resolve_err}")
                return []

        # Search messages
        messages = await client.get_messages(chat, limit=limit, search=query)

        # Process messages
        message_list = []
        for msg in messages:
            message_info = {
                "id": msg.id,
                "text": msg.text or "[Media/No text]",
                "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                "sender": (
                    getattr(msg.sender, "first_name", "Unknown")
                    if msg.sender
                    else "Unknown"
                ),
                "username": (
                    getattr(msg.sender, "username", None) if msg.sender else None
                ),
            }
            message_list.append(message_info)

        return message_list

    except Exception as e:
        log_message(f"Error searching messages: {e}")
        logger.exception("Failed to search messages")
        return []

    finally:
        # Only disconnect if we created a new connection
        if should_disconnect:
            await client.disconnect()


# Example usage:
async def main():
    # Connect to Telegram once
    client = await connect_telegram()
    if client:
        try:
            chat_link = "https://t.me/soutrik_bot"
            messages = await get_messages(chat_link, limit=10, client=client)
            if messages:
                # get the latest message
                latest_message = messages[0]
                log_message(
                    f"From: {latest_message['sender']} (@{latest_message['username']})"
                )
                log_message(f"Date: {latest_message['date']}")
                log_message(f"Message: {latest_message['text']}")
                log_message("-" * 50)

        finally:
            # Disconnect when done
            await disconnect_telegram()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
