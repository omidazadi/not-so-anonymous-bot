import logging
import pickle
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler
from mixin.message_and_media_mixin import MessageAndMediaMixin

class PeerReplyHandler(MessageAndMediaMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'peer_reply handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['peer_reply']['hidden_start'] or
            event.message.message.startswith(self.button_messages['peer_reply']['hidden_start'] + ' ')):
            data = self.parse_hidden_start(event.message.message)
            if data == None:
                (return_state, return_edge, return_kws) = await self.get_return_state_for_reply(user_status, db_connection)
                (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                user_status.state = return_state
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       return_state, return_edge, return_kws,
                                                       return_button_state, return_button_kws)
            else:
                await self.goto_channel_reply_state(input_sender, user_status.extra.split(',')[0], data, user_status, db_connection)
        elif event.message.message == self.button_messages['peer_reply']['discard']:
            (return_state, return_edge, return_kws) = await self.get_return_state_for_reply(user_status, db_connection)
            (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
            user_status.state = return_state
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'peer_reply', 'discard', {},
                                                   return_button_state, return_button_kws)
        else:
            message, media = await self.verify_message_and_media(event, user_status.extra.split(',')[0], user_status, db_connection)
            if message == None and media == None:
                return
            
            media_stream = pickle.dumps(media)
            replied_to_peer_message_id = int(user_status.extra.split(',')[1])
            replied_to_peer_message = await self.repository.peer_message.get_peer_message(replied_to_peer_message_id, db_connection)
            original_message = None
            if replied_to_peer_message.channel_message_reply != None:
                original_message = await self.repository.channel_message.get_channel_message(replied_to_peer_message.channel_message_reply, db_connection)
            else:
                original_message = await self.repository.peer_message.get_peer_message(replied_to_peer_message.peer_message_reply, db_connection)
            reply_message_id = await self.repository.peer_message.create_peer_peer_message(replied_to_peer_message_id, user_status.user_id, original_message.from_user_veil, message, media_stream, db_connection)
            reply_message = await self.repository.peer_message.get_peer_message(reply_message_id, db_connection)
            reply_message_tid_int = await self.frontend.send_inline_message(input_sender, 'outgoing_reply', 'waiting', 
                                                                            { 'message': reply_message },
                                                                            { 'peer_message_id': reply_message_id },
                                                                            media=media, reply_to=replied_to_peer_message.to_message_tid)
            if reply_message_tid_int == None:
                (return_state, return_edge, return_kws) = await self.get_return_state_for_reply(user_status, db_connection)
                (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                user_status.state = return_state
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'peer_reply', 'confirmation', {},
                                                       return_button_state, return_button_kws)
            else:
                await self.repository.peer_message.set_from_message_tid(reply_message_id, str(reply_message_tid_int), db_connection)
                (return_state, return_edge, return_kws) = await self.get_return_state_for_reply(user_status, db_connection)
                (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                user_status.state = return_state
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'peer_reply', 'confirmation', {},
                                                       return_button_state, return_button_kws)