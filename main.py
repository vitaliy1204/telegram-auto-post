
import os
import json
import logging
import datetime
import aiohttp
import asyncio
from telegram import InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
CHANNEL = os.getenv("CHANNEL")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
PHOTO_COLUMN_KEYWORDS = ["google drive", "photo", "фото", "посилання"]
TEXT_COLUMN_KEYWORDS = ["текст", "post"]
DATE_COLUMN_KEYWORDS = ["дата", "date"]
WHO_COLUMN_KEYWORDS = ["хто", "хто писав", "author"]
EXTRA_COLUMN_KEYWORDS = ["доп", "extra"]

def get_today_text_and_links():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_info = json.loads(os.getenv("GOOGLE_SHEET_CREDENTIALS"))
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        data = sheet.get_all_values()
        if not data or len(data) < 2:
            return None, []

        headers = data[0]
        rows = data[1:]

        def find_index(targets):
            for i, h in enumerate(headers):
                h_clean = h.strip().lower()
                if any(t in h_clean for t in targets):
                    return i
            return -1

        idx_date = find_index(DATE_COLUMN_KEYWORDS)
        idx_text = find_index(TEXT_COLUMN_KEYWORDS)
        idx_extra = find_index(EXTRA_COLUMN_KEYWORDS)
        idx_who = find_index(WHO_COLUMN_KEYWORDS)
        idx_photos = find_index(PHOTO_COLUMN_KEYWORDS)

        if idx_date == -1 or idx_text == -1:
            logging.error("Не знайдено колонок 'дата' або 'текст'")
            return None, []

        lines = []
        photo_links = []

        for row in rows:
            if len(row) <= idx_date:
                continue
            row_date = row[idx_date].strip()
            if row_date != today:
                continue

            text = row[idx_text].strip() if idx_text < len(row) else ""
            extra = row[idx_extra].strip() if idx_extra != -1 and idx_extra < len(row) else ""
            who = row[idx_who].strip() if idx_who != -1 and idx_who < len(row) else ""
            photos = row[idx_photos].strip() if idx_photos != -1 and idx_photos < len(row) else ""

            if photos:
                photo_links.extend([p.strip() for p in photos.split(",") if p.strip()])

            line = " ".join([text, extra, who]).strip()
            lines.append(line)

        if not lines:
            return None, []

        full_text = f"*Запорізька гімназія №110*
Дата: {today}

" + "

".join(lines)
        return full_text, photo_links
    except Exception as e:
        logging.error(f"❌ Помилка при отриманні тексту з таблиці: {e}")
        return None, []

async def download_media(photo_links):
    media = []
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(photo_links):
            if "drive.google.com" in url:
                url = convert_drive_link(url)
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        ext = ".jpg" if "image" in resp.headers.get("Content-Type", "") else ".mp4"
                        filename = f"temp_{i}{ext}"
                        with open(filename, "wb") as f:
                            f.write(content)
                        if ext == ".mp4":
                            media.append(InputMediaVideo(media=open(filename, "rb")))
                        else:
                            media.append(InputMediaPhoto(media=open(filename, "rb")))
            except Exception as e:
                logging.warning(f"⚠️ Не вдалося завантажити {url}: {e}")
    return media

def convert_drive_link(url):
    if "file/d/" in url:
        file_id = url.split("/file/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    elif "open?id=" in url:
        file_id = url.split("open?id=")[-1]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    else:
        return url

async def post_to_telegram(application):
    caption, photo_links = get_today_text_and_links()
    if not caption:
        logging.info("📭 Немає тексту для публікації сьогодні")
        return

    logging.info("📥 Завантаження медіа...")
    media = await download_media(photo_links)
    if not media:
        logging.info("📢 Публікація лише тексту...")
        await application.bot.send_message(chat_id=CHANNEL, text=caption, parse_mode="Markdown")
        return

    media[0].caption = caption
    media[0].parse_mode = "Markdown"
    await application.bot.send_media_group(chat_id=CHANNEL, media=media)
    logging.info("✅ Опубліковано!")

def schedule_job(application):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(post_to_telegram, "cron", hour=16, minute=0, args=[application])
    scheduler.start()

async def main():
    application = ApplicationBuilder().token(TOKEN).build()
    schedule_job(application)
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
