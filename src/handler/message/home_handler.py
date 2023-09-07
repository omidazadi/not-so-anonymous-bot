import logging
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler
from mixin.rate_limit_mixin import RateLimitMixin

class HomeHandler(RateLimitMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'home handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['home']['hidden_start'] or
            event.message.message.startswith(self.button_messages['home']['hidden_start'] + ' ')):
            data = self.parse_hidden_start(event.message.message)
            if data == None:
                await self.frontend.send_state_message(input_sender, 
                                                       'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                await self.goto_channel_reply_state(input_sender, 'home', data, user_status, db_connection)
        elif event.message.message == self.button_messages['home']['hidden_admin']:
            user_status.state = 'admin_auth'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'admin_auth', 'main', {},
                                                   'admin_auth', { 'button_messages': self.button_messages })
        elif event.message.message == self.button_messages['home']['talk_to_admin']:
            await self.frontend.send_state_message(input_sender, 
                                                   'home', 'talk_to_admin', { 'channel_admin': self.config.channel.admin },
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        elif event.message.message == self.button_messages['home']['send_message']:
            sender_entity = await self.telethon_bot.get_entity(int(user_status.user_tid))
            if await self.is_member_of_channel(sender_entity):
                if not await self.is_rate_limited(user_status):
                    user_status.state = 'sending'
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'sending', 'main', {},
                                                           'sending', { 'button_messages': self.button_messages })
                else:
                    await self.frontend.send_state_message(input_sender, 
                                                           'home', 'slow_down', { 'wait': self.constant.limit.rate_limit },
                                                           'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                await self.frontend.send_state_message(input_sender, 
                                                       'home', 'must_be_a_member', { 'channel_id': self.config.channel.id },
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'unknown', {},
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
