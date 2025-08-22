import asyncio
import logging
import os

from telethon.sessions import StringSession
from telethon.sync import TelegramClient

# --- Logging Setup ---
# Configure logging to show timestamp, level, and message.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.info("🚀 Starting session generator...")
logging.info("⚠️ IMPORTANT: Treat the output string like a password. Do not share it.")

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]


async def main() -> None:
    """Run main function."""
    # We use StringSession() to indicate we want the session as a string.
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        # The first run will prompt for phone, code, and 2FA password.
        # After a successful login, the session string is generated.
        session_string = client.session.save()
        logging.info("\n✅ Login successful! Your session string is below:")
        logging.info("======================================================")
        logging.info(session_string)
        logging.info("======================================================")
        logging.info(
            "\n📋 Copy this string and save it as the SESSION_STRING environment variable."
        )


if __name__ == "__main__":
    asyncio.run(main())
