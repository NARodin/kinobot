import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY", "")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

if not KINOPOISK_API_KEY:
    raise RuntimeError("KINOPOISK_API_KEY is not set")
