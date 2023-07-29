import math
import logging
import json
import bcrypt
from telethon import TelegramClient, events
from telethon.hints import EntityLike
from frontend import Frontend
from repository import Repository
from model.user_status import UserStatus

class Bot:
    def __init__(self):
        pass

    async def initialize(self, api_id, api_hash, bot_token, channel_id, admin_password_hash, page_size, sqlite_db):
        self.logger = logging.getLogger('not_so_anonymous')
        self.channel_id: str = channel_id
        self.admin_password_hash: bytes = admin_password_hash
        self.page_size: int = page_size
        self.sqlite_db: str = sqlite_db
        self.telethonBot: TelegramClient = await TelegramClient('bot', api_id, api_hash, base_logger=logging.getLogger('telethon')).start(bot_token=bot_token)
        self.repository = Repository()
        await self.repository.initialize(sqlite_db)
        self.frontend = Frontend(self.telethonBot)
        self.button_messages = json.load(open('resources/button.json', 'r'))
        self.is_paused = False
        self.hook_handler_to_telethon()

    def hook_handler_to_telethon(self):
        @self.telethonBot.on(events.NewMessage())
        async def general_message_handler(event):
            if not hasattr(event.message.input_sender, 'user_id'):
                return
            
            if self.is_paused:
                await self.frontend.maintenance_mode(event.message.input_sender)
                return

            user_id = str(event.message.input_sender.user_id)
            user_status = await self.repository.get_user_status(user_id)
            if user_status == None:
                await self.repository.create_user_status(user_id)
                user_status = await self.repository.get_user_status(user_id)

            if user_status.state == 'home':
                await self.home_handler(user_status, event)
            elif user_status.state == 'sending':
                await self.sending_handler(user_status, event)
            elif user_status.state == 'admin-auth':
                await self.admin_auth_handler(user_status, event)
            elif user_status.state == 'admin-home':
                await self.admin_home_handler(user_status, event)
            elif user_status.state == 'pending-list':
                await self.pending_list_handler(user_status, event)
            elif user_status.state == 'message-review':
                await self.message_review_handler(user_status, event)
            
    async def home_handler(self, user_status: UserStatus, event):
        if event.message.message == self.button_messages['home']['hidden-start']:
            await self.frontend.answer(event.message.input_sender, 'home', 'home', 'main', arguments=[self.channel_id])
        elif event.message.message == self.button_messages['home']['hidden-admin']:
            user_status.state = 'admin-auth'
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'home', 'admin-auth', 'yield')
        elif event.message.message == self.button_messages['home']['send-message']:
            sender = await self.telethonBot.get_entity(event.message.input_sender)
            if await self.is_member_of_channel(sender):
                user_status.state = 'sending'
                await self.repository.set_user_status(user_status)
                await self.frontend.answer(event.message.input_sender, 'home', 'sending', 'yield')
            else:
                await self.frontend.answer(event.message.input_sender, 'home', 'home', 'must-be-a-member', arguments=[self.channel_id])
        else:
            await self.frontend.answer(event.message.input_sender, 'home', 'home', 'unknown')

    async def sending_handler(self, user_status: UserStatus, event):
        if event.message.message == self.button_messages['sending']['hidden-start']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'sending', 'home', 'yield', arguments=[self.channel_id])
        elif event.message.message == self.button_messages['sending']['discard']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'sending', 'home', 'discard')
        else:
            await self.repository.create_message(event.message.message)
            user_status.state = 'home'
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'sending', 'home', 'success')
            await self.notify_admins()

    async def admin_auth_handler(self, user_status: UserStatus, event):
        if event.message.message == self.button_messages['admin-auth']['hidden-start']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'admin-auth', 'home', 'wink')
        elif event.message.message == self.button_messages['admin-auth']['back']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'admin-auth', 'home', 'wink')
        else:
            if bcrypt.checkpw(bytes(event.message.message, 'utf-8'), self.admin_password_hash):
                user_status.state = 'admin-home'
                await self.repository.set_user_status(user_status)
                await self.frontend.answer(event.message.input_sender, 'admin-auth', 'admin-home', 'correct', no_buttons=True)
                await self.frontend.answer(event.message.input_sender, 'admin-home', 'admin-home', 'main')
            else:
                user_status.state = 'home'
                await self.repository.set_user_status(user_status)
                await self.frontend.answer(event.message.input_sender, 'admin-auth', 'home', 'incorrect')

    async def admin_home_handler(self, user_status: UserStatus, event):
        if event.message.message == self.button_messages['admin-home']['hidden-start']:
            await self.frontend.answer(event.message.input_sender, 'admin-home', 'admin-home', 'main')
        elif event.message.message == self.button_messages['admin-home']['exit']:
            user_status.state = 'home'
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'admin-home', 'home', 'yield')
        elif event.message.message == self.button_messages['admin-home']['refresh']:
            await self.frontend.answer(event.message.input_sender, 'admin-home', 'admin-home', 'main')
        elif event.message.message == self.button_messages['admin-home']['pending-list']:
            user_status.state = 'pending-list'
            user_status.extra = '1'
            messages = self.get_paginated_pending_messages(user_status)
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'admin-home', 'pending-list', 'yield', arguments=[messages])
        else:
            await self.frontend.answer(event.message.input_sender, 'admin-home', 'admin-home', 'unknown')

    async def pending_list_handler(self, user_status: UserStatus, event):
        if event.message.message == self.button_messages['pending-list']['hidden-start']:
            user_status.state = 'admin-home'
            user_status.extra = None
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'pending-list', 'admin-home', 'yield')
        elif event.message.message == self.button_messages['pending-list']['back']:
            user_status.state = 'admin-home'
            user_status.extra = None
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'pending-list', 'admin-home', 'yield')
        elif event.message.message == self.button_messages['pending-list']['next']:
            user_status.extra = str(int(user_status.extra) + 1)
            messages = self.get_paginated_pending_messages(user_status)
            await self.frontend.answer(event.message.input_sender, 'pending-list', 'pending-list', 'main', arguments=[messages])
        elif event.message.message == self.button_messages['pending-list']['previous']:
            user_status.extra = str(int(user_status.extra) - 1)
            messages = self.get_paginated_pending_messages(user_status)
            await self.frontend.answer(event.message.input_sender, 'pending-list', 'pending-list', 'main', arguments=[messages])
        else:
            if event.message.message.isnumeric():
                id = int(event.message.message)
                message = await self.repository.get_pending_message(id)
                if message != None:
                    user_status.state = 'message-review'
                    #user_status.extra = 
                    await self.frontend.answer(event.message.input_sender, 'pending-list', 'message-review', 'yield')
                else:
                    await self.frontend.answer(event.message.input_sender, 'pending-list', 'pending-list', 'unknown')
            else:
                await self.frontend.answer(event.message.input_sender, 'pending-list', 'pending-list', 'unknown')

    async def message_review_handler(self, user_status: UserStatus, event):
        if event.message.message == self.button_messages['message-review']['hidden-start']:
            user_status.state = 'pending-list'
            user_status.extra = '1'
            messages = self.get_paginated_pending_messages(user_status)
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'message-review', 'pending-list', 'yield', arguments=[messages])
        elif event.message.message == self.button_messages['message-review']['back']:
            user_status.state = 'pending-list'
            user_status.extra = '1'
            messages = self.get_paginated_pending_messages(user_status)
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'message-review', 'pending-list', 'yield', arguments=[messages])
        elif event.message.message == self.button_messages['message-review']['accept']:
            user_status.state = 'pending-list'
            user_status.extra = '1'
            messages = self.get_paginated_pending_messages(user_status)
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'message-review', 'pending-list', 'yield', arguments=[messages])
        elif event.message.message == self.button_messages['message-review']['reject']:
            user_status.state = 'pending-list'
            user_status.extra = '1'
            messages = self.get_paginated_pending_messages(user_status)
            await self.repository.set_user_status(user_status)
            await self.frontend.answer(event.message.input_sender, 'message-review', 'pending-list', 'yield', arguments=[messages])
        else:
            await self.frontend.answer(event.message.input_sender, 'message-review', 'message-review', 'unknown')
        
    async def notify_admins():
        pass

    async def get_paginated_pending_messages(self, user_status: UserStatus):
        no_pending_messages = await self.repository.get_no_pending_messages()
        if math.ceil(no_pending_messages / self.page_size) < int(user_status.extra):
            user_status.extra = str(math.ceil(no_pending_messages / self.page_size))
        if user_status.extra < 1:
            user_status.extra = '1'
        
        messages = await self.repository.get_pending_messages_sorted((int(user_status.extra) - 1) * self.page_size, self.page_size)
        return messages

    async def is_member_of_channel(self, sender: EntityLike):
        channel = await self.telethonBot.get_input_entity(self.channel_id)
        async for user in self.telethonBot.iter_participants(channel, search=sender.username):
            if user.username == sender.username:
                return True
        return False

    async def start(self):
        self.logger.info('Not So Anonymous is at work!')
        await self.telethonBot.run_until_disconnected()
