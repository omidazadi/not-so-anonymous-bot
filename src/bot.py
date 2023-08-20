from datetime import datetime
import pickle
import math
import logging
import json
import bcrypt
import aiomysql
from telethon import TelegramClient, events
from telethon.hints import EntityLike
from frontend import Frontend
from repository import Repository
from model.user_status import UserStatus
from helper import utf8len

class Bot:
    def __init__(self):
        pass

    async def initialize(self, api_id, api_hash, bot_token, channel_id, pending_page_size, pending_preview_length,
                         mysql_db, mysql_host, mysql_port, mysql_user, mysql_password, limit_anonymous_gap, 
                         limit_simple_message_size, limit_media_message_size):
        self.logger = logging.getLogger('not_so_anonymous')
        self.channel_id: str = channel_id
        self.pending_page_size: int = pending_page_size
        self.pending_preview_length: int = pending_preview_length
        self.limit_anonymous_gap: int = limit_anonymous_gap
        self.limit_simple_message_size = limit_simple_message_size
        self.limit_media_message_size = limit_media_message_size
        self.telethonBot: TelegramClient = await TelegramClient('bot', api_id, api_hash, base_logger=logging.getLogger('telethon')).start(bot_token=bot_token)
        self.repository = Repository()
        await self.repository.initialize(mysql_db, mysql_host, mysql_port, mysql_user, mysql_password)
        self.frontend = Frontend(self.telethonBot, self.pending_preview_length, channel_id)
        self.button_messages = json.load(open('resources/button.json', 'r', encoding='utf-8'))
        self.is_paused = False
        self.hook_handler_to_telethon()

    def hook_handler_to_telethon(self):
        @self.telethonBot.on(events.CallbackQuery())
        async def general_callback_handler(event):
            self.logger.info('Incoming callback!')

            if self.is_paused:
                return
            
            data_payload = bytes.decode(event.data, 'utf-8')
            db_connection = await self.repository.open_connection()

            print(event)

            try:
                if data_payload.startswith('ump'):
                    if data_payload.startswith('ump_s'):
                        (channel_message_id, user_id,) = tuple(map(int, data_payload[5:].split(',')))
                        user_status = await self.repository.get_user_status(user_id, db_connection)
                        channel_message = await self.repository.get_channel_message(channel_message_id, db_connection)

                        if user_status != None or channel_message != None:
                            input_user = await self.telethonBot.get_input_entity(int(user_status.user_tid))
                            is_ok = await self.repository.send_the_waiting_channel_message(channel_message_id, db_connection)
                            if is_ok:
                                await self.frontend.edit_inline(input_user, channel_message.message_tid, 'user-message-queue', 'main')
                                await self.frontend.answer_inline(input_user, 'user-message-preview', 'send', reply_to=channel_message.message_tid)
                                await self.notify_admins(db_connection)
                            else:
                                await self.frontend.internal_error(input_user)
                    else:
                        (channel_message_id, user_id,) = tuple(map(int, data_payload[5:].split(',')))
                        user_status = await self.repository.get_user_status(user_id, db_connection)
                        channel_message = await self.repository.get_channel_message(channel_message_id, db_connection)

                        if user_status != None or channel_message != None:
                            input_user = await self.telethonBot.get_input_entity(int(user_status.user_tid))
                            is_ok = await self.repository.delete_the_waiting_channel_message(channel_message_id, db_connection)
                            if is_ok:
                                await self.frontend.edit_inline(input_user, channel_message.message_tid, 'user-message-discard', 'main')
                            else:
                                await self.frontend.internal_error(input_user)

                await self.repository.commit_connection(db_connection)

                self.logger.info(f'Callback has been handled!')
            except Exception as e:
                await self.repository.rollback_connection(db_connection)
                raise e


        @self.telethonBot.on(events.NewMessage())
        async def general_message_handler(event):
            self.logger.info('Incoming message!')

            if not hasattr(event.message.peer_id, 'user_id'):
                return
            
            if self.is_paused:
                await self.frontend.maintenance_mode(event.message.input_sender)
                return

            self.logger.info(f'Input sender: {event.message.input_sender}')
            
            db_connection = await self.repository.open_connection()

            try:
                user_tid = str(event.message.input_sender.user_id)
                user_status = await self.repository.get_user_status_by_tid(user_tid, db_connection)
                if user_status == None:
                    is_admin = True if await self.repository.get_admin(user_tid, db_connection) != None else False
                    await self.repository.create_user_status(user_tid, is_admin, db_connection)
                    user_status = await self.repository.get_user_status_by_tid(user_tid, db_connection)

                if user_status.state == 'home':
                    await self.home_handler(user_status, event, db_connection)
                elif user_status.state == 'sending':
                    await self.sending_handler(user_status, event, db_connection)
                elif user_status.state == 'admin-auth':
                    await self.admin_auth_handler(user_status, event, db_connection)
                elif user_status.state == 'admin-home':
                    await self.admin_home_handler(user_status, event, db_connection)
                elif user_status.state == 'pending-list':
                    await self.pending_list_handler(user_status, event, db_connection)
                elif user_status.state == 'message-review':
                    await self.message_review_handler(user_status, event, db_connection)

                await self.repository.commit_connection(db_connection)

                self.logger.info(f'Request has been completed!')
            except Exception as e:
                await self.repository.rollback_connection(db_connection)
                await self.frontend.internal_error(event.message.input_sender)
                raise e
            
    async def home_handler(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'home handler!')

        if event.message.message == self.button_messages['home']['hidden-start']:
            await self.frontend.answer(event.message.input_sender, user_status, 'home', 'home', 'main', arguments=[self.frontend.make_final_name(user_status), self.channel_id])
        elif event.message.message == self.button_messages['home']['hidden-admin']:
            user_status.state = 'admin-auth'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'home', 'admin-auth', 'yield')
        elif event.message.message == self.button_messages['home']['talk-to-admin']:
            await self.frontend.answer(event.message.input_sender, user_status, 'home', 'home', 'talk-to-admin')
        elif event.message.message == self.button_messages['home']['send-message']:
            sender = await self.telethonBot.get_entity(event.message.input_sender)
            if await self.is_member_of_channel(sender):
                if not await self.is_rate_limited(user_status):
                    user_status.state = 'sending'
                    await self.repository.set_user_status(user_status, db_connection)
                    await self.frontend.answer(event.message.input_sender, user_status, 'home', 'sending', 'yield')
                else:
                    await self.frontend.answer(event.message.input_sender, user_status, 'home', 'home', 'slow-down', arguments=[self.limit_anonymous_gap])
            else:
                await self.frontend.answer(event.message.input_sender, user_status, 'home', 'home', 'must-be-a-member', arguments=[self.channel_id])
        else:
            await self.frontend.answer(event.message.input_sender, user_status, 'home', 'home', 'unknown')

    async def sending_handler(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'sending handler!')

        if event.message.message == self.button_messages['sending']['hidden-start']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'sending', 'home', 'yield', arguments=[self.frontend.make_final_name(user_status), self.channel_id])
        elif event.message.message == self.button_messages['sending']['discard']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'sending', 'home', 'discard')
        else:
            media = None
            if event.message.media != None:
                if hasattr(event.message.media, 'photo'):
                    media = event.message.media.photo
                elif hasattr(event.message.media, 'document'):
                    media = event.message.media.document
                else:
                    await self.frontend.answer(event.message.input_sender, user_status, 'sending', 'home', 'not-supported')
                    return
                
            if media != None and utf8len(event.message.message) > self.limit_media_message_size:
                await self.frontend.answer(event.message.input_sender, user_status, 'sending', 'home', 'too-big')
                return
            if media == None and utf8len(event.message.message) > self.limit_simple_message_size:
                await self.frontend.answer(event.message.input_sender, user_status, 'sending', 'home', 'too-big')
                return
            
            media_stream = pickle.dumps(media)

            channel_message_id = await self.repository.create_channel_message(user_status.user_id, event.message.message, media_stream, db_connection)
            message_tid = str(await self.frontend.send_user_message_preview(event.message.input_sender, channel_message_id, event.message.message, media, user_status))
            await self.repository.set_channel_message_tid(channel_message_id, message_tid, db_connection)
            user_status.state = 'home'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'sending', 'home', 'confirmation', reply_to=message_tid)

    async def admin_auth_handler(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'auth handler!')

        if event.message.message == self.button_messages['admin-auth']['hidden-start'] or \
            event.message.message == self.button_messages['admin-auth']['back']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'admin-auth', 'home', 'wink')
        else:
            if user_status.is_admin:
                admin = await self.repository.get_admin(user_status.user_tid, db_connection)
                if bcrypt.checkpw(bytes(event.message.message, 'utf-8'), bytes(admin.password_hash, encoding='utf-8')):
                    no_pending_messages = await self.repository.get_no_pending_messages(db_connection)
                    user_status.state = 'admin-home'
                    await self.repository.set_user_status(user_status, db_connection)
                    await self.frontend.answer(event.message.input_sender, user_status, 'admin-auth', 'admin-auth', 'correct', no_buttons=True)
                    await self.frontend.answer(event.message.input_sender, user_status, 'admin-auth', 'admin-home', 'yield', arguments=[no_pending_messages])
            else:
                user_status.state = 'home'
                await self.repository.set_user_status(user_status, db_connection)
                await self.frontend.answer(event.message.input_sender, user_status, 'admin-auth', 'home', 'incorrect')

    async def admin_home_handler(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'admin-home handler!')

        if event.message.message == self.button_messages['admin-home']['hidden-start'] or \
            event.message.message == self.button_messages['admin-home']['refresh']:
            no_pending_messages = await self.repository.get_no_pending_messages(db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'admin-home', 'admin-home', 'main', arguments=[no_pending_messages])
        elif event.message.message == self.button_messages['admin-home']['hidden-omidi']:
            await self.frontend.answer(event.message.input_sender, user_status, 'admin-home', 'admin-home', 'omidi')
        elif event.message.message == self.button_messages['admin-home']['exit']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'admin-home', 'home', 'yield', arguments=[self.frontend.make_final_name(user_status), self.channel_id])
        elif event.message.message == self.button_messages['admin-home']['pending-list']:
            user_status.state = 'pending-list'
            user_status.extra = '1'
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'admin-home', 'pending-list', 'yield', special_generation='pending-list', extras=[messages, int(user_status.extra), total_pages])
        else:
            await self.frontend.answer(event.message.input_sender, user_status, 'admin-home', 'admin-home', 'unknown')

    async def pending_list_handler(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'pending-list handler!')

        if event.message.message == self.button_messages['pending-list']['hidden-start'] or \
            event.message.message == self.button_messages['pending-list']['back']:
            no_pending_messages = await self.repository.get_no_pending_messages(db_connection)
            user_status.state = 'admin-home'
            user_status.extra = None
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'pending-list', 'admin-home', 'yield', arguments=[no_pending_messages])
        elif event.message.message == self.button_messages['pending-list']['next']:
            user_status.extra = str(int(user_status.extra) + 1)
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'pending-list', 'pending-list', 'main', special_generation='pending-list', extras=[messages, int(user_status.extra), total_pages])
        elif event.message.message == self.button_messages['pending-list']['previous']:
            user_status.extra = str(int(user_status.extra) - 1)
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'pending-list', 'pending-list', 'main', special_generation='pending-list', extras=[messages, int(user_status.extra), total_pages])
        else:
            if event.message.message.isnumeric():
                channel_message_id = int(event.message.message)
                channel_message = await self.repository.get_channel_message(channel_message_id, db_connection)
                if channel_message != None:
                    user_status.state = 'message-review'
                    user_status.extra = f'{str(channel_message.channel_message_id)},{user_status.extra}'
                    await self.repository.set_user_status(user_status, db_connection)
                    await self.frontend.answer(event.message.input_sender, user_status, 'pending-list', 'message-review', 'yield', special_generation='message-review', extras=[channel_message])
                else:
                    await self.frontend.answer(event.message.input_sender, user_status, 'pending-list', 'pending-list', 'not-found')
            else:
                await self.frontend.answer(event.message.input_sender, user_status, 'pending-list', 'pending-list', 'not-found')

    async def message_review_handler(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'message-review handler!')

        if event.message.message == self.button_messages['message-review']['hidden-start']:
            no_pending_messages = await self.repository.get_no_pending_messages(db_connection)
            user_status.state = 'admin-home'
            user_status.extra = None
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'admin-home', 'yield', arguments=[no_pending_messages])
        elif event.message.message == self.button_messages['message-review']['back']:
            user_status.state = 'pending-list'
            user_status.extra = user_status.extra.split(',')[1]
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'pending-list', 'yield', special_generation='pending-list', extras=[messages, int(user_status.extra), total_pages])
        elif event.message.message == self.button_messages['message-review']['accept']:
            channel_message_id = int(user_status.extra.split(',')[0])
            is_ok = await self.repository.set_channel_message_verdict('a', user_status.user_id, channel_message_id, db_connection)
            user_status.state = 'pending-list'
            user_status.extra = user_status.extra.split(',')[1]
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)

            if is_ok:
                await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'message-review', 'accept', no_buttons=True)
                await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'pending-list', 'yield', special_generation='pending-list', extras=[messages, int(user_status.extra), total_pages])
                await self.send_to_channel(channel_message_id, user_status, db_connection)
            else:
                await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'message-review', 'not-found', no_buttons=True)
                await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'pending-list', 'yield', special_generation='pending-list', extras=[messages, int(user_status.extra), total_pages])
        elif event.message.message == self.button_messages['message-review']['reject']:
            channel_message_id = int(user_status.extra.split(',')[0])
            is_ok = await self.repository.set_channel_message_verdict('r', user_status.user_id, channel_message_id, db_connection)
            user_status.state = 'pending-list'
            user_status.extra = user_status.extra.split(',')[1]
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)

            if is_ok:
                await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'message-review', 'reject', no_buttons=True)
                await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'pending-list', 'yield', special_generation='pending-list', extras=[messages, int(user_status.extra), total_pages])
            else:
                await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'message-review', 'not-found', no_buttons=True)
                await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'pending-list', 'yield', special_generation='pending-list', extras=[messages, int(user_status.extra), total_pages])
        else:
            await self.frontend.answer(event.message.input_sender, user_status, 'message-review', 'message-review', 'unknown')
        
    async def notify_admins(self, db_connection: aiomysql.Connection):
        admin_users = await self.repository.get_admin_users(db_connection)
        for admin_user in admin_users:
            input_user = await self.telethonBot.get_input_entity(int(admin_user.user_tid))
            await self.frontend.notify_admin(input_user)

    async def send_to_channel(self, channel_message_id, user_status: UserStatus, db_connection: aiomysql.Connection):
        message = await self.repository.get_channel_message(channel_message_id, db_connection)
        sender_user_status = await self.repository.get_user_status(message.from_user, db_connection)
        input_sender = await self.telethonBot.get_input_entity(int(sender_user_status.user_tid))
        await self.frontend.edit_inline(input_sender, message.message_tid, 'user-message-approved', 'main', str(message.channel_message_id))
        await self.frontend.notify_sender_approved(input_sender, message.message_tid)

        channel = await self.telethonBot.get_input_entity(self.channel_id)
        await self.frontend.send_to_channel(channel, message, user_status)

    async def get_paginated_pending_messages(self, user_status: UserStatus, db_connection: aiomysql.Connection):
        no_pending_messages = await self.repository.get_no_pending_messages(db_connection)
        total_pages = math.ceil(no_pending_messages / self.pending_page_size)
        if total_pages < int(user_status.extra):
            user_status.extra = total_pages
        if int(user_status.extra) < 1:
            user_status.extra = '1'
        
        messages = await self.repository.get_pending_messages_sorted((int(user_status.extra) - 1) * self.pending_page_size, self.pending_page_size, db_connection)
        return messages, total_pages

    async def is_rate_limited(self, user_status: UserStatus):
        if user_status.last_message_at == None:
            return False
        now = datetime.utcnow()
        time_passed = now - user_status.last_message_at
        if time_passed.total_seconds() < self.limit_anonymous_gap:
            return True
        return False

    async def is_member_of_channel(self, sender: EntityLike):
        channel = await self.telethonBot.get_input_entity(self.channel_id)
        async for user in self.telethonBot.iter_participants(channel, search=sender.first_name):
            if user.id == sender.id:
                return True
        return False

    async def start(self):
        self.logger.info('Not So Anonymous is at work!')
        await self.telethonBot.run_until_disconnected()
