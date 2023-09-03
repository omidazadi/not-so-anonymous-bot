from datetime import datetime
import logging
import aiomysql
from telethon import TelegramClient
from telethon.hints import EntityLike
from model.user_status import UserStatus
from repository.user_status_repo import UserStatusRepo
from neo_frontend import Frontend
from config import Config
from constant import Constant

class HomeHandler:
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, user_status_repo):
        self.logger = logging.getLogger('not_so_anonymous')
        self.config: Config = config
        self.constant: Constant = constant
        self.telethon_bot: TelegramClient = telethon_bot
        self.button_messages = button_messages
        self.frontend: Frontend = frontend
        self.user_status_repo: UserStatusRepo = user_status_repo
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'home handler!')

        input_sender = event.message.input_sender
        if event.message.message == self.button_messages['home']['hidden_start']:
            await self.frontend.send_state_message(input_sender, 
                                                   'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        elif event.message.message == self.button_messages['home']['hidden_admin']:
            user_status.state = 'admin_auth'
            await self.user_status_repo.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'admin_auth', 'main', {},
                                                   'admin_auth', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['home']['talk_to_admin']:
            await self.frontend.send_state_message(input_sender, 
                                                   'home', 'talk_to_admin', { 'channel_admin': self.config.channel.admin },
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        elif event.message.message == self.button_messages['home']['send_message']:
            sender = await self.telethon_bot.get_entity(event.message.input_sender)
            if await self.is_member_of_channel(sender):
                if not await self.is_rate_limited(user_status):
                    user_status.state = 'sending'
                    await self.user_status_repo.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'sending', 'main', {},
                                                           'sending', { 'button_messages': self.button_messages })
                else:
                    await self.frontend.send_state_message(input_sender, 
                                                           'home', 'slow_down', { 'wait': self.constant.limit.rate_limit },
                                                           'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                await self.frontend.send_state_message(input_sender, 
                                                       'home', 'must_be_a_member', { 'channel_id': self.config.channel.id },
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'unknown', {},
                                                   None, None)

    async def is_rate_limited(self, user_status: UserStatus):
        if user_status.last_message_at == None:
            return False
        now = datetime.utcnow()
        time_passed = now - user_status.last_message_at
        if time_passed.total_seconds() < self.constant.limit.rate_limit:
            return True
        return False

    async def is_member_of_channel(self, sender: EntityLike):
        input_channel = await self.telethon_bot.get_input_entity(self.config.channel.id)
        async for user in self.telethon_bot.iter_participants(input_channel, search=sender.first_name):
            if user.id == sender.id:
                return True
        return False