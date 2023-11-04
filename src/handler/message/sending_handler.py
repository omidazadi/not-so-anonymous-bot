import pickle
import logging
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler
from mixin.message_and_media_mixin import MessageAndMediaMixin

class SendingHandler(MessageAndMediaMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, participant_manager, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'sending handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['sending']['hidden_start'] or
            event.message.message.startswith(self.button_messages['sending']['hidden_start'] + ' ')):
            data = self.parse_hidden_start(event.message.message)
            if data == None:
                user_status.state = 'home'
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                await self.goto_channel_reply_state(input_sender, 'home', data, user_status, db_connection)
        elif event.message.message == self.button_messages['sending']['discard']:
            user_status.state = 'home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'sending', 'discard', {},
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            (message, media) = await self.verify_message_and_media(event, 'home', user_status, db_connection)
            if message == None and media == None:
                return
            
            media_stream = pickle.dumps(media)
            channel_message_id = await self.repository.channel_message.create_channel_message(user_status.user_id, user_status.veil, message, media_stream, db_connection)
            channel_message = await self.repository.channel_message.get_channel_message(channel_message_id, db_connection)
            message_tid_int = await self.frontend.send_inline_message(input_sender, 'channel_message_preview', 'waiting', 
                                                                      { 'message': channel_message },
                                                                      { 'channel_message_id': channel_message_id },
                                                                      media=media)
            if message_tid_int != None:
                await self.repository.channel_message.set_channel_message_tid(channel_message_id, str(message_tid_int), db_connection)

            user_status.state = 'home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'sending', 'confirmation', {},
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })