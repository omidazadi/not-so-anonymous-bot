import logging
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler

class DirectAdminIdPhaseHandler(BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'direct_admin_id_phase handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['direct_admin_id_phase']['hidden_start'] or
            event.message.message.startswith(self.button_messages['direct_admin_id_phase']['hidden_start'] + ' ')):
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
        elif event.message.message == self.button_messages['direct_admin_id_phase']['discard']:
            user_status.state = 'admin_home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'direct_admin_id_phase', 'discard', {},
                                                   'admin_home', { 'button_messages': self.button_messages })
        else:
            if event.message.message.isnumeric():
                if await self.repository.user_status.get_user_status(int(event.message.message), db_connection) == None:
                    user_status.state = 'admin_home'
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'direct_admin_id_phase', 'no_such_user', {},
                                                           'admin_home', { 'button_messages': self.button_messages })
                    return

                user_status.state = 'direct_admin_message_phase'
                user_status.extra = f'{event.message.message}'
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'direct_admin_message_phase', 'main', {},
                                                       'direct_admin_message_phase', { 'button_messages': self.button_messages })
            else:
                user_status.state = 'admin_home'
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'direct_admin_id_phase', 'no_such_user', {},
                                                       'admin_home', { 'button_messages': self.button_messages })