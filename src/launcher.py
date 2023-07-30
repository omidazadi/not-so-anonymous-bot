import os
import asyncio
import dotenv
import logging
import logging.config
import bcrypt
from bot import Bot
from telethon import TelegramClient, events

dotenv.load_dotenv()
logging.config.fileConfig(fname='src/logger.conf', disable_existing_loggers=False)

async def main():
    api_id, api_hash, bot_token, channel_id, admin_password_hash, pending_page_size, pending_preview_length, \
        sqlite_db, security_rate_limit = \
        os.getenv('TELEGRAM_API_ID'), os.getenv('TELEGRAM_API_HASH'), os.getenv('TELEGRAM_BOT_TOKEN'), \
        os.getenv('CHANNEL_ID'), os.getenv('ADMIN_PASSWORD_HASH'), os.getenv('PENDING_PAGE_SIZE'), \
        os.getenv('PENDING_PREVIEW_LENGTH'), os.getenv('SQLITE_DB'), os.getenv('SECURITY_RATE_LIMIT')
    bot = Bot()
    await bot.initialize(api_id, api_hash, bot_token, channel_id, bytes(admin_password_hash, encoding='utf-8'), \
                         int(pending_page_size), int(pending_preview_length), sqlite_db, int(security_rate_limit))
    await bot.start()

if __name__ == '__main__':
    asyncio.run(main())