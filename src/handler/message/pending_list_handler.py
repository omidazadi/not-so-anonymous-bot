import logging
import aiomysql
from telethon import TelegramClient
from model.user_status import UserStatus
from repository.user_status_repo import UserStatusRepo
from repository.channel_message_repo import ChannelMessageRepo
from neo_frontend import Frontend
from mixin.paginated_pending_list_mixin import PaginatedPendingListMixin
from config import Config
from constant import Constant

class PendingListHandler(PaginatedPendingListMixin):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, user_status_repo, channel_message_repo):
        self.logger = logging.getLogger('not_so_anonymous')
        self.config: Config = config
        self.constant: Constant = constant
        self.telethon_bot: TelegramClient = telethon_bot
        self.button_messages = button_messages
        self.frontend: Frontend = frontend
        self.user_status_repo: UserStatusRepo = user_status_repo
        self.channel_message_repo: ChannelMessageRepo = channel_message_repo
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'pending-list handler!')

        input_sender = event.message.input_sender
        if event.message.message == self.button_messages['pending_list']['hidden_start'] or \
            event.message.message == self.button_messages['pending_list']['back']:
            no_pending_messages = await self.channel_message_repo.get_no_pending_messages(db_connection)
            user_status.state = 'admin_home'
            user_status.extra = None
            await self.user_status_repo.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'admin_home', 'main', { 'no_pending_messages': no_pending_messages },
                                                   'admin_home', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['pending_list']['next']:
            user_status.extra = str(int(user_status.extra) + 1)
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.user_status_repo.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'pending_list', 'main', { 'current_page': int(user_status.extra), 'total_page': total_pages, 'preview_length': self.constant.view.pending_list_preview_length, 'messages': messages },
                                                   'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
        elif event.message.message == self.button_messages['pending_list']['previous']:
            user_status.extra = str(int(user_status.extra) - 1)
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.user_status_repo.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'pending_list', 'main', { 'current_page': int(user_status.extra), 'total_page': total_pages, 'preview_length': self.constant.view.pending_list_preview_length, 'messages': messages },
                                                   'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
        else:
            if event.message.message.isnumeric():
                channel_message_id = int(event.message.message)
                channel_message = await self.channel_message_repo.get_channel_message(channel_message_id, db_connection)
                if channel_message != None:
                    user_status.state = 'message_review'
                    user_status.extra = f'{str(channel_message.channel_message_id)},{user_status.extra}'
                    await self.user_status_repo.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                   'message_review', 'main', { 'user_status': user_status, 'message': channel_message.message },
                                                   'message_review', { 'button_messages': self.button_messages })
                else:
                    await self.frontend.send_state_message(input_sender, 
                                                   'pending_list', 'not_found', {},
                                                    None, None)
            else:
                await self.frontend.send_state_message(input_sender, 
                                                   'pending_list', 'not_found', {},
                                                    None, None)