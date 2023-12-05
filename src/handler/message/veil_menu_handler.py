import logging
import io
import csv
import aiomysql
from model.user_status import UserStatus
from model.veil import Veil
from handler.message.base_handler import BaseHandler

class VeilMenuHandler(BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'veil_menu handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['veil_menu']['hidden_start'] or
            event.message.message.startswith(self.button_messages['veil_menu']['hidden_start'] + ' ')):
            reply_type, channel_message_id_str = self.parse_hidden_start(event.message.message)
            if reply_type == None:
                no_pending_messages = await self.repository.channel_message.get_no_pending_messages(db_connection)
                no_reports = ((await self.repository.peer_message.get_no_reports(db_connection)) + 
                              (await self.repository.answer_message.get_no_reports(db_connection)))
                user_status.state = 'admin_home'
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'admin_home', 'main', { 'no_pending_messages': no_pending_messages, 'no_reports': no_reports },
                                                       'admin_home', { 'button_messages': self.button_messages })
            else:
                await self.goto_channel_reply_state(input_sender, 'admin_home', channel_message_id_str, reply_type, user_status, db_connection)
        elif event.message.message == self.button_messages['veil_menu']['back']:
            no_pending_messages = await self.repository.channel_message.get_no_pending_messages(db_connection)
            no_reports = ((await self.repository.peer_message.get_no_reports(db_connection)) + 
                          (await self.repository.answer_message.get_no_reports(db_connection)))
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
            2: command not successful
            '''
            command: str = event.message.message
            tokens, error_code = self.extract_tokens(command), 0
            
            if tokens[0] == 'veil':
                if len(tokens) == 1:
                    error_code = 1
                else:
                    if tokens[1] == 'craft':
                        if len(tokens) != 4 or (tokens[2] not in ['masculine', 'feminine', 'neutral']) or not self.is_quoted(tokens[3]):
                            error_code = 1
                        else:
                            is_ok = await self.repository.veil.craft_veil(self.remove_quotation_marks(tokens[3]), tokens[2], db_connection)
                            if not is_ok:
                                error_code = 2
                            else:
                                await self.frontend.send_state_message(input_sender, 
                                                                       'veil_menu', 'veil_craft_successful', {},
                                                                       'veil_menu', { 'button_messages': self.button_messages })

                    elif tokens[1] == 'modify':
                        if len(tokens) != 5 or not self.is_quoted(tokens[2]) or tokens[3] != 'to' or not self.is_quoted(tokens[4]):
                            error_code = 1
                        else:
                            is_ok = await self.repository.veil.modify_veil(self.remove_quotation_marks(tokens[2]), self.remove_quotation_marks(tokens[4]), db_connection)
                            if not is_ok:
                                error_code = 2
                            else:
                                await self.frontend.send_state_message(input_sender, 
                                                                       'veil_menu', 'veil_modify_successful', {},
                                                                       'veil_menu', { 'button_messages': self.button_messages })
                    
                    elif tokens[1] == 'destroy':
                        if len(tokens) != 3 or not self.is_quoted(tokens[2]):
                            error_code = 1
                        else:
                            is_ok = await self.repository.veil.destroy_veil(self.remove_quotation_marks(tokens[2]), db_connection)
                            if not is_ok:
                                error_code = 2 
                            else:
                                await self.frontend.send_state_message(input_sender, 
                                                                       'veil_menu', 'veil_delete_successful', {},
                                                                       'veil_menu', { 'button_messages': self.button_messages })

                    elif tokens[1] == 'reserve':
                        if len(tokens) != 3 or not self.is_quoted(tokens[2]):
                            error_code = 1
                        else:
                            is_ok = await self.repository.veil.manually_reserve_veil(self.remove_quotation_marks(tokens[2]), db_connection)
                            if not is_ok:
                                error_code = 2 
                            else:
                                await self.frontend.send_state_message(input_sender, 
                                                                       'veil_menu', 'veil_reserve_successful', {},
                                                                       'veil_menu', { 'button_messages': self.button_messages })

                    elif tokens[1] == 'free':
                        if len(tokens) != 3 or not self.is_quoted(tokens[2]):
                            error_code = 1
                        else:
                            is_ok = await self.repository.veil.free_veil(self.remove_quotation_marks(tokens[2]), db_connection)
                            if not is_ok:
                                error_code = 2 
                            else:
                                is_ok = await self.repository.user_status.take_veil_back(self.remove_quotation_marks(tokens[2]), db_connection)
                                if not is_ok:
                                    error_code = 2 
                                else:
                                    await self.frontend.send_state_message(input_sender, 
                                                                           'veil_menu', 'veil_free_successful', {},
                                                                           'veil_menu', { 'button_messages': self.button_messages })
                    
                    elif tokens[1] == 'gift':
                        if len(tokens) != 5 or not self.is_quoted(tokens[2]) or tokens[3] != 'to' or not tokens[4].isnumeric():
                            error_code = 1
                        else:
                            veil = await self.repository.veil.get_veil(self.remove_quotation_marks(tokens[2]), db_connection)
                            reciever_status = await self.repository.user_status.get_user_status(int(tokens[4]), db_connection)
                            if veil == None or reciever_status == None:
                                error_code = 2
                            else:
                                input_reciever = await self.telethon_bot.get_input_entity(int(reciever_status.user_tid))
                                await self.veil_manager.acquire_veil(reciever_status, veil, db_connection)
                                await self.frontend.send_inline_message(input_reciever, 'notification', 'got_a_veil', 
                                                                        { 'veil': veil },
                                                                        {})
                                await self.frontend.send_state_message(input_sender, 
                                                                       'veil_menu', 'veil_gift_successful', {},
                                                                       'veil_menu', { 'button_messages': self.button_messages })
                    else:
                        error_code = 1

            elif tokens[0] == 'ticket':
                if len(tokens) == 1:
                    error_code = 1
                else:
                    if tokens[1] == 'gift':
                        if len(tokens) != 3 or not tokens[2].isnumeric():
                            error_code = 1
                        else:
                            reciever_status = await self.repository.user_status.get_user_status(int(tokens[2]), db_connection)
                            input_reciever = await self.telethon_bot.get_input_entity(int(reciever_status.user_tid))
                            reciever_status.ticket += 1
                            print(reciever_status.user_id, reciever_status.ticket)
                            await self.repository.user_status.set_user_status(reciever_status, db_connection)
                            await self.frontend.send_inline_message(input_reciever, 'notification', 'got_a_ticket', 
                                                                    {},
                                                                    {})
                            await self.frontend.send_state_message(input_sender, 
                                                                   'veil_menu', 'ticket_gift_successful', {},
                                                                   'veil_menu', { 'button_messages': self.button_messages })
                    
                    elif tokens[1] == 'giveaway':
                        if len(tokens) != 3 or not tokens[2].isnumeric():
                            error_code = 1
                        else:
                            winners = await self.veil_manager.giveaway_tickets(int(tokens[2]), db_connection)
                            for winner in winners:
                                input_reciever = await self.telethon_bot.get_input_entity(int(winner.user_tid))
                                await self.frontend.send_inline_message(input_reciever, 'notification', 'got_a_ticket', 
                                                                        {},
                                                                        {})
                            await self.frontend.send_state_message(input_sender, 
                                                                   'veil_menu', 'ticket_giveaway_successful', { 'no_tickets': len(winners) },
                                                                   'veil_menu', { 'button_messages': self.button_messages })
                    else:
                        error_code = 1
            elif tokens[0] == 'search':
                if len(tokens) == 1:
                    error_code = 1
                else:
                    if tokens[1] == 'veil':
                        if tokens[2] == 'status' and len(tokens) == 4:
                            if tokens[3] == 'all':
                                veils = await self.repository.veil.get_all_veils(db_connection)
                                await self.frontend.send_state_message_as_xlsx(input_sender, 
                                                                              'veil_menu', 'veils_csv', { 'csv': self.veils_to_csv(veils) },
                                                                              'veil_menu', { 'button_messages': self.button_messages })
                            elif tokens[3] == 'free':
                                veils = await self.repository.veil.get_veil_by_reservation_status('free', db_connection)
                                await self.frontend.send_state_message_as_xlsx(input_sender, 
                                                                              'veil_menu', 'veils_csv', { 'csv': self.veils_to_csv(veils) },
                                                                              'veil_menu', { 'button_messages': self.button_messages })
                            elif tokens[3] == 'manually_reserved':
                                veils = await self.repository.veil.get_veil_by_reservation_status('manually_reserved', db_connection)
                                await self.frontend.send_state_message_as_xlsx(input_sender, 
                                                                              'veil_menu', 'veils_csv', { 'csv': self.veils_to_csv(veils) },
                                                                              'veil_menu', { 'button_messages': self.button_messages })
                            elif tokens[3] == 'automatically_reserved':
                                veils = await self.repository.veil.get_veil_by_reservation_status('automatically_reserved', db_connection)
                                await self.frontend.send_state_message_as_xlsx(input_sender, 
                                                                              'veil_menu', 'veils_csv', { 'csv': self.veils_to_csv(veils) },
                                                                              'veil_menu', { 'button_messages': self.button_messages })
                            elif tokens[3] == 'taken':
                                veils = await self.repository.veil.get_veil_by_reservation_status('taken', db_connection)
                                await self.frontend.send_state_message_as_xlsx(input_sender, 
                                                                              'veil_menu', 'veils_csv', { 'csv': self.veils_to_csv(veils) },
                                                                              'veil_menu', { 'button_messages': self.button_messages })
                            else:
                                error_code = 1
                        elif self.is_quoted(tokens[2]) and len(tokens) == 3:
                            veil = await self.repository.veil.get_veil(self.remove_quotation_marks(tokens[2]), db_connection)
                            if veil == None:
                                error_code = 2
                            else:
                                await self.frontend.send_state_message_as_xlsx(input_sender, 
                                                                              'veil_menu', 'veils_csv', { 'csv': self.veils_to_csv([veil]) },
                                                                              'veil_menu', { 'button_messages': self.button_messages })
                        else:
                            error_code = 1
                    else:
                        error_code = 1
            else:
                error_code = 1

            if error_code == 1:
                await self.frontend.send_state_message(input_sender, 
                                                       'veil_menu', 'invalid_command', {},
                                                       'veil_menu', { 'button_messages': self.button_messages })
            elif error_code == 2:
                await self.frontend.send_state_message(input_sender, 
                                                       'veil_menu', 'command_not_successful', {},
                                                       'veil_menu', { 'button_messages': self.button_messages })
                
    def extract_tokens(self, command):
        intermediate_parse, tokens, current_token = command.strip().split(' '), [], ''
        for intermediate_token in intermediate_parse:
            if intermediate_token != '' and current_token == '':
                if (intermediate_token.startswith(self.constant.persian.open_quotation_mark) and
                    not intermediate_token.endswith(self.constant.persian.close_quotation_mark)):
                    current_token = intermediate_token
                else:
                    tokens.append(intermediate_token)
            elif intermediate_token == '' and current_token == '':
                continue
            else:
                current_token += ' ' + intermediate_token
                if intermediate_token.endswith(self.constant.persian.close_quotation_mark):
                    tokens.append(current_token)
                    current_token = ''
        
        if current_token != '':
            tokens.append(current_token)
        return tokens
    
    def is_quoted(self, token):
        return True if (token.startswith(self.constant.persian.open_quotation_mark) and 
                        token.endswith(self.constant.persian.close_quotation_mark)) else False
    
    def remove_quotation_marks(self, token):
        return token[1:-1]
    
    def veils_to_csv(self, veils: list[Veil]):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['name', 'category', 'reserved_by', 'owned_by', 'reservation_status'])
        for veil in veils:
            writer.writerow([veil.name, veil.category, (veil.reserved_by if veil.reserved_by != None else 'None'), (veil.owned_by if veil.owned_by != None else 'None'), veil.reservation_status])
        return output.getvalue()

