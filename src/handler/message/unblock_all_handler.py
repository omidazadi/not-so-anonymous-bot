import logging
import aiomysql
from model.user_status import UserStatus
from handler.message.base_handler import BaseHandler

class UnblockAllHandler(BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        
    async def handle(self, user_status: UserStatus, event, db_connection: aiomysql.Connection):
        self.logger.info(f'unblock_all handler!')

        input_sender = event.message.input_sender
        if (event.message.message == self.button_messages['unblock_all']['hidden_start'] or
            event.message.message.startswith(self.button_messages['unblock_all']['hidden_start'] + ' ')):
            reply_type, channel_message_id_str = self.parse_hidden_start(event.message.message)
            if reply_type == None:
                user_status.state = 'home'
                user_status.extra = None
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                       'home', 'main', { 'user_status': user_status, 'channel_id': self.config.channel.id },
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            else:
                await self.goto_channel_reply_state(input_sender, 'home', channel_message_id_str, reply_type, user_status, db_connection)
        elif event.message.message == self.button_messages['unblock_all']['accept']:
            blocked_users = await self.repository.block.get_blocked_users(user_status.user_id, db_connection)
            for blocked_user in blocked_users:
                await self.repository.block.unblock(user_status.user_id, blocked_user.blocked, db_connection)
                peer_tail_replies = await self.repository.peer_message.get_tail_replies(blocked_user.blocked, user_status.user_id, db_connection)
                for tail_reply in peer_tail_replies:
                    await self.frontend.edit_inline_message(input_sender, tail_reply.to_message_tid, 'incoming_reply', 'opened', 
                                                            { 'message': tail_reply },
                                                            { 'peer_message_id': tail_reply.peer_message_id },
                                                            media=tail_reply.media)
                answer_tail_replies = await self.repository.answer_message.get_tail_replies(blocked_user.blocked, user_status.user_id, db_connection)
                for tail_reply in answer_tail_replies:
                    await self.frontend.edit_inline_message(input_sender, tail_reply.to_message_tid, 'incoming_answer', 'opened', 
                                                            { 'message': tail_reply },
                                                            { 'answer_message_id': tail_reply.answer_message_id },
                                                            media=tail_reply.media)
            user_status.state = 'home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'unblock_all', 'unblocked_all', {},
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        elif event.message.message == self.button_messages['unblock_all']['discard']:
            user_status.state = 'home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'unblock_all', 'discard', {},
                                                   'home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'unknown', {},
                                                   'unblock_all', { 'button_messages': self.button_messages })
