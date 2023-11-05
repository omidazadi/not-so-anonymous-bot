import logging
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler
from mixin.message_and_media_mixin import MessageAndMediaMixin

class DirectAdminMessagePhaseHandler(MessageAndMediaMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'direct_admin_message_phase handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['direct_admin_message_phase']['hidden_start'] or
            event.message.message.startswith(self.button_messages['direct_admin_message_phase']['hidden_start'] + ' ')):
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
        elif event.message.message == self.button_messages['direct_admin_message_phase']['discard']:
            user_status.state = 'admin_home'
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'direct_admin_message_phase', 'discard', {},
                                                   'admin_home', { 'button_messages': self.button_messages })
        else:
            (message, media) = await self.verify_message_and_media(event, 'admin_home', user_status, db_connection)
            if message == None and media == None:
                return
            
            reciever_status = await self.repository.user_status.get_user_status(int(user_status.extra), db_connection)
            input_reciever = await self.telethon_bot.get_input_entity(int(reciever_status.user_tid))
            message_tid = await self.frontend.send_inline_message(input_reciever, 'notification', 'direct_admin', 
                                                                  { 'message': message },
                                                                  {},
                                                                  media=media)
            
            if message_tid == None:
                user_status.state = 'admin_home'
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'common', 'i_am_blocked', {},
                                                       'admin_home', { 'button_messages': self.button_messages })
            else:
                user_status.state = 'admin_home'
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'direct_admin_message_phase', 'success', {},
                                                       'admin_home', { 'button_messages': self.button_messages })