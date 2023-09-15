import os

class Config:
    def __init__(self):
        self.app = Config.App()
        self.channel = Config.Channel()
        self.bot = Config.Bot()
        self.telegram = Config.Telegram()
        self.mysql = Config.Mysql()
    
    class App:
        def __init__(self):
            self.environment: str = os.getenv('APP_ENVIRONMENT')
            self.maintenance: str = (False if os.getenv('APP_MAINTENANCE') == '0' else True)

    class Channel:
        def __init__(self):
            self.id: str = os.getenv('CHANNEL_ID')
            self.admin: str = os.getenv('CHANNEL_ADMIN')

    class Bot:
        def __init__(self):
            self.id: str = os.getenv('BOT_ID')
            self.discard_media: bytes = bytes.fromhex(os.getenv('BOT_DISCARD_MEDIA'))
            self.new_reply_media: bytes = bytes.fromhex(os.getenv('BOT_NEW_REPLY_MEDIA'))

    class Telegram:
        def __init__(self):
            self.api_id: str = os.getenv('TELEGRAM_API_ID')
            self.api_hash: str = os.getenv('TELEGRAM_API_HASH')
            self.bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN')

    class Mysql:
        def __init__(self):
            self.db: str = os.getenv('MYSQL_DB')
            self.host: str = os.getenv('MYSQL_HOST')
            self.port: int = int(os.getenv('MYSQL_PORT'))
            self.user: str = os.getenv('MYSQL_USER')
            self.password: str = os.getenv('MYSQL_PASSWORD')
            self.pool_size: int = int(os.getenv('MYSQL_POOL_SIZE'))