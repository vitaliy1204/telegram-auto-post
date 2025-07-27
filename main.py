import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from telegram.constants import ParseMode
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_NAME")
GS_JSON = os.getenv("GS_JSON_PATH")
GS_SHEET = os.getenv("GS_SHEET_NAME")

bot = Bot(token=TOKEN)


def get_today_text_and_photos():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GS_JSON, scope)
    client = gspread.authorize(creds)
    sheet = client.open(GS_SHEET).sheet1

    today = datetime.now().strftime("%d.%m.%Y")
    rows = sheet.get_all_records()
    lines = []
    media_urls = []

    for row in rows:
        if str(row.get("Дата")) == today:
            lines.append(f"• {row.get('Текст', '')}")
            if row.get("Фото"):
                media_urls.append(row["Фото"])

    header = f"""*Запорізька гімназія №110*
Дата: {сьогодні}"""
    return full_text, media_urls

async def post_to_telegram():
    text, media_urls = get_today_text_and_photos()
    if not media_urls:
        await bot.send_message(chat_id=CHANNEL, text=text, parse_mode=ParseMode.MARKDOWN)
    else:
        media = [InputMediaPhoto(url) for url in media_urls]
        media[0].caption = text
        media[0].parse_mode = ParseMode.MARKDOWN
        await bot.send_media_group(chat_id=CHANNEL, media=media)


async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    scheduler.add_job(post_to_telegram, "cron", hour=16, minute=0)
    scheduler.start()

    print("Бот працює. Очікування задачі...")
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
