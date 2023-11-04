import logging
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler
from mixin.veil_button_mixin import VeilButtonMixin

class MyVeilsHandler(VeilButtonMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'my_veils handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['my_veils']['hidden_start'] or
            event.message.message.startswith(self.button_messages['my_veils']['hidden_start'] + ' ')):
            data = self.parse_hidden_start(event.message.message)
            if data == None:
                user_status.state = 'home'
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                await self.goto_channel_reply_state(input_sender, 'home', data, user_status, db_connection)
        elif event.message.message == self.button_messages['my_veils']['back']:
            user_status.state = 'home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            if event.message.message == self.constant.persian.anonymous_name:
                user_status.veil = None
                user_status.state = 'my_veils'
                user_veils = await self.repository.veil.get_owned_veils(user_status.user_id, db_connection)
                user_veil_button_rows = self.create_veil_button_rows(user_veils)
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'my_veils', 'veil_changed', { 'veil': self.constant.persian.anonymous_name },
                                                       'my_veils', { 'button_messages': self.button_messages, 'veil_button_rows': user_veil_button_rows })
            else:
                veil = await self.repository.veil.get_veil(event.message.message, db_connection)
                if veil != None and veil.owned_by == user_status.user_id:
                    user_status.veil = veil.name
                    user_veils = await self.repository.veil.get_owned_veils(user_status.user_id, db_connection)
                    user_veil_button_rows = self.create_veil_button_rows(user_veils)
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'my_veils', 'veil_changed', { 'veil': veil.name },
                                                           'my_veils', { 'button_messages': self.button_messages, 'veil_button_rows': user_veil_button_rows })
                else:
                    user_veils = await self.repository.veil.get_owned_veils(user_status.user_id, db_connection)
                    user_veil_button_rows = self.create_veil_button_rows(user_veils)
                    await self.frontend.send_state_message(input_sender, 
                                                           'my_veils', 'no_such_veil', {},
                                                           'my_veils', { 'button_messages': self.button_messages, 'veil_button_rows': user_veil_button_rows })