import aiomysql
from telethon import TelegramClient
from telethon.hints import EntityLike
from model.user_status import UserStatus
from repository.repository import Repository
from frontend import Frontend
from config import Config
from constant import Constant
from veil_manager import VeilManager
from mixin.member_check_mixin import MemberCheckMixin

class BaseHandler(MemberCheckMixin):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, veil_manager):
        self.config: Config = config
        self.constant: Constant = constant
        self.telethon_bot: TelegramClient = telethon_bot
        self.button_messages = button_messages
        self.frontend: Frontend = frontend
        self.repository: Repository = repository
        self.veil_manager: VeilManager = veil_manager
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        pass

    def parse_hidden_start(self, message):
        if len(message) > len(self.button_messages['home']['hidden_start']):
            if message[len(self.button_messages['home']['hidden_start']) + 1] == 'p':
                return 'p', message[len(self.button_messages['home']['hidden_start']) + 2:]
            elif message[len(self.button_messages['home']['hidden_start']) + 1] == 'a':
                return 'a', message[len(self.button_messages['home']['hidden_start']) + 2:]
            return 'c', message[len(self.button_messages['home']['hidden_start']) + 1:]
        return None, None
    
    async def goto_channel_reply_state(self, input_sender, prev_state, channel_message_id_str: str, reply_type, user_status: UserStatus, db_connection: aiomysql.Connection):
        user_status.state = 'channel_reply'
        user_status.extra = f'{prev_state},{channel_message_id_str},{reply_type}'

        if await self.is_member_of_channel(user_status):
            if reply_type == 'p' or reply_type == 'c':
                channel_message = (await self.repository.channel_message.get_channel_message(int(channel_message_id_str), db_connection)
                                   if channel_message_id_str.isnumeric() else None)
                
                if channel_message == None or channel_message.verdict != 'a':
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'common', 'not_found', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                if (channel_message.is_public and reply_type == 'c') or (not channel_message.is_public and reply_type == 'p'):
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'common', 'not_found', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                if channel_message.discusison_message_tid == '?':
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'channel_reply', 'wait_a_little', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                if channel_message.from_user == user_status.user_id:
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'channel_reply', 'can_not_reply_to_yourself', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                if await self.repository.block.is_blocked_by(channel_message.from_user, user_status.user_id, db_connection):
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'common', 'you_are_blocked', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                if await self.repository.block.is_blocked_by(user_status.user_id, channel_message.from_user, db_connection):
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'common', 'he_is_blocked', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return

                if not channel_message.can_reply:
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'channel_reply', 'reply_is_closed', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                no_replies = (await self.repository.peer_message.get_no_replies(channel_message.channel_message_id, user_status.user_id, db_connection) + 
                              await self.repository.answer_message.get_no_replies(channel_message.channel_message_id, user_status.user_id, db_connection))
                if no_replies >= self.constant.limit.channel_reply_limit:
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'channel_reply', 'reply_limit_reached', { 'channel_reply_limit': self.constant.limit.channel_reply_limit },
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                await self.frontend.send_state_message(input_sender, 
                                                       'channel_reply', 'main', {},
                                                       'channel_reply', { 'button_messages': self.button_messages })
                await self.repository.user_status.set_user_status(user_status, db_connection)
            else:
                answer_message = (await self.repository.answer_message.get_answer_message(int(channel_message_id_str), db_connection)
                                  if channel_message_id_str.isnumeric() else None)
                if answer_message == None or answer_message.message_status != 'a':
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'common', 'not_found', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                if answer_message.from_user == user_status.user_id:
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'channel_reply', 'can_not_reply_to_yourself', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                if await self.repository.block.is_blocked_by(answer_message.from_user, user_status.user_id, db_connection):
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'common', 'you_are_blocked', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                if await self.repository.block.is_blocked_by(user_status.user_id, answer_message.from_user, db_connection):
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'common', 'he_is_blocked', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                if not answer_message.can_reply:
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'channel_reply', 'reply_is_closed', {},
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                no_replies = await self.repository.peer_message.get_no_replies_to_answers(answer_message.answer_message_id, user_status.user_id, db_connection)
                if no_replies >= self.constant.limit.channel_reply_limit:
                    (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
                    await self.frontend.send_state_message(input_sender, 
                                                           'channel_reply', 'reply_limit_reached', { 'channel_reply_limit': self.constant.limit.channel_reply_limit },
                                                           return_button_state, return_button_kws)
                    user_status.state = user_status.extra.split(',')[0]
                    user_status.extra = None
                    await self.repository.user_status.set_user_status(user_status, db_connection)
                    return
                
                await self.frontend.send_state_message(input_sender, 
                                                       'channel_reply', 'main', {},
                                                       'channel_reply', { 'button_messages': self.button_messages })
                await self.repository.user_status.set_user_status(user_status, db_connection)
        else:
            (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'must_be_a_member', { 'channel_id': self.config.channel.id },
                                                   return_button_state, return_button_kws)
            user_status.state = user_status.extra.split(',')[0]
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            return
        
    async def get_return_state_for_reply(self, user_status: UserStatus, db_connection: aiomysql.Connection):
        prev_state = user_status.extra.split(',')[0]
        if prev_state == 'home':
            return ('home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id })
        else:
            no_pending_messages = await self.repository.channel_message.get_no_pending_messages(db_connection)
            no_reports = ((await self.repository.peer_message.get_no_reports(db_connection)) + 
                          (await self.repository.answer_message.get_no_reports(db_connection)))
            return ('admin_home', 'main', { 'no_pending_messages': no_pending_messages, 'no_reports': no_reports })

    async def get_return_button_state_for_reply(self, user_status: UserStatus, db_connection: aiomysql.Connection):
        prev_state = user_status.extra.split(',')[0]
        if prev_state == 'home':
            return ('home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            return ('admin_home', { 'button_messages': self.button_messages })