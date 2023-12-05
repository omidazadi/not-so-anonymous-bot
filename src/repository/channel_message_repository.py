from datetime import datetime
import logging
import aiomysql
from model.channel_message import ChannelMessage

class ChannelMessageRepository:
    def __init__(self):
        self.logger = logging.getLogger('not_so_anonymous')

    async def create_channel_message(self, from_user, from_user_veil, message, media, is_public, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        now_date = datetime.utcnow()
        sql_statement = """
            INSERT INTO channel_message (message_tid, channel_message_tid, discussion_message_tid, from_user, from_user_veil, message, media, can_reply, is_public, verdict, reviewed_by, sent_at, reviewed_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = ('?', '?', '?', from_user, from_user_veil, message, media, True, is_public, 'w', None, now_date, datetime.fromisoformat('2000-01-01 00:00:00'),)
        await cursor.execute(sql_statement, values)
        channel_message_id = cursor.lastrowid
        await cursor.close()
        return channel_message_id

    async def set_message_tid(self, channel_message_id, message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE channel_message SET message_tid = %s WHERE message_tid = "?" AND channel_message_id = %s;
        """
        values = (message_tid, channel_message_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def set_channel_message_tid(self, channel_message_id, channel_message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE channel_message SET channel_message_tid = %s WHERE channel_message_tid = "?" AND channel_message_id = %s;
        """
        values = (channel_message_tid, channel_message_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def set_discussion_message_tid(self, channel_message_id, discussion_message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE channel_message SET discussion_message_tid = %s WHERE discussion_message_tid = "?" AND channel_message_id = %s;
        """
        values = (discussion_message_tid, channel_message_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()
    
    async def set_channel_message_verdict(self, verdict, user_id, channel_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        now_date = datetime.utcnow()
        sql_statement = """
            UPDATE channel_message SET verdict = %s, reviewed_by = %s, reviewed_at = %s WHERE verdict = "p" AND channel_message_id = %s;
        """
        values = (verdict, user_id, now_date, channel_message_id,)
        await cursor.execute(sql_statement, values)

        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def send_the_waiting_channel_message(self, channel_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE channel_message SET verdict = "p" WHERE verdict = "w" AND channel_message_id = %s;
        """
        values = (channel_message_id,)
        await cursor.execute(sql_statement, values)

        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def delete_the_waiting_channel_message(self, channel_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            DELETE FROM channel_message WHERE verdict = "w" AND channel_message_id = %s;
        """
        values = (channel_message_id,)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok

    async def get_no_pending_messages(self, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM channel_message WHERE verdict = "p";
        """
        values = ()
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return result[0]
    
    async def get_pending_messages_sorted(self, offset, limit, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT * FROM channel_message WHERE verdict = "p" ORDER BY channel_message_id DESC LIMIT %s OFFSET %s;
        """
        values = (limit, offset,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchall()
        await cursor.close()
        return ChannelMessage.cook(result)
    
    async def get_channel_message(self, channel_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        
        sql_statement = """
            SELECT * FROM channel_message WHERE channel_message_id = %s;
        """
        values = (channel_message_id,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return ChannelMessage(*result)
    
    async def get_channel_message_by_channel_message_tid(self, channel_message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        
        sql_statement = """
            SELECT * FROM channel_message WHERE channel_message_tid = %s;
        """
        values = (channel_message_tid,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return ChannelMessage(*result)
    
    async def close_reply(self, channel_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE channel_message SET can_reply = FALSE WHERE verdict = "a" AND channel_message_id = %s;
        """
        values = (channel_message_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def open_reply(self, channel_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE channel_message SET can_reply = TRUE WHERE verdict = "a" AND channel_message_id = %s;
        """
        values = (channel_message_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def get_no_user_channel_messages(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM channel_message WHERE from_user = %s;
        """
        values = (user_id)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return result[0]
