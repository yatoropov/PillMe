import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
import gspread

# --- Налаштування ---
TOKEN = TELEGRAM_TOKEN
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '') + WEBHOOK_PATH
SPREADSHEET_ID = '1ponbZwTOObCwcx3pn2LtQ7jLFK5QKvKx5TF4b51ARrg'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# --- Google Sheets ---
gc = gspread.service_account(filename='service_account.json')
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

logging.basicConfig(level=logging.INFO)

# --- Базова логіка бота ---
@dp.message_handler()
async def handle_message(message: types.Message):
    text = message.text.strip()
    user = message.from_user.username or str(message.from_user.id)
    # Примітивний парсер: розбиваємо через кому (можна покращити потім)
    # Очікуємо: "Пульцет, 1, 12:00" або просто "Пульцет 1"
    row = [user, text]
    sheet.append_row(row)
    await message.reply(f"✅ Заніс у таблицю:\n{text}")

# --- Webhook старт ---
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
