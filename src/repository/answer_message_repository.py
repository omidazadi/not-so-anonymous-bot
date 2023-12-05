from datetime import datetime
import logging
import aiomysql
from model.answer_message import AnswerMessage

class AnswerMessageRepository:
    def __init__(self):
        self.logger = logging.getLogger('not_so_anonymous')

    async def create_answer_message(self, channel_message_reply, from_user, from_user_veil, message, media, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        now_date = datetime.utcnow()
        sql_statement = """
            INSERT INTO answer_message (channel_message_reply, from_message_tid, to_notification_tid, to_message_tid, discussion_message_tid, from_user, from_user_veil, message, media, can_reply, message_status, is_reported, is_report_reviewed, sent_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = (channel_message_reply, '?', '?', '?', '?', from_user, from_user_veil, message, media, True, 'w', False, False, now_date)
        await cursor.execute(sql_statement, values)
        answer_message_id = cursor.lastrowid
        await cursor.close()
        return answer_message_id
    
    async def get_answer_message(self, answer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        
        sql_statement = """
            SELECT * FROM answer_message WHERE answer_message_id = %s;
        """
        values = (answer_message_id,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return AnswerMessage(*result)
    
    async def set_from_message_tid(self, answer_message_id, from_message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET from_message_tid = %s WHERE answer_message_id = %s;
        """
        values = (from_message_tid, answer_message_id)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def set_to_notification_tid(self, answer_message_id, to_notification_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET to_notification_tid = %s WHERE answer_message_id = %s;
        """
        values = (to_notification_tid, answer_message_id)
        await cursor.execute(sql_statement, values)
        await cursor.close()
    
    async def set_to_message_tid(self, answer_message_id, to_message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET to_message_tid = %s WHERE answer_message_id = %s;
        """
        values = (to_message_tid, answer_message_id)
        await cursor.execute(sql_statement, values)
        await cursor.close()
    
    async def set_discussion_message_tid(self, answer_message_id, discussion_message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET discussion_message_tid = %s WHERE answer_message_id = %s;
        """
        values = (discussion_message_tid, answer_message_id)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def report_reply(self, answer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET is_reported = TRUE WHERE is_reported = FALSE AND answer_message_id = %s;
        """
        values = (answer_message_id,)
        await cursor.execute(sql_statement, values)

        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def get_a_report(self, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT * FROM answer_message WHERE is_reported = TRUE AND is_report_reviewed = FALSE;
        """
        values = ()
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return AnswerMessage(*result)
    
    async def get_no_reports(self, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM answer_message WHERE is_reported = TRUE AND is_report_reviewed = FALSE;
        """
        values = ()
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return result[0]
    
    async def review_report(self, answer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET is_report_reviewed = TRUE WHERE is_report_reviewed = FALSE AND answer_message_id = %s;
        """
        values = (answer_message_id,)
        await cursor.execute(sql_statement, values)

        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def get_tail_replies(self, sender_user_id, reciever_user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT pm1.* FROM answer_message pm1 INNER JOIN channel_message pm2 on pm1.channel_message_reply = pm2.channel_message_id
            WHERE pm1.message_status = "s" AND pm1.from_user = %s AND pm2.from_user = %s AND NOT EXISTS (
                SELECT 1 FROM peer_message pm3 WHERE pm3.peer_message_reply = pm1.answer_message_id 
            )
        """
        values = (sender_user_id, reciever_user_id,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchall()
        await cursor.close()
        return AnswerMessage.cook(result)
    
    async def close_reply(self, answer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET can_reply = FALSE WHERE message_status = "a" AND answer_message_id = %s;
        """
        values = (answer_message_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def open_reply(self, answer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET can_reply = TRUE WHERE message_status = "a" AND answer_message_id = %s;
        """
        values = (answer_message_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def get_no_replies(self, channel_message_id, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM answer_message WHERE channel_message_reply = %s AND from_user = %s AND message_status != "w";
        """
        values = (channel_message_id, user_id)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return result[0]
    
    async def send_the_waiting_answer_message(self, answer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET message_status = "z" WHERE message_status = "w" AND answer_message_id = %s;
        """
        values = (answer_message_id,)
        await cursor.execute(sql_statement, values)

        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def delete_the_waiting_answer_message(self, answer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            DELETE FROM answer_message WHERE message_status = "w" AND answer_message_id = %s;
        """
        values = (answer_message_id,)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def seen_answer_message(self, answer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET message_status = "s" WHERE message_status = "z" AND answer_message_id = %s;
        """
        values = (answer_message_id,)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def accept_answer_message(self, answer_message_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            UPDATE answer_message SET message_status = "a" WHERE message_status = "s" AND answer_message_id = %s;
        """
        values = (answer_message_id,)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok