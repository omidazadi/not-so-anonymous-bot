import logging
import pickle
import aiomysql
from model.user_status import UserStatus
from handler.callback.base_handler import BaseHandler
from mixin.reciever_mixin import RecieverMixin

class OutgoingReplyHandler(RecieverMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository)
        self.logger = logging.getLogger('not_so_anonymous')

    async def handle(self, sender_status: UserStatus, inline_senario, inline_button, data, db_connection: aiomysql.Connection):
        self.logger.info(f'outgoing_reply handler!')

        peer_message = await self.repository.peer_message.get_peer_message(int(data), db_connection)
        user_status = await self.repository.user_status.get_user_status(peer_message.from_user, db_connection)
        if sender_status.user_id != user_status.user_id:
            return
        
        input_sender = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
        if inline_senario == 'w':
            if peer_message.message_status != 'w':
                return
            
            if inline_button == 's':
                (reciever_status, message_tid) = await self.get_reciever(peer_message, db_connection)
                input_reciever = await self.telethon_bot.get_input_entity(int(reciever_status.user_tid))
                media = None
                if peer_message.media != None:
                    media = pickle.loads(self.constant.view.new_reply_media)
                to_message_tid_int = await self.frontend.send_inline_message(input_reciever, 'incoming_reply', 'sealed', 
                                                                             { 'user_status': user_status, 'message': peer_message.message },
                                                                             { 'peer_message_id': peer_message.peer_message_id },
                                                                             reply_to=message_tid, media=media)
                
                if to_message_tid_int == None:
                    await self.frontend.send_inline_message(input_sender, 'i_am_blocked', 'notification', 
                                                            {},
                                                            {},
                                                            reply_to=peer_message.from_message_tid)
                    return
                else:
                    is_ok = await self.repository.peer_message.send_the_waiting_peer_message(peer_message.peer_message_id, db_connection)
                    if is_ok:
                        if peer_message.peer_message_reply != None:
                            replied_to_peer_message = await self.repository.peer_message.get_peer_message(peer_message.peer_message_reply, db_connection)
                            await self.frontend.edit_inline_message(input_reciever, replied_to_peer_message.to_message_tid, 'incoming_reply', 'answered', 
                                                                    { 'user_status': user_status, 'message': peer_message.message },
                                                                    {})
                        await self.repository.peer_message.set_to_message_tid(peer_message.peer_message_id, str(to_message_tid_int), db_connection)
                        await self.frontend.edit_inline_message(input_sender, peer_message.from_message_tid, 'outgoing_reply', 'sent_not_seen', 
                                                                { 'user_status': user_status, 'message': peer_message.message },
                                                                {})
            elif inline_button == 'd':
                is_ok = await self.repository.peer_message.delete_the_waiting_peer_message(peer_message.peer_message_id, db_connection)
                if is_ok:
                    media = None
                    if peer_message.media != None:
                        media = pickle.loads(self.constant.view.discard_media)
                    await self.frontend.edit_inline_message(input_sender, peer_message.from_message_tid, 'outgoing_reply', 'discarded', 
                                                            {},
                                                            {},
                                                            media=media)
