# Auto Photo Bot для Telegram

Цей бот:
- Публікує щоденні пости в Telegram-канал о 16:00
- Бере текст з Google Sheets
- Бере фото та відео з Google Drive (посилання в таблиці)
- Написано на `python-telegram-bot v20.0`

## 🛠 Необхідні змінні оточення (Environment Variables)

| Назва                  | Опис                                 |
|------------------------|--------------------------------------|
| `TOKEN`                | Токен бота Telegram                  |
| `CHANNEL`              | Ім'я або ID каналу, наприклад `@MyChannel` |
| `SPREADSHEET_ID`       | ID Google-таблиці                   |
| `GOOGLE_SHEET_CREDENTIALS` | JSON (однорядковий) із сервісного облікового запису Google |

## 📦 Запуск локально

```bash
pip install -r requirements.txt
python main.py
```

## 🚀 Деплой на Render

1. Підключи GitHub репозиторій
2. Додай змінні оточення у Render → Environment
3. Стартова команда: `python main.py`