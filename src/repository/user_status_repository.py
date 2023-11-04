from datetime import datetime, timedelta
import logging
import aiomysql
from model.user_status import UserStatus

class UserStatusRepository:
    def __init__(self):
        self.logger = logging.getLogger('not_so_anonymous')

    async def get_user_status(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM user_status WHERE user_id = %s;
        """
        values = (user_id,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return UserStatus(*result)

    async def get_user_status_by_tid(self, user_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM user_status WHERE user_tid = %s;
        """
        values = (user_tid,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return UserStatus(*result)
    
    async def set_user_status(self, user_status: UserStatus, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE user_status SET veil = %s, ticket = %s, state = %s, extra = %s, last_message_at = %s, is_banned = %s WHERE user_id = %s;
        """
        values = (user_status.veil, user_status.ticket, user_status.state, user_status.extra, user_status.last_message_at, user_status.is_banned, user_status.user_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()
    
    async def create_user_status(self, user_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            INSERT INTO user_status (user_tid, veil, state, extra, last_message_at, is_banned, ticket) VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        values = (user_tid, None, 'home', None, datetime.fromisoformat('2000-01-01 00:00:00'), False, 0)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def get_admin_users(self, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM user_status WHERE gen_is_admin = TRUE;
        """
        values = ()
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchall()
        await cursor.close()
        return UserStatus.cook(result)
    
    async def ban_user(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE user_status SET is_banned = TRUE WHERE is_banned = FALSE AND user_id = %s;
        """
        values = (user_id,)
        await cursor.execute(sql_statement, values)
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def unban_user(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE user_status SET is_banned = FALSE WHERE is_banned = TRUE AND user_id = %s;
        """
        values = (user_id,)
        await cursor.execute(sql_statement, values)
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def get_all_banned_users(self, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM user_status WHERE is_banned = TRUE;
        """
        values = ()
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchall()
        await cursor.close()
        return UserStatus.cook(result)
    
    async def get_ticket_candidates(self, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        start_date = datetime.utcnow() - timedelta(days=7)
        sql_statement = """
            SELECT * FROM user_status WHERE (
                EXISTS (
                    SELECT 1 FROM channel_message WHERE channel_message.sent_at > %s
                ) OR EXISTS (
                    SELECT 1 FROM peer_message WHERE peer_message.sent_at > %s
                )
            ) AND ticket = 0 AND (
                NOT EXISTS (
                    SELECT 1 FROM veil WHERE veil.reserved_by = user_status.user_id
                ) AND NOT EXISTS (
                    SELECT 1 FROM veil WHERE veil.owned_by = user_status.user_id
                )
            )
        """
        values = (start_date, start_date)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchall()
        await cursor.close()
        return UserStatus.cook(result)