import logging
from telethon import TelegramClient
from config import Config
from constant import Constant
from model.user_status import UserStatus

class ParticipantManager:
    def __init__(self, telethon_bot: TelegramClient, config: Config, constant: Constant):
        self.logger = logging.getLogger('not_so_anonymous')
        self.telethon_bot = telethon_bot
        self.config = config
        self.constant = constant
        self.participants = set()

    async def initialize(self):
        self.participants = set()
        async for user in self.telethon_bot.iter_participants(self.config.channel.id):
            self.participants.add(user.id)
    
    def add_participant(self, user_tid):
        self.participants.add(user_tid)

    def remove_participant(self, user_tid):
        self.participants.remove(user_tid)

    def is_a_member(self, user_status: UserStatus):
        return True if int(user_status.user_tid) in self.participants else False
    