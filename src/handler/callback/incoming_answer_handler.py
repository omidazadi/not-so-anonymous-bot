import logging
import aiomysql
from model.user_status import UserStatus
from handler.callback.base_handler import BaseHandler
from mixin.reciever_mixin import RecieverMixin
from mixin.report_mixin import ReportMixin
from magical_emoji import MagicalEmoji

class IncomingAnswersHandler(RecieverMixin, ReportMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')
        self.magical_emoji = MagicalEmoji()

    async def handle(self, sender_status: UserStatus, inline_senario, inline_button, data, db_connection: aiomysql.Connection):
        self.logger.info(f'incoming_answer handler!')

        answer_message = await self.repository.answer_message.get_answer_message(int(data), db_connection)
        if answer_message == None:
            return
        
        user_status = await self.repository.user_status.get_user_status(answer_message.from_user, db_connection)
        (reciever_status, message_tid) = await self.get_peer_reciever(answer_message, db_connection)
        if sender_status.user_id != reciever_status.user_id:
            return
        
        input_sender = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
        input_reciever = await self.telethon_bot.get_input_entity(int(reciever_status.user_tid))
        if inline_senario == 'o':
            if (answer_message.message_status != 's' or
                await self.repository.block.is_blocked_by(reciever_status.user_id, user_status.user_id, db_connection)):
                return
            
            if inline_button == 'a':
                is_ok = await self.repository.answer_message.accept_answer_message(answer_message.answer_message_id, db_connection)
                if is_ok:
                    channel_message = await self.repository.channel_message.get_channel_message(answer_message.channel_message_reply, db_connection)
                    input_discussion = await self.telethon_bot.get_input_entity(self.config.channel.discussion)
                    discussion_message_tid = await self.frontend.send_discussion_message(input_discussion, 'answer', 
                                                                                         { 'message': answer_message },
                                                                                         { 'emoji': self.magical_emoji.get_random_emoji(), 'bot_id': self.config.bot.id, 'answer_message_id': answer_message.answer_message_id},
                                                                                         reply_to=channel_message.discusison_message_tid, media=answer_message.media)
                    await self.repository.answer_message.set_discussion_message_tid(answer_message.answer_message_id, discussion_message_tid, db_connection)
                    await self.frontend.edit_inline_message(input_reciever, answer_message.to_message_tid, 'incoming_answer', 'accepted', 
                                                            { 'message': answer_message },
                                                            { 'answer_message_id': answer_message.answer_message_id },
                                                            media=answer_message.media)
                    await self.frontend.edit_inline_message(input_sender, answer_message.from_message_tid, 'outgoing_answer', 'seen_accepted', 
                                                            { 'message': answer_message },
                                                            { 'answer_message_id': answer_message.answer_message_id },
                                                            media=answer_message.media)
                    await self.frontend.send_inline_message(input_sender, 'notification', 'answer_accepted', 
                                                            {},
                                                            {},
                                                            reply_to=answer_message.from_message_tid)
            elif inline_button == 'b':
                await self.repository.block.block(reciever_status.user_id, user_status.user_id, db_connection)
                peer_tail_replies = await self.repository.peer_message.get_tail_replies(user_status.user_id, reciever_status.user_id, db_connection)
                for tail_reply in peer_tail_replies:
                    await self.frontend.edit_inline_message(input_reciever, tail_reply.to_message_tid, 'incoming_reply', 'opened_blocked', 
                                                            { 'message': tail_reply },
                                                            { 'peer_message_id': tail_reply.peer_message_id },
                                                            media=tail_reply.media)
                answer_tail_replies = await self.repository.answer_message.get_tail_replies(user_status.user_id, reciever_status.user_id, db_connection)
                for tail_reply in answer_tail_replies:
                    await self.frontend.edit_inline_message(input_sender, tail_reply.to_message_tid, 'incoming_answer', 'opened_blocked', 
                                                            { 'message': tail_reply },
                                                            { 'answer_message_id': tail_reply.answer_message_id },
                                                            media=tail_reply.media)
                await self.frontend.send_inline_message(input_reciever, 'notification', 'successfully_blocked', 
                                                        {},
                                                        {},
                                                        reply_to=answer_message.to_message_tid)
            elif inline_button == 'r':
                is_ok = await self.repository.answer_message.report_reply(answer_message.answer_message_id, db_connection)
                if is_ok:
                    await self.frontend.send_inline_message(input_reciever, 'notification', 'successfully_reported', 
                                                            {},
                                                            {},
                                                            reply_to=answer_message.to_message_tid)
                    await self.notify_admins_new_report(db_connection)
                else:
                    await self.frontend.send_inline_message(input_reciever, 'notification', 'already_reported', 
                                                            {},
                                                            {},
                                                            reply_to=answer_message.to_message_tid)
        elif inline_senario == 'b':
            if (answer_message.message_status != 's' or
                not await self.repository.block.is_blocked_by(reciever_status.user_id, user_status.user_id, db_connection)):
                return
            
            if inline_button == 'u':
                await self.repository.block.unblock(reciever_status.user_id, user_status.user_id, db_connection)
                peer_tail_replies = await self.repository.peer_message.get_tail_replies(user_status.user_id, reciever_status.user_id, db_connection)
                for tail_reply in peer_tail_replies:
                    await self.frontend.edit_inline_message(input_reciever, tail_reply.to_message_tid, 'incoming_reply', 'opened', 
                                                            { 'message': tail_reply },
                                                            { 'peer_message_id': tail_reply.peer_message_id },
                                                            media=tail_reply.media)
                answer_tail_replies = await self.repository.answer_message.get_tail_replies(user_status.user_id, reciever_status.user_id, db_connection)
                for tail_reply in answer_tail_replies:
                    await self.frontend.edit_inline_message(input_sender, tail_reply.to_message_tid, 'incoming_answer', 'opened', 
                                                            { 'message': tail_reply },
                                                            { 'answer_message_id': tail_reply.answer_message_id },
                                                            media=tail_reply.media)
                await self.frontend.send_inline_message(input_reciever, 'notification', 'successfully_unblocked', 
                                                        {},
                                                        {},
                                                        reply_to=answer_message.to_message_tid)
        elif inline_senario == 'a':
            if answer_message.message_status != 'a':
                return
            
            if inline_button == 'd':
                input_discussion = await self.telethon_bot.get_input_entity(self.config.channel.discussion)
                await self.frontend.delete_inline_message(answer_message.to_message_tid)
                await self.frontend.delete_discussion_message(input_discussion, answer_message.discussion_message_tid)
