import os
import json
import datetime
import logging
import asyncio
import gspread
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot, InputMediaPhoto

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL = os.getenv("CHANNEL")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

logging.basicConfig(level=logging.INFO)

def get_today_text():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_json_str = os.getenv("GOOGLE_SHEET_CREDENTIALS")
        creds_info = json.loads(creds_json_str)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        data = sheet.get_all_values()
        if not data or len(data) < 2:
            return None, []

        headers = data[0]
        records = data[1:]

        def find_index(targets):
            for i, h in enumerate(headers):
                if any(t in h.lower() for t in targets):
                    return i
            return -1

        idx_date = find_index(["дата", "date"])
        idx_text = find_index(["текст", "post"])
        idx_links = find_index(["посилання", "link", "photo"])

        if idx_date == -1 or idx_text == -1 or idx_links == -1:
            return None, []

        lines = []
        media_links = []

        for row in records:
            if len(row) <= max(idx_date, idx_text, idx_links):
                continue
            if row[idx_date].strip() != today:
                continue
            lines.append(row[idx_text].strip())
            media_links.append(row[idx_links].strip())

        header = f"*Запорізька гімназія №110*
Дата: {today}"
        return header + "

" + "
".join(lines), media_links
    except Exception as e:
        logging.error(f"❌ Помилка при отриманні тексту: {e}")
        return None, []

async def post_to_telegram():
    bot = Bot(token=TOKEN)
    caption, links = get_today_text()
    if not caption or not links:
        print("📭 Немає контенту для публікації")
        return

    media = []
    for i, link in enumerate(links):
        try:
            media.append(InputMediaPhoto(media=link, caption=caption if i == 0 else None, parse_mode="Markdown"))
        except Exception as e:
            logging.warning(f"⚠️ Неможливо додати медіа: {link} — {e}")

    try:
        await bot.send_media_group(chat_id=CHANNEL, media=media)
        print("✅ Успішно опубліковано!")
    except Exception as e:
        logging.error(f"❌ Помилка Telegram: {e}")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(post_to_telegram, trigger="cron", hour=16, minute=0)
    scheduler.start()
    print("🕓 Планувальник запущено. Очікування...")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
