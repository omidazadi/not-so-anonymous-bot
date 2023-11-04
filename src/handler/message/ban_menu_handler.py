import logging
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler

class BanMenuHandler(BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'ban_menu handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['ban_menu']['hidden_start'] or
            event.message.message.startswith(self.button_messages['ban_menu']['hidden_start'] + ' ')):
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
        elif event.message.message == self.button_messages['ban_menu']['back']:
            no_pending_messages = await self.repository.channel_message.get_no_pending_messages(db_connection)
            no_reports = await self.repository.peer_message.get_no_reports(db_connection)
            user_status.state = 'admin_home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'admin_home', 'main', { 'no_pending_messages': no_pending_messages, 'no_reports': no_reports },
                                                   'admin_home', { 'button_messages': self.button_messages })
        else:
            '''
            error_codes:
            0: success
            1: invalid command
            2: ban not successful
            3: unban not successful
            '''
            command: str = event.message.message
            intermediate_parse = command.strip().split(' ')
            tokens, error_code = [token for token in intermediate_parse if token != ''], 0
            
            if tokens[0] == 'ban':
                if len(tokens) != 2 or not tokens[1].isnumeric():
                    error_code = 1
                else:
                    user_id = int(tokens[1])
                    is_ok = await self.repository.user_status.ban_user(user_id, db_connection)
                    if is_ok:
                        await self.frontend.send_state_message(input_sender, 
                                                               'ban_menu', 'ban_successful', {},
                                                               'ban_menu', { 'button_messages': self.button_messages })
                    else:
                        error_code = 2
            elif tokens[0] == 'unban':
                if len(tokens) != 2 or not tokens[1].isnumeric():
                    error_code = 1
                else:
                    user_id = int(tokens[1])
                    is_ok = await self.repository.user_status.unban_user(user_id, db_connection)
                    if is_ok:
                        await self.frontend.send_state_message(input_sender, 
                                                               'ban_menu', 'unban_successful', {},
                                                               'ban_menu', { 'button_messages': self.button_messages })
                    else:
                        error_code = 3
            elif tokens[0] == 'list':
                if len(tokens) != 1:
                    error_code = 1
                else:
                    banned_users = await self.repository.user_status.get_all_banned_users(db_connection)
                    list_str = ' '.join([str(banned_user.user_id) for banned_user in banned_users])
                    await self.frontend.send_state_message(input_sender, 
                                                           'ban_menu', 'list', { 'list_str': list_str },
                                                           'ban_menu', { 'button_messages': self.button_messages })
            else:
                error_code = 1

            if error_code == 1:
                await self.frontend.send_state_message(input_sender, 
                                                       'ban_menu', 'invalid_command', {},
                                                       'ban_menu', { 'button_messages': self.button_messages })
            elif error_code == 2:
                await self.frontend.send_state_message(input_sender, 
                                                       'ban_menu', 'ban_not_successful', {},
                                                       'ban_menu', { 'button_messages': self.button_messages })
            elif error_code == 3:
                await self.frontend.send_state_message(input_sender, 
                                                       'ban_menu', 'unban_not_successful', {},
                                                       'ban_menu', { 'button_messages': self.button_messages })
            

