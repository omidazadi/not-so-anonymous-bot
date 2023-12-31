import logging
import aiomysql
from model.user_status import UserStatus
from model.peer_message import PeerMessage
from handler.callback.base_handler import BaseHandler
from mixin.reciever_mixin import RecieverMixin
from mixin.report_mixin import ReportMixin

class IncomingReplyHandler(RecieverMixin, ReportMixin, BaseHandler):
    def __init__(self, config, constant, telethon_bot, button_messages, frontend, repository, veil_manager):
        super().__init__(config, constant, telethon_bot, button_messages, frontend, repository, veil_manager)
        self.logger = logging.getLogger('not_so_anonymous')

    async def handle(self, sender_status: UserStatus, inline_senario, inline_button, data, db_connection: aiomysql.Connection):
        self.logger.info(f'incoming_reply handler!')

        peer_message = await self.repository.peer_message.get_peer_message(int(data), db_connection)
        if peer_message == None:
            return
        
        user_status = await self.repository.user_status.get_user_status(peer_message.from_user, db_connection)
        (reciever_status, message_tid) = await self.get_peer_reciever(peer_message, db_connection)
        if sender_status.user_id != reciever_status.user_id:
            return
        
        input_sender = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
        input_reciever = await self.telethon_bot.get_input_entity(int(reciever_status.user_tid))
        if inline_senario == 's':
            if peer_message.message_status != 'z':
                return
            
            if inline_button == 'o':
                to_message_tid = None
                if await self.repository.block.is_blocked_by(reciever_status.user_id, user_status.user_id, db_connection):
                    to_message_tid = await self.frontend.send_inline_message(input_reciever, 'incoming_reply', 'opened_blocked', 
                                                                             { 'message': peer_message },
                                                                             { 'peer_message_id': peer_message.peer_message_id },
                                                                             media=peer_message.media, reply_to=message_tid)
                else:
                    to_message_tid = await self.frontend.send_inline_message(input_reciever, 'incoming_reply', 'opened', 
                                                                             { 'message': peer_message },
                                                                             { 'peer_message_id': peer_message.peer_message_id },
                                                                             media=peer_message.media, reply_to=message_tid)
                if to_message_tid == None:
                    return
                
                await self.repository.peer_message.set_to_message_tid(peer_message.peer_message_id, to_message_tid, db_connection)
                await self.frontend.delete_inline_message(peer_message.to_notification_tid)
                
                await self.repository.peer_message.seen_peer_message(peer_message.peer_message_id, db_connection)
                await self.frontend.edit_inline_message(input_sender, peer_message.from_message_tid, 'outgoing_reply', 'sent_seen', 
                                                        { 'message': peer_message },
                                                        {})
        elif inline_senario == 'o':
            if (peer_message.message_status != 's' or
                await self.repository.block.is_blocked_by(reciever_status.user_id, user_status.user_id, db_connection)):
                return
            
            if inline_button == 'a':
                await self.goto_peer_reply_state(input_reciever, peer_message, reciever_status, db_connection)
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
                                                        reply_to=peer_message.to_message_tid)
            elif inline_button == 'r':
                is_ok = await self.repository.peer_message.report_reply(peer_message.peer_message_id, db_connection)
                if is_ok:
                    await self.frontend.send_inline_message(input_reciever, 'notification', 'successfully_reported', 
                                                            {},
                                                            {},
                                                            reply_to=peer_message.to_message_tid)
                    await self.notify_admins_new_report(db_connection)
                else:
                    await self.frontend.send_inline_message(input_reciever, 'notification', 'already_reported', 
                                                            {},
                                                            {},
                                                            reply_to=peer_message.to_message_tid)
        elif inline_senario == 'b':
            if (peer_message.message_status != 's' or
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
                                                        reply_to=peer_message.to_message_tid)
    
    async def goto_peer_reply_state(self, input_sender, peer_message: PeerMessage, user_status: UserStatus, db_connection: aiomysql.Connection):
        admin_states = ['admin_home', 'pending_list', 'message_review', 'ban_menu']
        prev_state = ('admin_home' if ((user_status.state in admin_states) or 
                      (user_status.state == 'channel_reply' and user_status.extra.split(',')[0] == 'admin_home') or
                      (user_status.state == 'peer_reply' and user_status.extra.split(',')[0] == 'admin_home')) else 'home')
        user_status.state = 'peer_reply'
        user_status.extra = f'{prev_state},{peer_message.peer_message_id}'

        if peer_message.message_status != 's':
            (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
            user_status.state = user_status.extra.split(',')[0]
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'not_found', {},
                                                   return_button_state, return_button_kws)
            return
        
        if await self.repository.peer_message.is_already_replied(peer_message.peer_message_id, db_connection):
            (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'already_replied', {},
                                                   return_button_state, return_button_kws)
            user_status.state = user_status.extra.split(',')[0]
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            return

        if not await self.is_member_of_channel(user_status):
            (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
            user_status.state = user_status.extra.split(',')[0]
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'must_be_a_member', { 'channel_id': self.config.channel.id },
                                                   return_button_state, return_button_kws)
            return
        
        if await self.repository.block.is_blocked_by(peer_message.from_user, user_status.user_id, db_connection):
            (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                    'common', 'you_are_blocked', {},
                                                    return_button_state, return_button_kws)
            user_status.state = user_status.extra.split(',')[0]
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            return
            
        if await self.repository.block.is_blocked_by(user_status.user_id, peer_message.from_user, db_connection):
            (return_button_state, return_button_kws) = await self.get_return_button_state_for_reply(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                   'common', 'he_is_blocked', {},
                                                   return_button_state, return_button_kws)
            user_status.state = user_status.extra.split(',')[0]
            user_status.extra = None
            await self.repository.user_status.set_user_status(user_status, db_connection)
            return
        
        await self.frontend.send_state_message(input_sender, 
                                               'peer_reply', 'main', {},
                                               'peer_reply', { 'button_messages': self.button_messages })
        await self.repository.user_status.set_user_status(user_status, db_connection)
        
    async def get_return_button_state_for_reply(self, user_status: UserStatus, db_connection: aiomysql.Connection):
        prev_state = user_status.extra.split(',')[0]
        if prev_state == 'home':
            return ('home', { 'button_messages': self.button_messages, 'user_status': user_status })
        else:
            return ('admin_home', { 'button_messages': self.button_messages })
