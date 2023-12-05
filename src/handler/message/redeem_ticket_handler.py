import logging
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler
from mixin.veil_button_mixin import VeilButtonMixin

class RedeemTicketHandler(VeilButtonMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'redeem_ticket handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['redeem_ticket']['hidden_start'] or
            event.message.message.startswith(self.button_messages['redeem_ticket']['hidden_start'] + ' ')):
            reply_type, channel_message_id_str = self.parse_hidden_start(event.message.message)
            if reply_type == None:
                user_status.state = 'home'
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                await self.goto_channel_reply_state(input_sender, 'home', channel_message_id_str, reply_type, user_status, db_connection)
        elif event.message.message == self.button_messages['redeem_ticket']['back']:
            user_status.state = 'home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            veil = await self.repository.veil.get_veil(event.message.message, db_connection)
            if veil != None and veil.reservation_status == 'automatically_reserved' and veil.reserved_by == user_status.user_id:
                await self.veil_manager.acquire_automatically_reserved_veil(user_status, veil, db_connection)
                user_status.ticket -= 1
                if user_status.ticket > 0:
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
            else:
                user_status.state = 'redeem_ticket'
                veil_buttons = await self.repository.veil.get_automatically_reserved_veils(user_status.user_id, db_connection)
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'redeem_ticket', 'no_such_veil', {},
                                                       'redeem_ticket', { 'button_messages': self.button_messages, 'veil_buttons': veil_buttons })