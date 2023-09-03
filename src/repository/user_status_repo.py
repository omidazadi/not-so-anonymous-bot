import logging
import aiomysql
from model.user_status import UserStatus

class UserStatusRepo:
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
            UPDATE user_status SET veil = %s, is_veiled = %s, state = %s, extra = %s, last_message_at = %s WHERE user_id = %s;
        """
        values = (user_status.veil, user_status.is_veiled, user_status.state, user_status.extra, user_status.last_message_at, user_status.user_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()
    
    async def create_user_status(self, user_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            INSERT INTO user_status (user_tid, veil, is_veiled, state, extra, last_message_at) VALUES (%s, %s, %s, %s, %s, %s);
        """
        values = (user_tid, None, False, 'home', None, None,)
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