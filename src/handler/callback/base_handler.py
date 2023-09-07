from telethon import TelegramClient
from repository.repository import Repository
from frontend import Frontend
from config import Config
from constant import Constant
from mixin.member_check_mixin import MemberCheckMixin

class BaseHandler(MemberCheckMixin):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository):
        self.config: Config = config
        self.constant: Constant = constant
        self.telethon_bot: TelegramClient = telethon_bot
        self.button_messages = button_messages
        self.frontend: Frontend = frontend
        self.repository: Repository = repository