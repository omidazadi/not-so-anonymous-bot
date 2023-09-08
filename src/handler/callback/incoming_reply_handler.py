import logging
import aiomysql
from model.user_status import UserStatus
from model.peer_message import PeerMessage
from handler.callback.base_handler import BaseHandler
from mixin.reciever_mixin import RecieverMixin

class IncomingReplyHandler(RecieverMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository)
        self.logger = logging.getLogger('not_so_anonymous')

    async def handle(self, sender_status: UserStatus, inline_senario, inline_button, data, db_connection: aiomysql.Connection):
        self.logger.info(f'incoming_reply handler!')

        peer_message = await self.repository.peer_message.get_peer_message(int(data), db_connection)
        user_status = await self.repository.user_status.get_user_status(peer_message.from_user, db_connection)
        (reciever_status, message_tid) = await self.get_reciever(peer_message, db_connection)
        if sender_status.user_id != reciever_status.user_id:
            return
        
        input_sender = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
        input_reciever = await self.telethon_bot.get_input_entity(int(reciever_status.user_tid))
        if inline_senario == 's':
            if peer_message.message_status != 'z':
                return
            
            if inline_button == 'o':
                await self.repository.peer_message.seen_peer_message(peer_message.peer_message_id, db_connection)
                await self.frontend.edit_inline_message(input_sender, peer_message.from_message_tid, 'outgoing_reply', 'sent_seen', 
                                                        { 'user_status': user_status, 'message': peer_message.message },
                                                        {})
                await self.frontend.edit_inline_message(input_reciever, peer_message.to_message_tid, 'incoming_reply', 'opened', 
                                                        { 'user_status': user_status, 'message': peer_message.message },
                                                        { 'peer_message_id': peer_message.peer_message_id },
                                                        media=(None if peer_message.media == None else peer_message.media))
        elif inline_senario == 'o':
            if peer_message.message_status != 's':
                return
            
            if inline_button == 'a':
                await self.goto_peer_reply_state(input_reciever, peer_message, reciever_status, db_connection)
    
    async def goto_peer_reply_state(self, input_sender, peer_message: PeerMessage, user_status: UserStatus, db_connection: aiomysql.Connection):
        admin_states = ['admin_home', 'pending_list', 'message_review']
        prev_state = ('admin_home' if ((user_status.state in admin_states) or 
                      (user_status.state == 'channel_reply' and user_status.extra.split(',')[0] == 'admin_home') or
                      (user_status.state == 'peer_reply' and user_status.extra.split(',')[0] == 'admin_home')) else 'home')
        user_status.state = 'peer_reply'
        user_status.extra = f'{prev_state},{peer_message.peer_message_id}'

        if peer_message.message_status != 's':
            (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
            user_status.state = user_status.extra.split(',')[0]
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'not_found', {},
                                                   return_button_state, return_button_kws)
            return

        sender_entity = await self.telethon_bot.get_entity(int(user_status.user_tid))
        if not await self.is_member_of_channel(sender_entity):
            (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
            user_status.state = user_status.extra.split(',')[0]
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'must_be_a_member', { 'channel_id': self.config.channel.id },
                                                   return_button_state, return_button_kws)
            return
        
        await self.frontend.send_state_message(input_sender, 
                                               'peer_reply', 'main', {},
                                               'peer_reply', { 'button_messages': self.button_messages })
        await self.repository.user_status.set_user_status(user_status, db_connection)
        
    async def get_return_button_state_for_reply(self, user_status: UserStatus, db_connection: aiomysql.Connection):
        prev_state = user_status.extra.split(',')[0]
        if prev_state == 'home':
            return ('home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            return ('admin_home', { 'button_messages': self.button_messages })

        

