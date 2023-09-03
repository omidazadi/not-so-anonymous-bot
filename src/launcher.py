import asyncio
import dotenv
import logging
import logging.config
from config import Config
from constant import Constant
from bot import Bot

dotenv.load_dotenv()

config = Config()
constant = Constant()

if config.app.environment == 'developement':
    logging.config.fileConfig(fname='src/logger.dev.conf', disable_existing_loggers=False)
elif config.app.environment == 'production':
    logging.config.fileConfig(fname='src/logger.prod.conf', disable_existing_loggers=False)
else:
    raise ValueError('Invalid `APP_ENVIRONMENT` value.')

async def main():
    bot = Bot(config, constant)
    await bot.initialize()
    await bot.start()

if __name__ == '__main__':
    asyncio.run(main())