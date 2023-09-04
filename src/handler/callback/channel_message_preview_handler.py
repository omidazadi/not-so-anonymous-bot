from datetime import datetime
import pickle
import logging
import aiomysql
from telethon import TelegramClient
from telethon.hints import EntityLike
from model.user_status import UserStatus
from repository.user_status_repo import UserStatusRepo
from repository.channel_message_repo import ChannelMessageRepo
from frontend import Frontend
from config import Config
from constant import Constant

class ChannelMessagePreviewHandler:
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, user_status_repo, channel_message_repo):
        self.logger = logging.getLogger('not_so_anonymous')
        self.config: Config = config
        self.constant: Constant = constant
        self.telethon_bot: TelegramClient = telethon_bot
        self.button_messages = button_messages
        self.frontend: Frontend = frontend
        self.user_status_repo: UserStatusRepo = user_status_repo
        self.channel_message_repo: ChannelMessageRepo = channel_message_repo

    async def handle(self, inline_senario, inline_button, data, db_connection: aiomysql.Connection):
        self.logger.info(f'channel_message_preview handler!')

        channel_message = await self.channel_message_repo.get_channel_message(int(data), db_connection)
        user_status = await self.user_status_repo.get_user_status(channel_message.from_user, db_connection)
        input_sender = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
        if inline_senario == 'w':
            if channel_message.verdict != 'w':
                return
            
            if inline_button == 's':
                sender_entity = await self.telethon_bot.get_entity(int(user_status.user_tid))
                if await self.is_member_of_channel(sender_entity):
                    if not await self.is_rate_limited(user_status):
                        is_ok = await self.channel_message_repo.send_the_waiting_channel_message(channel_message.channel_message_id, db_connection)
                        if is_ok:
                            user_status.last_message_at = datetime.utcnow()
                            await self.user_status_repo.set_user_status(user_status, db_connection)
                            await self.frontend.edit_inline_message(input_sender, channel_message.message_tid, 'channel_message_preview', 'pending', 
                                                                    { 'user_status': user_status, 'message': channel_message.message },
                                                                    {})
                            await self.notify_admins(db_connection)
                    else:
                        await self.frontend.send_inline_message(input_sender, 'slow_down', 'notification', 
                                                                { 'wait': self.constant.limit.rate_limit },
                                                                {},
                                                                reply_to=channel_message.message_tid)
                else:
                    await self.frontend.send_inline_message(input_sender, 'must_be_a_member', 'notification', 
                                                            { 'channel_id': self.config.channel.id },
                                                            {},
                                                            reply_to=channel_message.message_tid)
            elif inline_button == 'd':
                is_ok = await self.channel_message_repo.delete_the_waiting_channel_message(channel_message.channel_message_id, db_connection)
                if is_ok:
                    media = None
                    if channel_message.media != None:
                        media = pickle.loads(self.constant.view.discard_media)
                    await self.frontend.edit_inline_message(input_sender, channel_message.message_tid, 'channel_message_preview', 'discarded', 
                                                            {},
                                                            {},
                                                            media=media)
        elif inline_senario == 'a':
            if channel_message.verdict != 'a':
                return
            
            if inline_button == 'c':
                await self.frontend.edit_inline_message(input_sender, channel_message.message_tid, 'channel_message_preview', 'approved_closed', 
                                                        { 'user_status': user_status, 'message': channel_message.message },
                                                        {})

    async def notify_admins(self, db_connection: aiomysql.Connection):
        admin_states = ['admin_home', 'pending_list', 'message_review']
        admin_users = await self.user_status_repo.get_admin_users(db_connection)
        for admin_user in admin_users:
            if (admin_user.state in admin_states or
                (admin_user.state == 'channel_reply' and admin_user.extra.split('@')[0] in admin_states) or
                (admin_user.state == 'peer_reply' and admin_user.extra.split('@')[0] in admin_states)):
                input_user = await self.telethon_bot.get_input_entity(int(admin_user.user_tid))
                await self.frontend.send_inline_message(input_user, 'new_channel_message_notification', 'notification', 
                                                        {},
                                                        {})
                
    async def is_member_of_channel(self, sender_entity: EntityLike):
        input_channel = await self.telethon_bot.get_input_entity(self.config.channel.id)
        async for user in self.telethon_bot.iter_participants(input_channel, search=sender_entity.first_name):
            if user.id == sender_entity.id:
                return True
        return False
    
    async def is_rate_limited(self, user_status: UserStatus):
        if user_status.last_message_at == None:
            return False
        now = datetime.utcnow()
        time_passed = now - user_status.last_message_at
        if time_passed.total_seconds() < self.constant.limit.rate_limit:
            return True
        return False
