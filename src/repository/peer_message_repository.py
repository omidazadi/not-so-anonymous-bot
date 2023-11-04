from datetime import datetime
import logging
import aiomysql
from model.peer_message import PeerMessage

class PeerMessageRepository:
    def __init__(self):
        self.logger = logging.getLogger('not_so_anonymous')

    async def create_channel_peer_message(self, channel_message_reply, from_user, from_user_veil, message, media, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        now_date = datetime.utcnow()
        sql_statement = """
            INSERT INTO peer_message (channel_message_reply, peer_message_reply, from_message_tid, to_notification_tid, to_message_tid, from_user, from_user_veil, message, media, message_status, sent_at, is_reported, is_report_reviewed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = (channel_message_reply, None, '?', '?', '?', from_user, from_user_veil, message, media, 'w', now_date, False, False)
        await cursor.execute(sql_statement, values)
        peer_message_id = cursor.lastrowid
        await cursor.close()
        return peer_message_id
    
    async def create_peer_peer_message(self, peer_message_reply, from_user, from_user_veil, message, media, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        now_date = datetime.utcnow()
        sql_statement = """
            INSERT INTO peer_message (channel_message_reply, peer_message_reply, from_message_tid, to_notification_tid, to_message_tid, from_user, from_user_veil, message, media, message_status, sent_at, is_reported, is_report_reviewed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = (None, peer_message_reply, '?', '?', '?', from_user, from_user_veil, message, media, 'w', now_date, False, False)
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
    
    async def is_already_replied(self, peer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM peer_message WHERE peer_message_reply = %s AND (message_status = "z" OR message_status = "s");
        """
        values = (peer_message_id)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return (False if result[0] == 0 else True)

    async def set_from_message_tid(self, peer_message_id, from_message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE peer_message SET from_message_tid = %s WHERE peer_message_id = %s;
        """
        values = (from_message_tid, peer_message_id)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def set_to_notification_tid(self, peer_message_id, to_notification_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE peer_message SET to_notification_tid = %s WHERE peer_message_id = %s;
        """
        values = (to_notification_tid, peer_message_id)
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
            SELECT COUNT(*) FROM peer_message WHERE channel_message_reply = %s AND from_user = %s AND (message_status = "z" OR message_status = "s");
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
            UPDATE peer_message SET message_status = "z" WHERE message_status = "w" AND peer_message_id = %s;
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
            DELETE FROM peer_message WHERE message_status = "w" AND peer_message_id = %s;
        """
        values = (peer_message_id,)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def seen_peer_message(self, peer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE peer_message SET message_status = "s" WHERE message_status = "z" AND peer_message_id = %s;
        """
        values = (peer_message_id,)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def report_reply(self, peer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE peer_message SET is_reported = TRUE WHERE is_reported = FALSE AND peer_message_id = %s;
        """
        values = (peer_message_id,)
        await cursor.execute(sql_statement, values)

        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def get_a_report(self, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT * FROM peer_message WHERE is_reported = TRUE AND is_report_reviewed = FALSE;
        """
        values = ()
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return PeerMessage(*result)
    
    async def get_no_reports(self, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM peer_message WHERE is_reported = TRUE AND is_report_reviewed = FALSE;
        """
        values = ()
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return result[0]
    
    async def review_report(self, peer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE peer_message SET is_report_reviewed = TRUE WHERE is_report_reviewed = FALSE AND peer_message_id = %s;
        """
        values = (peer_message_id,)
        await cursor.execute(sql_statement, values)

        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def get_tail_replies(self, sender_user_id, reciever_user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            (
                SELECT pm1.* FROM peer_message pm1 INNER JOIN peer_message pm2 on pm1.peer_message_reply = pm2.peer_message_id
                WHERE pm1.message_status = "s" AND pm1.from_user = %s AND pm2.from_user = %s AND NOT EXISTS (
                    SELECT 1 FROM peer_message pm3 WHERE pm3.peer_message_reply = pm1.peer_message_id 
                )
            )
            UNION
            (
                SELECT pm1.* FROM peer_message pm1 INNER JOIN channel_message pm2 on pm1.channel_message_reply = pm2.channel_message_id
                WHERE pm1.message_status = "s" AND pm1.from_user = %s AND pm2.from_user = %s AND NOT EXISTS (
                    SELECT 1 FROM peer_message pm3 WHERE pm3.peer_message_reply = pm1.peer_message_id 
                )
            )
        """
        values = (sender_user_id, reciever_user_id, sender_user_id, reciever_user_id,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchall()
        await cursor.close()
        return PeerMessage.cook(result)
    
    async def get_no_user_peer_messages(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM peer_message WHERE from_user = %s;
        """
        values = (user_id)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return result[0]