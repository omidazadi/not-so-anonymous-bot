import logging
import bcrypt
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler

class AdminAuthHandler(BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'admin_auth handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['admin_auth']['hidden_start'] or
            event.message.message.startswith(self.button_messages['admin_auth']['hidden_start'] + ' ')):
            data = self.parse_hidden_start(event.message.message)
            if data == None:
                user_status.state = 'home'
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                await self.goto_channel_reply_state(input_sender, 'home', data, user_status, db_connection)
        elif event.message.message == self.button_messages['admin_auth']['back']:
            user_status.state = 'home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender,
                                                   'admin_auth', 'wink', {},
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            if user_status.gen_is_admin:
                admin = await self.repository.admin.get_admin(user_status.user_tid, db_connection)
                if bcrypt.checkpw(bytes(event.message.message, 'utf-8'), bytes(admin.password_hash, encoding='utf-8')):
                    no_pending_messages = await self.repository.channel_message.get_no_pending_messages(db_connection)
                    no_reports = await self.repository.peer_message.get_no_reports(db_connection)
                    user_status.state = 'admin_home'
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'admin_auth', 'correct', {},
                                                           None, None)
                    await self.frontend.send_state_message(input_sender, 
                                                           'admin_home', 'main', { 'no_pending_messages': no_pending_messages, 'no_reports': no_reports },
                                                           'admin_home', { 'button_messages': self.button_messages })
                else:
                    user_status.state = 'home'
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'admin_auth', 'incorrect', {},
                                                           'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                user_status.state = 'home'
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'admin_auth', 'incorrect', {},
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })