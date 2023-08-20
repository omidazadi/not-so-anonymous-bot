import os
import asyncio
import dotenv
import logging
import logging.config
from bot import Bot

dotenv.load_dotenv()
environment = os.getenv('ENVIRONMENT')
if environment == 'developement':
    logging.config.fileConfig(fname='src/logger.dev.conf', disable_existing_loggers=False)
elif environment == 'production':
    logging.config.fileConfig(fname='src/logger.prod.conf', disable_existing_loggers=False)
else:
    raise ValueError

async def main():
    api_id, api_hash, bot_token, channel_id, pending_page_size, pending_preview_length, \
        mysql_db, mysql_host, mysql_port, mysql_user, mysql_password, limit_anonymous_gap, \
        limit_simple_message_size, limit_media_message_size = \
        os.getenv('TELEGRAM_API_ID'), os.getenv('TELEGRAM_API_HASH'), os.getenv('TELEGRAM_BOT_TOKEN'), \
        os.getenv('CHANNEL_ID'), int(os.getenv('PENDING_PAGE_SIZE')), int(os.getenv('PENDING_PREVIEW_LENGTH')), \
        os.getenv('MYSQL_DB'), os.getenv('MYSQL_HOST'), int(os.getenv('MYSQL_PORT')), os.getenv('MYSQL_USER'), \
        os.getenv('MYSQL_PASSWORD'), int(os.getenv('LIMIT_ANONYMOUS_GAP')), int(os.getenv('LIMIT_SIMPLE_MESSAGE_SIZE')), \
        int(os.getenv('LIMIT_MEDIA_MESSAGE_SIZE'))
    bot = Bot()
    await bot.initialize(api_id, api_hash, bot_token, channel_id, pending_page_size, pending_preview_length, 
                         mysql_db, mysql_host, mysql_port, mysql_user, mysql_password, limit_anonymous_gap, 
                         limit_simple_message_size, limit_media_message_size)
    await bot.start()

if __name__ == '__main__':
    asyncio.run(main())