import aiomysql
from model.peer_message import PeerMessage

class RecieverMixin:
    async def get_reciever(self, peer_message: PeerMessage, db_connection: aiomysql.Connection):
        if peer_message.channel_message_reply != None:
            channel_message = await self.repository.channel_message.get_channel_message(peer_message.channel_message_reply, db_connection)
            reciever_status = await self.repository.user_status.get_user_status(channel_message.from_user, db_connection)
            return (reciever_status, channel_message.message_tid)
        else:
            peer_message = await self.repository.peer_message.get_peer_message(peer_message.peer_message_reply, db_connection)
            reciever_status = await self.repository.user_status.get_user_status(peer_message.from_user, db_connection)
            return (reciever_status, peer_message.from_message_tid)