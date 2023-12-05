import aiomysql
from model.peer_message import PeerMessage
from model.answer_message import AnswerMessage

class RecieverMixin:
    async def get_peer_reciever(self, peer_message: PeerMessage, db_connection: aiomysql.Connection):
        if peer_message.channel_message_reply != None:
            channel_message = await self.repository.channel_message.get_channel_message(peer_message.channel_message_reply, db_connection)
            reciever_status = await self.repository.user_status.get_user_status(channel_message.from_user, db_connection)
            return (reciever_status, channel_message.message_tid)
        elif peer_message.peer_message_reply != None:
            peer_message = await self.repository.peer_message.get_peer_message(peer_message.peer_message_reply, db_connection)
            reciever_status = await self.repository.user_status.get_user_status(peer_message.from_user, db_connection)
            return (reciever_status, peer_message.from_message_tid)
        else:
            answer_message = await self.repository.answer_message.get_answer_message(peer_message.answer_message_reply, db_connection)
            reciever_status = await self.repository.user_status.get_user_status(answer_message.from_user, db_connection)
            return (reciever_status, answer_message.from_message_tid)
        
    async def get_answer_reciever(self, answer_message: AnswerMessage, db_connection: aiomysql.Connection):
        channel_message = await self.repository.channel_message.get_channel_message(answer_message.channel_message_reply, db_connection)
        reciever_status = await self.repository.user_status.get_user_status(channel_message.from_user, db_connection)
        return (reciever_status, channel_message.message_tid)