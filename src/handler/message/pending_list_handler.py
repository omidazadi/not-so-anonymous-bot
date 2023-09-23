import logging
import aiomysql
from model.user_status import UserStatus
from mixin.paginated_pending_list_mixin import PaginatedPendingListMixin
from handler.message.base_handler import BaseHandler

class PendingListHandler(PaginatedPendingListMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'pending_list handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['pending_list']['hidden_start'] or
            event.message.message.startswith(self.button_messages['pending_list']['hidden_start'] + ' ')):
            data = self.parse_hidden_start(event.message.message)
            if data == None:
                no_pending_messages = await self.repository.channel_message.get_no_pending_messages(db_connection)
                no_reports = await self.repository.peer_message.get_no_reports(db_connection)
                user_status.state = 'admin_home'
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'admin_home', 'main', { 'no_pending_messages': no_pending_messages, 'no_reports': no_reports },
                                                       'admin_home', { 'button_messages': self.button_messages })
            else:
                await self.goto_channel_reply_state(input_sender, 'admin_home', data, user_status, db_connection)
        elif event.message.message == self.button_messages['pending_list']['back']:
            no_pending_messages = await self.repository.channel_message.get_no_pending_messages(db_connection)
            no_reports = await self.repository.peer_message.get_no_reports(db_connection)
            user_status.state = 'admin_home'
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'admin_home', 'main', { 'no_pending_messages': no_pending_messages, 'no_reports': no_reports },
                                                   'admin_home', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['pending_list']['next']:
            user_status.extra = str(int(user_status.extra) + 1)
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'pending_list', 'main', { 'current_page': int(user_status.extra), 'total_page': total_pages, 'preview_length': self.constant.view.pending_list_preview_length, 'messages': messages },
                                                   'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
        elif event.message.message == self.button_messages['pending_list']['previous']:
            user_status.extra = str(int(user_status.extra) - 1)
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'pending_list', 'main', { 'current_page': int(user_status.extra), 'total_page': total_pages, 'preview_length': self.constant.view.pending_list_preview_length, 'messages': messages },
                                                   'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
        else:
            if event.message.message.isnumeric():
                channel_message_id = int(event.message.message)
                channel_message = await self.repository.channel_message.get_channel_message(channel_message_id, db_connection)
                if channel_message != None:
                    user_status.state = 'message_review'
                    user_status.extra = f'{str(channel_message.channel_message_id)},{user_status.extra}'
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'message_review', 'main', { 'message': channel_message },
                                                           'message_review', { 'button_messages': self.button_messages },
                                                            media=channel_message.media)
                else:
                    messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'pending_list', 'not_found', {},
                                                           'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
            else:
                messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'common', 'not_found', {},
                                                       'pending_list', { 'button_messages': self.button_messages, 'messages': messages })