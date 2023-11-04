import logging
import pickle
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler
from mixin.message_and_media_mixin import MessageAndMediaMixin

class ChannelReplyHandler(MessageAndMediaMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'channel_reply handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['channel_reply']['hidden_start'] or
            event.message.message.startswith(self.button_messages['channel_reply']['hidden_start'] + ' ')):
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
        elif event.message.message == self.button_messages['channel_reply']['discard']:
            (return_state, return_edge, return_kws) = await self.get_return_state_for_reply(user_status, db_connection)
            (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
            user_status.state = return_state
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'channel_reply', 'discard', {},
                                                   return_button_state, return_button_kws)
        else:
            message, media = await self.verify_message_and_media(event, user_status.extra.split(',')[0], user_status, db_connection)
            if message == None and media == None:
                return
            
            media_stream = pickle.dumps(media)
            channel_message_id = int(user_status.extra.split(',')[1])
            peer_message_id = await self.repository.peer_message.create_channel_peer_message(channel_message_id, user_status.user_id, user_status.veil, message, media_stream, db_connection)
            peer_message = await self.repository.peer_message.get_peer_message(peer_message_id, db_connection)
            from_message_tid_int = await self.frontend.send_inline_message(input_sender, 'outgoing_reply', 'waiting', 
                                                                           { 'message': peer_message },
                                                                           { 'peer_message_id': peer_message_id },
                                                                           media=media)
            if from_message_tid_int == None:
                (return_state, return_edge, return_kws) = await self.get_return_state_for_reply(user_status, db_connection)
                (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                user_status.state = return_state
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
            else:
                await self.repository.peer_message.set_from_message_tid(peer_message_id, str(from_message_tid_int), db_connection)
                (return_state, return_edge, return_kws) = await self.get_return_state_for_reply(user_status, db_connection)
                (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                user_status.state = return_state
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'channel_reply', 'confirmation', {},
                                                       return_button_state, return_button_kws)