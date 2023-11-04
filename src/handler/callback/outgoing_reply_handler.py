import logging
import pickle
import aiomysql
from model.user_status import UserStatus
from handler.callback.base_handler import BaseHandler
from mixin.reciever_mixin import RecieverMixin

class OutgoingReplyHandler(RecieverMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')

    async def handle(self, sender_status: UserStatus, inline_senario, inline_button, data, db_connection: aiomysql.Connection):
        self.logger.info(f'outgoing_reply handler!')

        peer_message = await self.repository.peer_message.get_peer_message(int(data), db_connection)
        if peer_message == None:
            return
        
        user_status = await self.repository.user_status.get_user_status(peer_message.from_user, db_connection)
        if sender_status.user_id != user_status.user_id:
            return
        
        if not self.participant_manager.is_a_member(user_status):
            await self.frontend.send_inline_message(input_sender, 'notification', 'must_be_a_member', 
                                                    { 'channel_id': self.config.channel.id },
                                                    {},
                                                    reply_to=peer_message.from_message_tid)
            return
        
        (reciever_status, message_tid) = await self.get_reciever(peer_message, db_connection)
        input_reciever = await self.telethon_bot.get_input_entity(int(reciever_status.user_tid))
        input_sender = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
        if inline_senario == 'w':
            if peer_message.message_status != 'w':
                return
            
            if inline_button == 's':
                if await self.repository.block.is_blocked_by(reciever_status.user_id, user_status.user_id, db_connection):
                    await self.frontend.send_inline_message(input_sender, 'notification', 'you_are_blocked', 
                                                            {},
                                                            {},
                                                            reply_to=peer_message.from_message_tid)
                    return
                    
                if await self.repository.block.is_blocked_by(user_status.user_id, reciever_status.user_id, db_connection):
                    await self.frontend.send_inline_message(input_sender, 'notification', 'he_is_blocked', 
                                                            {},
                                                            {},
                                                            reply_to=peer_message.from_message_tid)
                    return
                
                if peer_message.peer_message_reply != None:
                    if await self.repository.peer_message.is_already_replied(peer_message.peer_message_reply, db_connection):
                        await self.frontend.send_inline_message(input_sender, 'notification', 'already_replied', 
                                                                {},
                                                                {},
                                                                reply_to=peer_message.from_message_tid)
                        return
                if peer_message.channel_message_reply != None:
                    channel_message = await self.repository.channel_message.get_channel_message(peer_message.channel_message_reply, db_connection)
                    if not channel_message.can_reply:
                        await self.frontend.send_inline_message(input_sender, 'notification', 'reply_is_closed', 
                                                                {},
                                                                {},
                                                                reply_to=peer_message.from_message_tid)
                        return

                    no_replies = await self.repository.peer_message.get_no_replies(channel_message.channel_message_id, user_status.user_id, db_connection)
                    if no_replies >= self.constant.limit.channel_reply_limit:
                        await self.frontend.send_inline_message(input_sender, 'notification', 'channel_reply_limit_reached', 
                                                                { 'channel_reply_limit': self.constant.limit.channel_reply_limit },
                                                                {},
                                                                reply_to=peer_message.from_message_tid)
                        return
                
                to_notification_tid_int = await self.frontend.send_inline_message(input_reciever, 'notification', 'you_have_a_reply', 
                                                                             {},
                                                                             { 'peer_message_id': peer_message.peer_message_id },
                                                                             reply_to=message_tid)
                
                if to_notification_tid_int == None:
                    await self.frontend.send_inline_message(input_sender, 'notification', 'i_am_blocked', 
                                                            {},
                                                            {},
                                                            reply_to=peer_message.from_message_tid)
                    return
                else:
                    is_ok = await self.repository.peer_message.send_the_waiting_peer_message(peer_message.peer_message_id, db_connection)
                    if is_ok:
                        if peer_message.peer_message_reply != None:
                            replied_to_peer_message = await self.repository.peer_message.get_peer_message(peer_message.peer_message_reply, db_connection)
                            await self.frontend.edit_inline_message(input_sender, replied_to_peer_message.to_message_tid, 'incoming_reply', 'answered', 
                                                                    { 'message': replied_to_peer_message },
                                                                    {})
                        await self.repository.peer_message.set_to_notification_tid(peer_message.peer_message_id, str(to_notification_tid_int), db_connection)
                        await self.frontend.edit_inline_message(input_sender, peer_message.from_message_tid, 'outgoing_reply', 'sent_not_seen', 
                                                                { 'message': peer_message },
                                                                {})
            elif inline_button == 'd':
                is_ok = await self.repository.peer_message.delete_the_waiting_peer_message(peer_message.peer_message_id, db_connection)
                if is_ok:
                    await self.frontend.delete_inline_message(peer_message.from_message_tid)
