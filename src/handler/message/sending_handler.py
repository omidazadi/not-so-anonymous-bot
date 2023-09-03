import pickle
import logging
import aiomysql
from telethon import TelegramClient
from model.user_status import UserStatus
from repository.user_status_repo import UserStatusRepo
from repository.channel_message_repo import ChannelMessageRepo
from neo_frontend import Frontend
from config import Config
from constant import Constant
from helper import utf8len

class SendingHandler:
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, user_status_repo, channel_message_repo):
        self.logger = logging.getLogger('not_so_anonymous')
        self.config: Config = config
        self.constant: Constant = constant
        self.telethon_bot: TelegramClient = telethon_bot
        self.button_messages = button_messages
        self.frontend: Frontend = frontend
        self.user_status_repo: UserStatusRepo = user_status_repo
        self.channel_message_repo: ChannelMessageRepo = channel_message_repo
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'sending handler!')

        input_sender = event.message.input_sender
        if event.message.message == self.button_messages['sending']['hidden_start']:
            user_status.state = 'home'
            await self.user_status_repo.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        elif event.message.message == self.button_messages['sending']['discard']:
            user_status.state = 'home'
            await self.user_status_repo.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'sending', 'discard', {},
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            media = None
            if event.message.media != None:
                if hasattr(event.message.media, 'photo'):
                    media = event.message.media.photo
                elif hasattr(event.message.media, 'document'):
                    media = event.message.media.document
                else:
                    user_status.state = 'home'
                    await self.user_status_repo.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'sending', 'not_supported', {},
                                                           'home', { 'button_messages': self.button_messages, 'user_status': user_status })
                    return
                
            if (media != None and utf8len(event.message.message) > self.constant.limit.media_message_size or 
                media == None and utf8len(event.message.message) > self.constant.limit.simple_message_size):
                user_status.state = 'home'
                await self.user_status_repo.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'sending', 'too_big', {}, 
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
                return
            
            media_stream = pickle.dumps(media)

            channel_message_id = await self.channel_message_repo.create_channel_message(user_status.user_id, event.message.message, media_stream, db_connection)
            
            message_tid = str(await self.frontend.send_inline_message(input_sender, 'channel_message_preview', 'waiting', 
                                                                      { 'user_status': user_status, 'message': event.message.message },
                                                                      { 'channel_message_id': channel_message_id }))
            await self.channel_message_repo.set_channel_message_tid(channel_message_id, message_tid, db_connection)
            user_status.state = 'home'
            await self.user_status_repo.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'sending', 'confirmation', {},
                                                  'home', { 'button_messages': self.button_messages, 'user_status': user_status },
                                                  reply_to=message_tid)