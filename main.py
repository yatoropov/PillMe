# 2-22-7-06-2025
import asyncio
import os
import datetime
import pytz  # pip install pytz
from aiogram import Bot, Dispatcher, types, F
import gspread
from dotenv import load_dotenv
import openai

# 1. Завантаження змінних середовища
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 2. Ініціалізація Telegram-бота та Google Sheets
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
gc = gspread.service_account(filename='service_account.json')
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# 3. OpenAI клієнт
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 4. Таймзона Києва
KYIV_TZ = pytz.timezone("Europe/Kyiv")

# 5. Функція розбору тексту через OpenAI
async def parse_message(text: str) -> dict:
    prompt = f"""
Ти асистент-бот, який допомагає записувати прийом ліків.
Розбери це повідомлення на три поля:
- Назва ліків
- Кількість (число)
- Час (hh:mm або "зараз", якщо часу немає).
Форматуй відповідь так:
назва: ...
кількість: ...
час: ...

Ось текст: {text}
"""
    resp = await asyncio.to_thread(
        openai_client.chat.completions.create,
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=100,
    )
    answer = resp.choices[0].message.content
    # Примітивний парсер ключ:значення
    result = {}
    for line in answer.split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            result[k.strip().lower()] = v.strip()
    return result

# 6. Головний хендлер повідомлень
@dp.message(F.text)
async def handle_message(message: types.Message):
    text = message.text.strip()
    user = message.from_user.username or str(message.from_user.id)

    parsed = await parse_message(text)
    # Обробка часу: якщо "зараз" або пусто — підставляємо поточну дату й час Києва
    time_str = parsed.get('час', '').lower()
    if time_str == "зараз" or not time_str:
        now = datetime.datetime.now(KYIV_TZ)
        time_str = now.strftime("%d.%m.%Y %H:%M")
    # Формуємо рядок для таблиці
    row = [
        user,
        parsed.get('назва', ''),
        parsed.get('кількість', ''),
        time_str,
        text  # оригінальний текст
    ]
    sheet.append_row(row)
    await message.reply(
        f"✅ Додано в таблицю:\nНазва: {parsed.get('назва', '')}\nКількість: {parsed.get('кількість', '')}\nЧас: {time_str}"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
