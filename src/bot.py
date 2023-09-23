import asyncio
import pickle
import logging
import json
import aiomysql
from telethon import TelegramClient, events
from frontend import Frontend
from veil_manager import VeilManager
from repository.database_manager import DatabaseManager
from repository.repository import Repository
from handler.message.home_handler import HomeHandler
from handler.message.sending_handler import SendingHandler
from handler.message.unblock_all_handler import UnblockAllHandler
from handler.message.admin_auth_handler import AdminAuthHandler
from handler.message.admin_home_handler import AdminHomeHandler
from handler.message.pending_list_handler import PendingListHandler
from handler.message.message_review_handler import MessageReviewHandler
from handler.message.ban_menu_handler import BanMenuHandler
from handler.message.channel_reply_handler import ChannelReplyHandler
from handler.message.peer_reply_handler import PeerReplyHandler
from handler.callback.channel_message_preview_handler import ChannelMessagePreviewHandler
from handler.callback.outgoing_reply_handler import OutgoingReplyHandler
from handler.callback.incoming_reply_handler import IncomingReplyHandler
from config import Config
from constant import Constant

class Bot:
    def __init__(self, config: Config, constant: Constant):
        self.config = config
        self.constant = constant

    async def initialize(self):
        self.logger = logging.getLogger('not_so_anonymous')
        self.locks: dict[str, asyncio.Lock] = dict()

        self.telethon_bot: TelegramClient = await TelegramClient('bot', self.config.telegram.api_id, self.config.telegram.api_hash, 
                                                                 base_logger=logging.getLogger('telethon')).start(bot_token=self.config.telegram.bot_token)
        self.database_manager = DatabaseManager(self.config.mysql)
        await self.database_manager.initialize()
        self.repository = Repository()

        self.frontend = Frontend(self.telethon_bot, self.config, self.constant)
        self.button_messages = json.load(open('ui/state_button.json', 'r', encoding='utf-8'))

        db_connection = await self.database_manager.open_connection()
        self.veil_manager = VeilManager(self.repository, self.config, self.constant)
        await self.veil_manager.initialize(db_connection)
        await self.database_manager.commit_connection(db_connection)

        self.home_handler = HomeHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                        self.repository)
        self.sending_handler = SendingHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                              self.repository)
        self.unblock_all_handler = UnblockAllHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                                     self.repository)
        self.admin_auth_handler = AdminAuthHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                                   self.repository)
        self.admin_home_handler = AdminHomeHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                                   self.repository)
        self.pending_list_handler = PendingListHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                                       self.repository)
        self.message_review_handler = MessageReviewHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                                           self.repository)
        self.channel_reply_handler = ChannelReplyHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                                         self.repository)
        self.peer_reply_handler = PeerReplyHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                                   self.repository)
        self.channel_message_preview_handler = ChannelMessagePreviewHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                                                            self.repository)
        self.ban_menu_handler = BanMenuHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                               self.repository)
        self.outgoing_reply_handler = OutgoingReplyHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                                           self.repository)
        self.incoming_reply_handler = IncomingReplyHandler(self.config, self.constant, self.telethon_bot, self.button_messages, self.frontend,
                                                           self.repository)

        self.hook_handler_to_telethon()

    def hook_handler_to_telethon(self):
        @self.telethon_bot.on(events.CallbackQuery())
        async def general_callback_handler(event):
            self.logger.info('Incoming callback!')

            if self.config.app.maintenance:
                input_sender = await self.telethon_bot.get_input_entity(event.original_update.user_id)
                await self.frontend.send_state_message(input_sender, 
                                                       'common', 'maintenance', {},
                                                       None, None)
                return
            
            [inline_type, inline_senario, inline_button, data] = bytes.decode(event.data, 'utf-8').split(',')
            db_connection = await self.database_manager.open_connection()

            try:
                user_tid = str(event.original_update.user_id)
                if not user_tid in self.locks:
                    self.locks[user_tid] = asyncio.Lock()
                async with self.locks[user_tid]:
                    user_status = await self.repository.user_status.get_user_status_by_tid(user_tid, db_connection)
                    if user_status == None:
                        await self.repository.user_status.create_user_status(user_tid, db_connection)
                        user_status = await self.repository.user_status.get_user_status_by_tid(user_tid, db_connection)

                    if user_status.is_banned:
                        input_sender = await self.telethon_bot.get_input_entity(event.original_update.user_id)
                        await self.frontend.send_state_message(input_sender, 
                                                               'common', 'banned', { 'channel_admin': self.config.channel.admin },
                                                               None, None)
                        return

                    if inline_type == 'cmp':
                        await self.channel_message_preview_handler.handle(user_status, inline_senario, inline_button, data, db_connection)
                    elif inline_type == 'or':
                        await self.outgoing_reply_handler.handle(user_status, inline_senario, inline_button, data, db_connection)
                    elif inline_type == 'ir':
                        await self.incoming_reply_handler.handle(user_status, inline_senario, inline_button, data, db_connection)

                    await self.database_manager.commit_connection(db_connection)

                    self.logger.info('Callback has been handled!')
            except Exception as e:
                await self.database_manager.rollback_connection(db_connection)
                raise e

        @self.telethon_bot.on(events.NewMessage())
        async def general_message_handler(event):
            self.logger.info('Incoming message!')

            if not hasattr(event.message.peer_id, 'user_id'):
                return
            
            if self.config.app.maintenance:
                await self.frontend.send_state_message(event.message.input_sender, 
                                                       'common', 'maintenance', {},
                                                       None, None)
                return

            self.logger.info(f'Input sender: {event.message.input_sender}')
            
            db_connection = await self.database_manager.open_connection()

            try:
                user_tid = str(event.message.input_sender.user_id)
                if not user_tid in self.locks:
                    self.locks[user_tid] = asyncio.Lock()
                
                async with self.locks[user_tid]:
                    user_status = await self.repository.user_status.get_user_status_by_tid(user_tid, db_connection)
                    if user_status == None:
                        await self.repository.user_status.create_user_status(user_tid, db_connection)
                        user_status = await self.repository.user_status.get_user_status_by_tid(user_tid, db_connection)

                    if user_status.is_banned:
                        await self.frontend.send_state_message(event.message.input_sender, 
                                                               'common', 'banned', { 'channel_admin': self.config.channel.admin },
                                                               None, None)
                        return

                    if user_status.state == 'home':
                        await self.home_handler.handle(user_status, event, db_connection)
                    elif user_status.state == 'sending':
                        await self.sending_handler.handle(user_status, event, db_connection)
                    elif user_status.state == 'unblock_all':
                        await self.unblock_all_handler.handle(user_status, event, db_connection)
                    elif user_status.state == 'admin_auth':
                        await self.admin_auth_handler.handle(user_status, event, db_connection)
                    elif user_status.state == 'admin_home':
                        await self.admin_home_handler.handle(user_status, event, db_connection)
                    elif user_status.state == 'pending_list':
                        await self.pending_list_handler.handle(user_status, event, db_connection)
                    elif user_status.state == 'message_review':
                        await self.message_review_handler.handle(user_status, event, db_connection)
                    elif user_status.state == 'ban_menu':
                        await self.ban_menu_handler.handle(user_status, event, db_connection)
                    elif user_status.state == 'channel_reply':
                        await self.channel_reply_handler.handle(user_status, event, db_connection)
                    elif user_status.state == 'peer_reply':
                        await self.peer_reply_handler.handle(user_status, event, db_connection)

                    await self.database_manager.commit_connection(db_connection)

                    self.logger.info(f'Request has been completed!')
            except Exception as e:
                await self.database_manager.rollback_connection(db_connection)
                await self.frontend.send_state_message(event.message.input_sender, 
                                                       'common', 'internal_error', {},
                                                       None, None)
                raise e 

    async def notify_admins(self, db_connection: aiomysql.Connection):
        admin_users = await self.repository.get_admin_users(db_connection)
        for admin_user in admin_users:
            input_user = await self.telethon_bot.get_input_entity(int(admin_user.user_tid))
            await self.frontend.notify_admin(input_user)

    async def start(self):
        self.logger.info('Not So Anonymous is at work!')
        await self.telethon_bot.run_until_disconnected()
