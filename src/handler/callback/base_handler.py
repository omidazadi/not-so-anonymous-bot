from telethon import TelegramClient
from repository.repository import Repository
from frontend import Frontend
from config import Config
from constant import Constant
from participant_manager import ParticipantManager
from veil_manager import VeilManager

class BaseHandler:
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager):
        self.config: Config = config
        self.constant: Constant = constant
        self.telethon_bot: TelegramClient = telethon_bot
        self.button_messages = button_messages
        self.frontend: Frontend = frontend
        self.repository: Repository = repository
        self.participant_manager: ParticipantManager = participant_manager
        self.veil_manager: VeilManager = veil_manager