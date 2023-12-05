import logging
import aiomysql
from model.user_status import UserStatus
from model.peer_message import PeerMessage
from handler.callback.base_handler import BaseHandler
from mixin.reciever_mixin import RecieverMixin

class NotificationHandler(RecieverMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')

    async def handle(self, sender_status: UserStatus, inline_senario, inline_button, data, db_connection: aiomysql.Connection):
        self.logger.info(f'notification handler!')

        if inline_senario == 'y':
            peer_message = await self.repository.peer_message.get_peer_message(int(data), db_connection)
            user_status = await self.repository.user_status.get_user_status(peer_message.from_user, db_connection)
            (reciever_status, message_tid) = await self.get_peer_reciever(peer_message, db_connection)
            if sender_status.user_id != reciever_status.user_id:
                return
            
            input_sender = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
            input_reciever = await self.telethon_bot.get_input_entity(int(reciever_status.user_tid))

            if peer_message.message_status != 'z':
                return
            
            if inline_button == 'o':
                to_message_tid = None
                if await self.repository.block.is_blocked_by(reciever_status.user_id, user_status.user_id, db_connection):
                    to_message_tid = await self.frontend.send_inline_message(input_reciever, 'incoming_reply', 'opened_blocked', 
                                                                             { 'message': peer_message },
                                                                             { 'peer_message_id': peer_message.peer_message_id },
                                                                             media=peer_message.media, reply_to=message_tid)
                else:
                    to_message_tid = await self.frontend.send_inline_message(input_reciever, 'incoming_reply', 'opened', 
                                                                             { 'message': peer_message },
                                                                             { 'peer_message_id': peer_message.peer_message_id },
                                                                             media=peer_message.media, reply_to=message_tid)
                if to_message_tid == None:
                    return
                
                await self.repository.peer_message.set_to_message_tid(peer_message.peer_message_id, to_message_tid, db_connection)
                await self.frontend.delete_inline_message(peer_message.to_notification_tid)
                
                await self.repository.peer_message.seen_peer_message(peer_message.peer_message_id, db_connection)
                await self.frontend.edit_inline_message(input_sender, peer_message.from_message_tid, 'outgoing_reply', 'sent_seen', 
                                                        { 'message': peer_message },
                                                        {})
        elif inline_senario == 'a':
            answer_message = await self.repository.answer_message.get_answer_message(int(data), db_connection)
            user_status = await self.repository.user_status.get_user_status(answer_message.from_user, db_connection)
            (reciever_status, message_tid) = await self.get_answer_reciever(answer_message, db_connection)
            if sender_status.user_id != reciever_status.user_id:
                return
            
            input_sender = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
            input_reciever = await self.telethon_bot.get_input_entity(int(reciever_status.user_tid))

            if answer_message.message_status != 'z':
                return
            
            if inline_button == 'o':
                to_message_tid = None
                if await self.repository.block.is_blocked_by(reciever_status.user_id, user_status.user_id, db_connection):
                    to_message_tid = await self.frontend.send_inline_message(input_reciever, 'incoming_answer', 'opened_blocked', 
                                                                             { 'message': answer_message },
                                                                             { 'answer_message_id': answer_message.answer_message_id },
                                                                             media=answer_message.media, reply_to=message_tid)
                else:
                    to_message_tid = await self.frontend.send_inline_message(input_reciever, 'incoming_answer', 'opened', 
                                                                             { 'message': answer_message },
                                                                             { 'answer_message_id': answer_message.answer_message_id },
                                                                             media=answer_message.media, reply_to=message_tid)
                if to_message_tid == None:
                    return
                
                await self.repository.answer_message.set_to_message_tid(answer_message.answer_message_id, to_message_tid, db_connection)
                await self.frontend.delete_inline_message(answer_message.to_notification_tid)
                
                await self.repository.answer_message.seen_answer_message(answer_message.answer_message_id, db_connection)
                await self.frontend.edit_inline_message(input_sender, answer_message.from_message_tid, 'outgoing_answer', 'seen_pending', 
                                                        { 'message': answer_message },
                                                        {})
                