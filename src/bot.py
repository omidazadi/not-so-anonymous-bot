import logging
import json
import aiomysql
from telethon import TelegramClient, events
from neo_frontend import Frontend
from repository.database_manager import DatabaseManager
from repository.admin_repo import AdminRepo
from repository.channel_message_repo import ChannelMessageRepo
from repository.user_status_repo import UserStatusRepo
from handler.message.home_handler import HomeHandler
from handler.message.sending_handler import SendingHandler
from handler.message.admin_auth_handler import AdminAuthHandler
from handler.message.admin_home_handler import AdminHomeHandler
from handler.message.pending_list_handler import PendingListHandler
from handler.message.message_review_handler import MessageReviewHandler
from config import Config
from constant import Constant

class Bot:
    def __init__(self, config: Config, constant: Constant):
        self.config = config
        self.constant = constant

    async def initialize(self):
        self.logger = logging.getLogger('not_so_anonymous')

        self.telethon_bot: TelegramClient = await TelegramClient('bot', self.config.telegram.api_id, self.config.telegram.api_hash, 
                                                                 base_logger=logging.getLogger('telethon')).start(bot_token=self.config.telegram.bot_token)
        self.database_manager = DatabaseManager(self.config.mysql)
        await self.database_manager.initialize()
        self.admin_repo = AdminRepo()
        self.channel_message_repo = ChannelMessageRepo()
        self.user_status_repo = UserStatusRepo()

        self.frontend = Frontend(self.telethon_bot, self.config, self.constant)
        self.button_messages = json.load(open('ui/state_button.json', 'r', encoding='utf-8'))

        self.home_handler = HomeHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                        self.user_status_repo)
        self.sending_handler = SendingHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                        self.user_status_repo, self.channel_message_repo)
        self.admin_auth_handler = AdminAuthHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                        self.user_status_repo, self.channel_message_repo, self.admin_repo)
        self.admin_home_handler = AdminHomeHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                        self.user_status_repo, self.channel_message_repo)
        self.pending_list_handler = PendingListHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                        self.user_status_repo, self.channel_message_repo)
        

        self.hook_handler_to_telethon()

    def hook_handler_to_telethon(self):
        @self.telethon_bot.on(events.CallbackQuery())
        async def general_callback_handler(event):
            self.logger.info('Incoming callback!')

            if self.config.app.maintenance:
                return
            
            data = bytes.decode(event.data, 'utf-8')
            print(data)
            return
            db_connection = await self.re.open_connection()

            try:
                if data_payload.startswith('ump'):
                    if data_payload.startswith('ump_s'):
                        (channel_message_id, user_id,) = tuple(map(int, data_payload[5:].split(',')))
                        user_status = await self.repository.get_user_status(user_id, db_connection)
                        channel_message = await self.repository.get_channel_message(channel_message_id, db_connection)

                        if user_status != None or channel_message != None:
                            input_user = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
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
                            input_user = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
                            is_ok = await self.repository.delete_the_waiting_channel_message(channel_message_id, db_connection)
                            if is_ok:
                                await self.frontend.edit_inline(input_user, channel_message.message_tid, 'user-message-discard', 'main')
                            else:
                                await self.frontend.internal_error(input_user)

                await self.repository.commit_connection(db_connection)

                self.logger.info('Callback has been handled!')
            except Exception as e:
                await self.repository.rollback_connection(db_connection)
                raise e


        @self.telethon_bot.on(events.NewMessage())
        async def general_message_handler(event):
            self.logger.info('Incoming message!')

            if not hasattr(event.message.peer_id, 'user_id'):
                return
            
            if self.config.app.maintenance:
                return

            self.logger.info(f'Input sender: {event.message.input_sender}')
            
            db_connection = await self.database_manager.open_connection()

            try:
                user_tid = str(event.message.input_sender.user_id)
                user_status = await self.user_status_repo.get_user_status_by_tid(user_tid, db_connection)
                if user_status == None:
                    await self.user_status_repo.create_user_status(user_tid, db_connection)
                    user_status = await self.user_status_repo.get_user_status_by_tid(user_tid, db_connection)

                if user_status.state == 'home':
                    await self.home_handler.handle(user_status, event, db_connection)
                elif user_status.state == 'sending':
                    await self.sending_handler.handle(user_status, event, db_connection)
                elif user_status.state == 'admin_auth':
                    await self.admin_auth_handler.handle(user_status, event, db_connection)
                elif user_status.state == 'admin_home':
                    await self.admin_home_handler.handle(user_status, event, db_connection)
                elif user_status.state == 'pending_list':
                    await self.pending_list_handler.handle(user_status, event, db_connection)
                elif user_status.state == 'message_review':
                    await self.message_review_handler(user_status, event, db_connection)

                await self.database_manager.commit_connection(db_connection)

                self.logger.info(f'Request has been completed!')
            except Exception as e:
                await self.database_manager.rollback_connection(db_connection)
                await self.frontend.internal_error(event.message.input_sender)
                raise e 

    async def notify_admins(self, db_connection: aiomysql.Connection):
        admin_users = await self.repository.get_admin_users(db_connection)
        for admin_user in admin_users:
            input_user = await self.telethon_bot.get_input_entity(int(admin_user.user_tid))
            await self.frontend.notify_admin(input_user)

    async def start(self):
        self.logger.info('Not So Anonymous is at work!')
        await self.telethon_bot.run_until_disconnected()
