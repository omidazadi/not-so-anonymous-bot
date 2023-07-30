from datetime import datetime
import math
import logging
import json
import bcrypt
import aiosqlite
from telethon import TelegramClient, events
from telethon.hints import EntityLike
from frontend import Frontend
from repository import Repository
from model.user_status import UserStatus

class Bot:
    def __init__(self):
        pass

    async def initialize(self, api_id, api_hash, bot_token, channel_id, admin_password_hash, pending_page_size, pending_preview_length, sqlite_db, security_rate_limit):
        self.logger = logging.getLogger('not_so_anonymous')
        self.channel_id: str = channel_id
        self.admin_password_hash: bytes = admin_password_hash
        self.pending_page_size: int = pending_page_size
        self.pending_preview_length: int = pending_preview_length
        self.sqlite_db: str = sqlite_db
        self.security_rate_limit: int = security_rate_limit
        self.telethonBot: TelegramClient = await TelegramClient('bot', api_id, api_hash, base_logger=logging.getLogger('telethon')).start(bot_token=bot_token)
        self.repository = Repository(sqlite_db)
        await self.repository.initialize()
        self.frontend = Frontend(self.telethonBot, self.pending_preview_length)
        self.button_messages = json.load(open('resources/button.json', 'r', encoding='utf-8'))
        self.is_paused = False
        self.hook_handler_to_telethon()

    def hook_handler_to_telethon(self):
        @self.telethonBot.on(events.NewMessage())
        async def general_message_handler(event):
            if not hasattr(event.message.peer_id, 'user_id'):
                return
            
            if self.is_paused:
                await self.frontend.maintenance_mode(event.message.input_sender)
                return
            
            db_connection = await self.repository.open_connection()

            try:
                user_id = str(event.message.input_sender.user_id)
                user_status = await self.repository.get_user_status(user_id, db_connection)
                if user_status == None:
                    await self.repository.create_user_status(user_id, db_connection)
                    user_status = await self.repository.get_user_status(user_id, db_connection)

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
            except Exception as e:
                await self.repository.rollback_connection(db_connection)
                raise e
            
    async def home_handler(self, user_status: UserStatus, event, db_connection: aiosqlite.Connection):
        if event.message.message == self.button_messages['home']['hidden-start']:
            await self.frontend.answer(event.message.input_sender, 'home', 'home', 'main', arguments=[self.channel_id])
        elif event.message.message == self.button_messages['home']['hidden-admin']:
            user_status.state = 'admin-auth'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'home', 'admin-auth', 'yield')
        elif event.message.message == self.button_messages['home']['send-message']:
            sender = await self.telethonBot.get_entity(event.message.input_sender)
            if await self.is_member_of_channel(sender):
                if not await self.is_rate_limited(user_status):
                    user_status.state = 'sending'
                    await self.repository.set_user_status(user_status, db_connection)
                    await self.frontend.answer(event.message.input_sender, 'home', 'sending', 'yield')
                else:
                    await self.frontend.answer(event.message.input_sender, 'home', 'home', 'slow-down', arguments=[self.security_rate_limit])
            else:
                await self.frontend.answer(event.message.input_sender, 'home', 'home', 'must-be-a-member', arguments=[self.channel_id])
        else:
            await self.frontend.answer(event.message.input_sender, 'home', 'home', 'unknown')

    async def sending_handler(self, user_status: UserStatus, event, db_connection: aiosqlite.Connection):
        if event.message.message == self.button_messages['sending']['hidden-start']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'sending', 'home', 'yield', arguments=[self.channel_id])
        elif event.message.message == self.button_messages['sending']['discard']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'sending', 'home', 'discard')
        else:
            await self.repository.create_message(event.message.message, db_connection)
            user_status.state = 'home'
            user_status.no_messages += 1
            user_status.last_message_at = datetime.now().isoformat()
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'sending', 'home', 'success')
            await self.notify_admins(db_connection)

    async def admin_auth_handler(self, user_status: UserStatus, event, db_connection: aiosqlite.Connection):
        if event.message.message == self.button_messages['admin-auth']['hidden-start'] or \
            event.message.message == self.button_messages['admin-auth']['back']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'admin-auth', 'home', 'wink')
        else:
            if bcrypt.checkpw(bytes(event.message.message, 'utf-8'), self.admin_password_hash):
                no_pending_messages = await self.repository.get_no_pending_messages(db_connection)
                user_status.state = 'admin-home'
                await self.repository.set_user_status(user_status, db_connection)
                await self.frontend.answer(event.message.input_sender, 'admin-auth', 'admin-auth', 'correct', no_buttons=True)
                await self.frontend.answer(event.message.input_sender, 'admin-auth', 'admin-home', 'yield', arguments=[no_pending_messages])
            else:
                user_status.state = 'home'
                await self.repository.set_user_status(user_status, db_connection)
                await self.frontend.answer(event.message.input_sender, 'admin-auth', 'home', 'incorrect')

    async def admin_home_handler(self, user_status: UserStatus, event, db_connection: aiosqlite.Connection):
        if event.message.message == self.button_messages['admin-home']['hidden-start'] or \
            event.message.message == self.button_messages['admin-home']['refresh']:
            no_pending_messages = await self.repository.get_no_pending_messages(db_connection)
            await self.frontend.answer(event.message.input_sender, 'admin-home', 'admin-home', 'main', arguments=[no_pending_messages])
        elif event.message.message == self.button_messages['admin-home']['hidden-omidi']:
            await self.frontend.answer(event.message.input_sender, 'admin-home', 'admin-home', 'omidi')
        elif event.message.message == self.button_messages['admin-home']['exit']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'admin-home', 'home', 'yield', arguments=[self.channel_id])
        elif event.message.message == self.button_messages['admin-home']['pending-list']:
            user_status.state = 'pending-list'
            user_status.extra = '1'
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'admin-home', 'pending-list', 'yield', special_generation='pending-list', arguments=[messages, int(user_status.extra), total_pages])
        else:
            await self.frontend.answer(event.message.input_sender, 'admin-home', 'admin-home', 'unknown')

    async def pending_list_handler(self, user_status: UserStatus, event, db_connection: aiosqlite.Connection):
        if event.message.message == self.button_messages['pending-list']['hidden-start'] or \
            event.message.message == self.button_messages['pending-list']['back']:
            no_pending_messages = await self.repository.get_no_pending_messages(db_connection)
            user_status.state = 'admin-home'
            user_status.extra = None
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'pending-list', 'admin-home', 'yield', arguments=[no_pending_messages])
        elif event.message.message == self.button_messages['pending-list']['next']:
            user_status.extra = str(int(user_status.extra) + 1)
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'pending-list', 'pending-list', 'main', special_generation='pending-list', arguments=[messages, int(user_status.extra), total_pages])
        elif event.message.message == self.button_messages['pending-list']['previous']:
            user_status.extra = str(int(user_status.extra) - 1)
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'pending-list', 'pending-list', 'main', special_generation='pending-list', arguments=[messages, int(user_status.extra), total_pages])
        else:
            if event.message.message.isnumeric():
                id = int(event.message.message)
                message = await self.repository.get_message(id, db_connection)
                if message != None:
                    user_status.state = 'message-review'
                    user_status.extra = f'{str(message.id)},{user_status.extra}'
                    await self.repository.set_user_status(user_status, db_connection)
                    await self.frontend.answer(event.message.input_sender, 'pending-list', 'message-review', 'yield', arguments=[message.id, message.message])
                else:
                    await self.frontend.answer(event.message.input_sender, 'pending-list', 'pending-list', 'not-found')
            else:
                await self.frontend.answer(event.message.input_sender, 'pending-list', 'pending-list', 'not-found')

    async def message_review_handler(self, user_status: UserStatus, event, db_connection: aiosqlite.Connection):
        if event.message.message == self.button_messages['message-review']['hidden-start']:
            no_pending_messages = await self.repository.get_no_pending_messages(db_connection)
            user_status.state = 'admin-home'
            user_status.extra = None
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'message-review', 'admin-home', 'yield', arguments=[no_pending_messages])
        elif event.message.message == self.button_messages['message-review']['back']:
            user_status.state = 'pending-list'
            user_status.extra = user_status.extra.split(',')[1]
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'message-review', 'pending-list', 'yield', special_generation='pending-list', arguments=[messages, int(user_status.extra), total_pages])
        elif event.message.message == self.button_messages['message-review']['accept']:
            message_id = int(user_status.extra.split(',')[0])
            await self.repository.set_verdict('a', str(event.message.input_sender.user_id), message_id, db_connection)
            user_status.state = 'pending-list'
            user_status.extra = user_status.extra.split(',')[1]
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'message-review', 'message-review', 'accept', no_buttons=True)
            await self.frontend.answer(event.message.input_sender, 'message-review', 'pending-list', 'yield', special_generation='pending-list', arguments=[messages, int(user_status.extra), total_pages])
            await self.send_to_channel(message_id, db_connection)
        elif event.message.message == self.button_messages['message-review']['reject']:
            message_id = int(user_status.extra.split(',')[0])
            await self.repository.set_verdict('r', str(event.message.input_sender.user_id), message_id, db_connection)
            user_status.state = 'pending-list'
            user_status.extra = user_status.extra.split(',')[1]
            messages, total_pages = await self.get_paginated_pending_messages(user_status, db_connection)
            await self.repository.set_user_status(user_status, db_connection)
            await self.frontend.answer(event.message.input_sender, 'message-review', 'message-review', 'reject', no_buttons=True)
            await self.frontend.answer(event.message.input_sender, 'message-review', 'pending-list', 'yield', special_generation='pending-list', arguments=[messages, int(user_status.extra), total_pages])
        else:
            await self.frontend.answer(event.message.input_sender, 'message-review', 'message-review', 'unknown')
        
    async def notify_admins(self, db_connection: aiosqlite.Connection):
        admins = await self.repository.get_admins(db_connection)
        for admin in admins:
            input_user = await self.telethonBot.get_input_entity(int(admin.telegram_id))
            await self.frontend.notify_admin(input_user)

    async def send_to_channel(self, message_id, db_connection: aiosqlite.Connection):
        message = await self.repository.get_message(message_id, db_connection)
        channel = await self.telethonBot.get_input_entity(self.channel_id)
        await self.frontend.send_to_channel(channel, message.message)

    async def get_paginated_pending_messages(self, user_status: UserStatus, db_connection: aiosqlite.Connection):
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
        now = datetime.now()
        last_message = datetime.fromisoformat(user_status.last_message_at)
        time_passed = now - last_message
        if time_passed.total_seconds() < self.security_rate_limit:
            return True
        return False

    async def is_member_of_channel(self, sender: EntityLike):
        channel = await self.telethonBot.get_input_entity(self.channel_id)
        async for user in self.telethonBot.iter_participants(channel, search=sender.username):
            if user.username == sender.username:
                return True
        return False

    async def start(self):
        self.logger.info('Not So Anonymous is at work!')
        await self.telethonBot.run_until_disconnected()
