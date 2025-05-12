from telethon import TelegramClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Client parameters
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUM = os.getenv("PHONE_NUM")

if not all([API_ID, API_HASH, PHONE_NUM]):
    raise ValueError(
        "TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE must be set in .env file"
    )


async def connect_telegram():
    """Connect to Telegram API"""
    print("Connecting to Telegram...")
    client = TelegramClient("Session", API_ID, API_HASH)
    if not await client.start():
        print("Could not connect to Telegram servers.")
        return None

    if not await client.is_user_authorized():
        print("First time login. Sending code request...")
        await client.sign_in(PHONE_NUM)
        while True:
            code = input("Enter the code you received: ")
            try:
                await client.sign_in(code=code)
                break
            except Exception as e:
                if "password" in str(e).lower():
                    pw = input(
                        "Two-step verification is enabled. Enter your password: "
                    )
                    await client.sign_in(password=pw)
                    break
                else:
                    print(f"Error: {e}")
                    return None

    print("Successfully connected to Telegram!")
    return client


async def get_messages(chat_link, limit=100):
    """
    Get messages from a chat/channel

    Args:
        chat_link (str): The link to the chat/channel (e.g., 'https://t.me/channel_name')
        limit (int): Maximum number of messages to retrieve (default: 100)

    Returns:
        list: List of dictionaries containing message information
    """
    client = await connect_telegram()
    if client is None:
        return []

    try:
        # Get the chat entity
        chat = await client.get_entity(chat_link)

        # Get messages
        messages = await client.get_messages(chat, limit=limit)

        # Process messages
        message_list = []
        for msg in messages:
            message_info = {
                "id": msg.id,
                "text": msg.text,
                "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                "sender": msg.sender.first_name if msg.sender else "Unknown",
                "username": msg.sender.username if msg.sender else None,
            }
            message_list.append(message_info)

        return message_list

    except Exception as e:
        print(f"Error getting messages: {e}")
        return []

    finally:
        await client.disconnect()


# Example usage:
async def main():
    chat_link = "https://t.me/soutrik_bot"
    messages = await get_messages(chat_link, limit=10)
    for msg in messages:
        print(f"From: {msg['sender']} (@{msg['username']})")
        print(f"Date: {msg['date']}")
        print(f"Message: {msg['text']}")
        print("-" * 50)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
