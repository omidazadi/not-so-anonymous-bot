from datetime import datetime
import logging
import aiomysql
from model.peer_message import PeerMessage

class PeerMessageRepository:
    def __init__(self):
        self.logger = logging.getLogger('not_so_anonymous')

    async def create_channel_peer_message(self, channel_message_reply, user_id, message, media, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        now_date = datetime.utcnow()
        sql_statement = """
            INSERT INTO peer_message (channel_message_reply, peer_message_reply, from_message_tid, to_message_tid, from_user, message, media, condition, sent_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = (channel_message_reply, None, '?', '?', user_id, message, media, 'w', now_date)
        await cursor.execute(sql_statement, values)
        peer_message_id = cursor.lastrowid
        await cursor.close()
        return peer_message_id
    
    async def delete_peer_message(self, peer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            DELETE FROM peer_message WHERE peer_message_id = %s;
        """
        values = (peer_message_id)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def get_peer_message(self, peer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT * FROM peer_message WHERE peer_message_id = %s;
        """
        values = (peer_message_id)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return PeerMessage(*result)

    async def set_from_message_tid(self, peer_message_id, from_message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE peer_message SET from_message_tid = %s WHERE peer_message_id = %s;
        """
        values = (from_message_tid, peer_message_id)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def set_to_message_tid(self, peer_message_id, to_message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE peer_message SET to_message_tid = %s WHERE peer_message_id = %s;
        """
        values = (to_message_tid, peer_message_id)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def get_no_replies(self, channel_message_id, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM peer_message WHERE channel_message_reply = %s AND from_user = %s;
        """
        values = (channel_message_id, user_id)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return result[0]
    
    async def send_the_waiting_peer_message(self, peer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE peer_message SET condition = "z" WHERE condition = "w" AND peer_message_id = %s;
        """
        values = (peer_message_id,)
        await cursor.execute(sql_statement, values)

        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def delete_the_waiting_peer_message(self, peer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            DELETE FROM peer_message_id WHERE condition = "w" AND peer_message_id = %s;
        """
        values = (peer_message_id,)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok