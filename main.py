import asyncio
import logging
import os
import sys
from threading import Thread

from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# =================================================================================
# 1. CONFIGURATION
# =================================================================================

# --- Logging Setup ---
# Configure logging to show timestamp, level, and message.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# --- Credentials (from Environment Variables) ---
# For security and flexibility, credentials are read from the environment.
try:
    HOST = os.environ.get("HOST")
    API_ID = int(os.environ["API_ID"])
    API_HASH = os.environ["API_HASH"]
    BOT_TOKEN = os.environ["BOT_TOKEN"]
    NOTIFY_USER_ID = int(os.environ["NOTIFY_USER_ID"])
    SESSION_STRING = os.environ["SESSION_STRING"]
except (KeyError, ValueError) as e:
    logging.critical("FATAL: Missing or invalid environment variable: %s. Please set it.", e)
    sys.exit(1)


# Add the numeric IDs of the channels you want to monitor.
CHANNEL_IDS = [
    -1001545535753,  # PROMOÇÕES IMPERDÍVEIS
    -1001437566099,  # Gafanhoto - Promoções
    -1001079131412,  # Pelando Promoções
    -1001446728597,  # Promobit - Promoções e Cupons de Desconto
    -1001007742949,  # [CANAL] PromoTop
    -1001420953728,  # Canal Cuponeiro Oficial
    -1002520998239,  # Pxinxa - Descontos
    -1001371796882,  # La Promotion - Promoções
    -1001260857435,  # LinksBR - Promoções
]

# Define the products and the keywords that MUST ALL be present in a message.
PRODUCTS_KEYWORDS = {
    "smartwatch": ["44mm", "watch7"],
    "smartphone": ["galaxy", "s25"],
}


# =================================================================================
# 2. APPLICATION LOGIC
# =================================================================================

# Initialize clients: one for the user account (monitors) and one for the bot (notifies).
user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient("bot_session", API_ID, API_HASH)

app = Flask(__name__)


def check_for_match(text: str | None) -> str | None:
    """Check if the message text contains all keywords for any product.

    Args:
        text: The text content of the message.

    Returns:
        The name of the matched product as a string, or None if no match is found.

    """
    if not text:
        return None

    lower_text = text.lower()
    for product_name, keywords in PRODUCTS_KEYWORDS.items():
        if all(keyword.lower() in lower_text for keyword in keywords):
            logging.info("✅ Match found for product '%s'!", product_name)
            return product_name
    return None


@user_client.on(events.NewMessage(chats=CHANNEL_IDS))
async def message_handler(event: events.NewMessage.Event) -> None:
    """Handle new messages.

    If a match is found, the bot copies the original text and
    sends it as a new message to the user.

    Args:
        event: The event object containing the new message.

    """
    message = event.message
    logging.info("-> New message from channel %s. Checking...", message.chat_id)

    matched_product = check_for_match(message.text)
    if matched_product and message.text:
        try:
            # Step 1: Create the new message content.
            # It combines a clear header with the full text from the original post.
            notification_text = (
                f"🔥 **Promotion Found: {matched_product.title()}**\n"
                f"--------------------------------------\n\n"
                f"{message.text}"
            )

            # Step 2: The bot sends the composed message.
            # We disable the web page preview for a cleaner look, as links
            # in promotion messages can sometimes generate large, ugly previews.
            await bot_client.send_message(
                entity=NOTIFY_USER_ID,
                message=notification_text,
                parse_mode="md",
                link_preview=False,
            )
            logging.info("👍 Sent copied message content from message ID %s.", message.id)

        except Exception:
            logging.exception("❌ Failed to send message for original message ID %s.", message.id)


@app.route("/")
def health_check() -> str:
    """Check health endpoint for the hosting service."""
    return "Monitoring service is running and healthy."


def run_flask_app() -> None:
    """Run the Flask web server."""
    app.run(host=HOST, port=8080)


async def main() -> None:
    """Connect and run both the user and bot clients."""
    logging.info("🚀 Starting Telethon clients...")
    try:
        await bot_client.start(bot_token=BOT_TOKEN)
        logging.info("✅ Bot client connected.")
        await user_client.start()
        logging.info("✅ User client connected and listening for messages.")
        await user_client.run_until_disconnected()
    finally:
        if bot_client.is_connected():
            await bot_client.disconnect()
        if user_client.is_connected():
            await user_client.disconnect()
    logging.info("Clients disconnected.")


if __name__ == "__main__":
    # Run Flask in a separate thread so it doesn't block the async Telethon client.
    flask_thread = Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    # Run the main async function for Telethon in the main thread.
    logging.info("Starting application...")
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Application shutting down.")
