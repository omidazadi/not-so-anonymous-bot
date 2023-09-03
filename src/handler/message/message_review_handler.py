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

class MessageReviewHandler(PaginatedPendingListMixin):
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
        self.logger.info(f'message-review handler!')

        input_sender = event.message.input_sender
        if event.message.message == self.button_messages['message_review']['hidden_start']:
            no_pending_messages = await self.channel_message_repo.get_no_pending_messages(db_connection)
            user_status.state = 'admin_home'
            user_status.extra = None
            await self.user_status_repo.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'admin_home', 'main', { 'no_pending_messages': no_pending_messages },
                                                   'admin_home', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['message_review']['back']:
            user_status.state = 'pending_list'
            user_status.extra = user_status.extra.split(',')[1]
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.user_status_repo.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'pending_list', 'main', { 'current_page': int(user_status.extra), 'total_page': total_pages, 'preview_length': self.constant.view.pending_list_preview_length, 'messages': messages },
                                                   'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
        elif event.message.message == self.button_messages['message_review']['accept']:
            channel_message_id = int(user_status.extra.split(',')[0])
            is_ok = await self.channel_message_repo.set_channel_message_verdict('a', user_status.user_id, channel_message_id, db_connection)
            user_status.state = 'pending_list'
            user_status.extra = user_status.extra.split(',')[1]
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.user_status_repo.set_user_status(user_status, db_connection)

            if is_ok:
                await self.frontend.send_state_message(input_sender, 
                                                       'message_review', 'accept', {},
                                                       None, None)
                await self.frontend.send_state_message(input_sender, 
                                                       'pending_list', 'main', { 'current_page': int(user_status.extra), 'total_page': total_pages, 'preview_length': self.constant.view.pending_list_preview_length, 'messages': messages },
                                                       'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
                await self.send_to_channel(channel_message_id, user_status, db_connection)
            else:
                await self.frontend.send_state_message(input_sender, 
                                                       'message_review', 'not_found', {},
                                                       None, None)
                await self.frontend.send_state_message(input_sender, 
                                                       'pending_list', 'main', { 'current_page': int(user_status.extra), 'total_page': total_pages, 'preview_length': self.constant.view.pending_list_preview_length, 'messages': messages },
                                                       'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
        elif event.message.message == self.button_messages['message_review']['reject']:
            channel_message_id = int(user_status.extra.split(',')[0])
            is_ok = await self.channel_message_repo.set_channel_message_verdict('r', user_status.user_id, channel_message_id, db_connection)
            user_status.state = 'pending_list'
            user_status.extra = user_status.extra.split(',')[1]
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.user_status_repo.set_user_status(user_status, db_connection)

            if is_ok:
                await self.frontend.send_state_message(input_sender, 
                                                       'message_review', 'accept', {},
                                                       None, None)
                await self.frontend.send_state_message(input_sender, 
                                                       'pending_list', 'main', { 'current_page': int(user_status.extra), 'total_page': total_pages, 'preview_length': self.constant.view.pending_list_preview_length, 'messages': messages },
                                                       'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
            else:
                await self.frontend.send_state_message(input_sender, 
                                                       'message_review', 'not_found', {},
                                                       None, None)
                await self.frontend.send_state_message(input_sender, 
                                                       'pending_list', 'main', { 'current_page': int(user_status.extra), 'total_page': total_pages, 'preview_length': self.constant.view.pending_list_preview_length, 'messages': messages },
                                                       'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
        else:
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'unknown', {},
                                                   None, None)

    async def send_to_channel(self, channel_message_id, user_status: UserStatus, db_connection: aiomysql.Connection):
        channel_message = await self.channel_message_repo.get_channel_message(channel_message_id, db_connection)
        sender_user_status = await self.user_status_repo.get_user_status(channel_message.from_user, db_connection)
        input_sender = await self.telethon_bot.get_input_entity(int(sender_user_status.user_tid))
        await self.frontend.edit_inline_message(input_sender, channel_message.message_tid, 'channel_message_preview', 'approved', 
                                                { 'user_status': user_status, 'message': channel_message.message },
                                                { 'channel_message_id': channel_message.channel_message_id })
        await self.frontend.send_inline_message(input_sender, 'channel_message_approved_notification', 'notification', 
                                                {},
                                                {},
                                                reply_to=channel_message.message_tid)

        input_channel = await self.telethon_bot.get_input_entity(self.channel_id)
        await self.frontend.send_to_channel(input_channel, channel_message, user_status)