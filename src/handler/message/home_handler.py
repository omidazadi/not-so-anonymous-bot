import logging
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler
from mixin.veil_button_mixin import VeilButtonMixin
from mixin.rate_limit_mixin import RateLimitMixin

class HomeHandler(VeilButtonMixin, RateLimitMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'home handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['home']['hidden_start'] or
            event.message.message.startswith(self.button_messages['home']['hidden_start'] + ' ')):
            data = self.parse_hidden_start(event.message.message)
            if data == None:
                await self.frontend.send_state_message(input_sender, 
                                                       'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                await self.goto_channel_reply_state(input_sender, 'home', data, user_status, db_connection)
        elif event.message.message == self.button_messages['home']['hidden_admin']:
            user_status.state = 'admin_auth'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'admin_auth', 'main', {},
                                                   'admin_auth', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['home']['unblock_all']:
            no_blocked_users = await self.repository.block.get_no_blocked_users(user_status.user_id, db_connection)
            user_status.state = 'unblock_all'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'unblock_all', 'main', { 'no_blocked_users': no_blocked_users },
                                                   'unblock_all', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['home']['talk_to_admin']:
            await self.frontend.send_state_message(input_sender, 
                                                   'home', 'talk_to_admin', { 'channel_admin': self.config.channel.admin },
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        elif event.message.message == self.button_messages['home']['my_veils']:
            if user_status.ticket > 0:
                if not await self.repository.veil.has_automatically_reserved_veils(user_status.user_id, db_connection):
                    await self.veil_manager.make_automatic_reservations(user_status, db_connection)
                    
                user_status.state = 'redeem_ticket'
                veil_buttons = await self.repository.veil.get_automatically_reserved_veils(user_status.user_id, db_connection)
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'redeem_ticket', 'main', {},
                                                       'redeem_ticket', { 'button_messages': self.button_messages, 'veil_buttons': veil_buttons })
            else:
                user_status.state = 'my_veils'
                user_veils = await self.repository.veil.get_owned_veils(user_status.user_id, db_connection)
                user_veil_button_rows = self.create_veil_button_rows(user_veils)
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'my_veils', 'main', { 'veils': user_veils, 'chosen_veil': user_status.veil },
                                                       'my_veils', { 'button_messages': self.button_messages, 'veil_button_rows': user_veil_button_rows })
        elif event.message.message == self.button_messages['home']['send_public']:
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'coming_soon', {},
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        elif event.message.message == self.button_messages['home']['send_anonymous']:
            if await self.is_member_of_channel(user_status):
                if not await self.is_rate_limited(user_status):
                    user_status.state = 'sending'
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'sending', 'main', {},
                                                           'sending', { 'button_messages': self.button_messages })
                else:
                    await self.frontend.send_state_message(input_sender, 
                                                           'home', 'slow_down', { 'wait': self.constant.limit.rate_limit },
                                                           'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                await self.frontend.send_state_message(input_sender, 
                                                       'common', 'must_be_a_member', { 'channel_id': self.config.channel.id },
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'unknown', {},
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
