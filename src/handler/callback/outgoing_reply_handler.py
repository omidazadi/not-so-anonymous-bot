import logging
import aiomysql
from model.peer_message import PeerMessage
from handler.callback.base_handler import BaseHandler

class OutgoingReplyHandler(BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository):
        super.__init__(config, constant, telethon_bot, button_messages, frontend, repository)
        self.logger = logging.getLogger('not_so_anonymous')

    async def handle(self, inline_senario, inline_button, data, db_connection: aiomysql.Connection):
        self.logger.info(f'outgoing_reply handler!')

        peer_message = await self.repository.peer_message.get_peer_message(int(data), db_connection)
        user_status = await self.repository.user_status.get_user_status(peer_message.from_user, db_connection)
        input_sender = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
        if inline_senario == 'w':
            if peer_message.condition != 'w':
                return
            
            if inline_button == 's':
                is_ok = await self.repository.peer_message.send_the_waiting_peer_message(peer_message.peer_message_id, db_connection)
                if is_ok:
                    (reciever_id, message_tid) = await self.get_reciever_and_tid(peer_message, db_connection)
                    input_reciever = self.telethon_bot.get_input_entity(int(reciever_id))
                    to_message_tid_int = await self.frontend.send_inline_message(input_reciever, 'incoming_reply', 'sealed', 
                                                                                 { 'user_status': user_status, 'message': peer_message.message },
                                                                                 {},
                                                                                 reply_to=message_tid)
                    
                    if to_message_tid_int == None:
                        await self.frontend.send_inline_message(input_reciever, 'i_am_blocked', 'notification', 
                                                                {},
                                                                {})
                        return
                    else:
                        await self.repository.peer_message.set_to_message_tid(peer_message.peer_message_id, str(to_message_tid_int))
                        await self.frontend.edit_inline_message(input_sender, peer_message.from_message_tid, 'outgoing_reply', 'sent_not_seen', 
                                                                { 'user_status': user_status, 'message': peer_message.message },
                                                                {})
            elif inline_button == 'd':
                is_ok = await self.repository.peer_message.delete_the_waiting_peer_message(peer_message.peer_message_id, db_connection)
                if is_ok:
                    await self.frontend.edit_inline_message(input_sender, peer_message.from_message_tid, 'outgoing_reply', 'discarded', 
                                                            {},
                                                            {})
            
    async def get_reciever_and_tid(self, peer_message: PeerMessage, db_connection: aiomysql.Connection):
        if peer_message.channel_message_reply != None:
            channel_message = await self.repository.channel_message.get_channel_message(peer_message.channel_message_reply, db_connection)
            return (channel_message.from_user, channel_message.message_tid)
        else:
            peer_message = await self.repository.peer_message.get_peer_message(peer_message.peer_message_reply, db_connection)
            return (peer_message.from_user, peer_message.from_message_tid)

