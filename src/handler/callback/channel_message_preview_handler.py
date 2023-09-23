from datetime import datetime
import pickle
import logging
import aiomysql
from model.user_status import UserStatus
from handler.callback.base_handler import BaseHandler
from mixin.rate_limit_mixin import RateLimitMixin

class ChannelMessagePreviewHandler(RateLimitMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository)
        self.logger = logging.getLogger('not_so_anonymous')

    async def handle(self, sender_status: UserStatus, inline_senario, inline_button, data, db_connection: aiomysql.Connection):
        self.logger.info(f'channel_message_preview handler!')

        channel_message = await self.repository.channel_message.get_channel_message(int(data), db_connection)
        user_status = await self.repository.user_status.get_user_status(channel_message.from_user, db_connection)
        if sender_status.user_id != user_status.user_id:
            return
        
        input_sender = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
        if inline_senario == 'w':
            if channel_message.verdict != 'w':
                return
            
            if inline_button == 's':
                if await self.is_member_of_channel(user_status.user_tid):
                    if not await self.is_rate_limited(user_status):
                        is_ok = await self.repository.channel_message.send_the_waiting_channel_message(channel_message.channel_message_id, db_connection)
                        if is_ok:
                            user_status.last_message_at = datetime.utcnow()
                            await self.repository.user_status.set_user_status(user_status, db_connection)
                            await self.frontend.edit_inline_message(input_sender, channel_message.message_tid, 'channel_message_preview', 'pending', 
                                                                    { 'user_status': user_status, 'message': channel_message.message },
                                                                    {})
                            await self.notify_admins_new_message(db_connection)
                    else:
                        await self.frontend.send_inline_message(input_sender, 'notification', 'slow_down', 
                                                                { 'wait': self.constant.limit.rate_limit },
                                                                {},
                                                                reply_to=channel_message.message_tid)
                else:
                    await self.frontend.send_inline_message(input_sender, 'notification', 'must_be_a_member', 
                                                            { 'channel_id': self.config.channel.id },
                                                            {},
                                                            reply_to=channel_message.message_tid)
            elif inline_button == 'd':
                is_ok = await self.repository.channel_message.delete_the_waiting_channel_message(channel_message.channel_message_id, db_connection)
                if is_ok:
                    media = None
                    if channel_message.media != None:
                        media = pickle.loads(self.config.bot.discard_media)
                    await self.frontend.edit_inline_message(input_sender, channel_message.message_tid, 'channel_message_preview', 'discarded', 
                                                            {},
                                                            {},
                                                            media=media)
        elif inline_senario == 'a':
            if channel_message.verdict != 'a':
                return
            
            if inline_button == 'c':
                await self.repository.channel_message.close_reply(channel_message.channel_message_id, db_connection)
                await self.frontend.edit_inline_message(input_sender, channel_message.message_tid, 'channel_message_preview', 'approved_closed', 
                                                        { 'user_status': user_status, 'message': channel_message.message },
                                                        {})

    async def notify_admins_new_message(self, db_connection: aiomysql.Connection):
        admin_states = ['admin_home', 'pending_list', 'message_review', 'ban_menu']
        admin_users = await self.repository.user_status.get_admin_users(db_connection)
        for admin_user in admin_users:
            if (admin_user.state in admin_states or
                (admin_user.state == 'channel_reply' and admin_user.extra.split(',')[0] == 'admin_home') or
                (admin_user.state == 'peer_reply' and admin_user.extra.split(',')[0] == 'admin_home')):
                input_user = await self.telethon_bot.get_input_entity(int(admin_user.user_tid))
                await self.frontend.send_inline_message(input_user, 'notification', 'admin_new_channel_message', 
                                                        {},
                                                        {})
