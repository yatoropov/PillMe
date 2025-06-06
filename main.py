import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
import gspread
from dotenv import load_dotenv
import openai

# Завантажити .env змінні
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Google Sheets ініціалізація
gc = gspread.service_account(filename='service_account.json')
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# OpenAI клієнт
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
    # Синхронний клієнт — обгортаємо через asyncio.to_thread
    resp = await asyncio.to_thread(
        openai_client.chat.completions.create,
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=100,
    )
    answer = resp.choices[0].message.content
    # Парсимо ключ:значення
    result = {}
    for line in answer.split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            result[k.strip().lower()] = v.strip()
    return result

@dp.message(F.text)
async def handle_message(message: types.Message):
    text = message.text.strip()
    user = message.from_user.username or str(message.from_user.id)

    parsed = await parse_message(text)
    # Формуємо рядок для таблиці
    row = [
        user,
        parsed.get('назва', ''),
        parsed.get('кількість', ''),
        parsed.get('час', ''),
        text  # оригінальний текст
    ]
    sheet.append_row(row)
    await message.reply(
        f"✅ Додано в таблицю:\nНазва: {parsed.get('назва', '')}\nКількість: {parsed.get('кількість', '')}\nЧас: {parsed.get('час', '')}"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
