import logging
import bcrypt
import aiomysql
from telethon import TelegramClient
from model.user_status import UserStatus
from repository.user_status_repo import UserStatusRepo
from repository.channel_message_repo import ChannelMessageRepo
from repository.admin_repo import AdminRepo
from frontend import Frontend
from config import Config
from constant import Constant

class AdminAuthHandler:
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, user_status_repo, channel_message_repo, admin_repo):
        self.logger = logging.getLogger('not_so_anonymous')
        self.config: Config = config
        self.constant: Constant = constant
        self.telethon_bot: TelegramClient = telethon_bot
        self.button_messages = button_messages
        self.frontend: Frontend = frontend
        self.user_status_repo: UserStatusRepo = user_status_repo
        self.channel_message_repo: ChannelMessageRepo = channel_message_repo
        self.admin_repo: AdminRepo = admin_repo
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'admin_auth handler!')

        input_sender = event.message.input_sender
        if event.message.message == self.button_messages['admin_auth']['hidden_start'] or \
            event.message.message == self.button_messages['admin_auth']['back']:
            user_status.state = 'home'
            await self.user_status_repo.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender,
                                                   'admin_auth', 'wink', {},
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            if user_status.gen_is_admin:
                admin = await self.admin_repo.get_admin(user_status.user_tid, db_connection)
                if bcrypt.checkpw(bytes(event.message.message, 'utf-8'), bytes(admin.password_hash, encoding='utf-8')):
                    no_pending_messages = await self.channel_message_repo.get_no_pending_messages(db_connection)
                    user_status.state = 'admin_home'
                    await self.user_status_repo.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'admin_auth', 'correct', {},
                                                           None, None)
                    await self.frontend.send_state_message(input_sender, 
                                                           'admin_home', 'main', { 'no_pending_messages': no_pending_messages },
                                                           'admin_home', { 'button_messages': self.button_messages })
                else:
                    user_status.state = 'home'
                    await self.user_status_repo.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'admin_auth', 'incorrect', {},
                                                           'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                user_status.state = 'home'
                await self.user_status_repo.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'admin_auth', 'incorrect', {},
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })