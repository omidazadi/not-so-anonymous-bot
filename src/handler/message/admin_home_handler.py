import logging
import aiomysql
from model.user_status import UserStatus
from mixin.paginated_pending_list_mixin import PaginatedPendingListMixin
from handler.message.base_handler import BaseHandler
from mixin.reciever_mixin import RecieverMixin

class AdminHomeHandler(PaginatedPendingListMixin, RecieverMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'admin_home handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['admin_home']['hidden_start'] or
            event.message.message.startswith(self.button_messages['admin_home']['hidden_start'] + ' ')):
            data = self.parse_hidden_start(event.message.message)
            if data == None:
                no_pending_messages = await self.repository.channel_message.get_no_pending_messages(db_connection)
                no_reports = await self.repository.peer_message.get_no_reports(db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'admin_home', 'main', { 'no_pending_messages': no_pending_messages, 'no_reports': no_reports },
                                                       'admin_home', { 'button_messages': self.button_messages })
            else:
                await self.goto_channel_reply_state(input_sender, 'admin_home', data, user_status, db_connection)
        elif event.message.message == self.button_messages['admin_home']['refresh']:
            no_pending_messages = await self.repository.channel_message.get_no_pending_messages(db_connection)
            no_reports = await self.repository.peer_message.get_no_reports(db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'admin_home', 'main', { 'no_pending_messages': no_pending_messages, 'no_reports': no_reports },
                                                   'admin_home', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['admin_home']['veil_menu']:
            user_status.state = 'veil_menu'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'veil_menu', 'main', {},
                                                   'veil_menu', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['admin_home']['ban_menu']:
            user_status.state = 'ban_menu'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'ban_menu', 'main', {},
                                                   'ban_menu', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['admin_home']['show_report']:
            peer_message = await self.repository.peer_message.get_a_report(db_connection)
            if peer_message == None:
                await self.frontend.send_state_message(input_sender, 
                                                       'admin_home', 'no_report', {},
                                                       'admin_home', { 'button_messages': self.button_messages })
            else:
                (reciever_status, message_tid) = await self.get_reciever(peer_message, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'admin_home', 'show_report', { 'reporter': reciever_status.user_id, 'reportee': peer_message.from_user, 'message': peer_message.message},
                                                       'admin_home', { 'button_messages': self.button_messages },
                                                       media=peer_message.media)
                await self.repository.peer_message.review_report(peer_message.peer_message_id, db_connection) 
        elif event.message.message == self.button_messages['admin_home']['direct_admin']:
            user_status.state = 'direct_admin_id_phase'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'direct_admin_id_phase', 'main', {},
                                                   'direct_admin_id_phase', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['admin_home']['hidden_omidi']:
            await self.frontend.send_state_message(input_sender, 
                                                   'admin_home', 'omidi', {},
                                                   'admin_home', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['admin_home']['exit']:
            user_status.state = 'home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        elif event.message.message == self.button_messages['admin_home']['pending_list']:
            user_status.state = 'pending_list'
            user_status.extra = '1'
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'pending_list', 'main', { 'current_page': int(user_status.extra), 'total_page': total_pages, 'preview_length': self.constant.view.pending_list_preview_length, 'messages': messages },
                                                   'pending_list', { 'button_messages': self.button_messages, 'messages': messages })
        else:
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'unknown', {},
                                                   'admin_home', { 'button_messages': self.button_messages })