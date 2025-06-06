import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
import gspread

# --- Секрети тільки через змінні середовища ---
TOKEN = os.environ["TELEGRAM_TOKEN"]
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '') + WEBHOOK_PATH
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

gc = gspread.service_account(filename='service_account.json')
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

logging.basicConfig(level=logging.INFO)

@dp.message_handler()
async def handle_message(message: types.Message):
    text = message.text.strip()
    user = message.from_user.username or str(message.from_user.id)
    row = [user, text]
    sheet.append_row(row)
    await message.reply(f"✅ Заніс у таблицю:\n{text}")

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
