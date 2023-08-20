import re
import logging
import aiomysql
from datetime import datetime
from model.user_status import UserStatus
from model.channel_message import ChannelMessage
from model.admin import Admin

class Repository:
    def __init__(self):
        self.logger = logging.getLogger('not_so_anonymous')
        self.db_pool: aiomysql.Pool = None
        self.db_name: str = None
    
    async def open_anonymous_connection(self) -> aiomysql.Connection:
        db_connection: aiomysql.Connection = await self.db_pool.acquire()
        await db_connection.begin()
        return db_connection

    async def open_connection(self) -> aiomysql.Connection:
        db_connection: aiomysql.Connection = await self.db_pool.acquire()
        await db_connection.select_db(self.db_name)
        await db_connection.begin()
        return db_connection
    
    async def commit_connection(self, db_connection: aiomysql.Connection):
        await db_connection.commit()
        db_connection.close()
        self.db_pool.release(db_connection)

    async def rollback_connection(self, db_connection: aiomysql.Connection):
        await db_connection.rollback()
        db_connection.close()
        self.db_pool.release(db_connection)

    async def initialize(self, db_name, host, port, user, password):
        self.db_name = db_name
        self.db_pool: aiomysql.Pool = await aiomysql.create_pool(host=host, port=port, user=user, password=password)

        db_connection: aiomysql.Connection = await self.open_anonymous_connection()
        cursor: aiomysql.Cursor = await db_connection.cursor()

        await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
        await cursor.execute(f"USE {self.db_name}")

        meta_command = open('src/sql/meta.sql', 'r').read()
        await cursor.execute(meta_command)
        migration_command = open('src/sql/migration.sql', 'r').read()
        await cursor.execute(migration_command)

        await cursor.close()
        await self.commit_connection(db_connection)

    async def create_channel_message(self, from_user, message, media, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        now_date = datetime.utcnow()
        sql_statement = """
            INSERT INTO channel_message (message_tid, from_user, message, media, verdict, reviewed_by, sent_at, reviewed_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = ('?', from_user, message, media, 'w', None, now_date, None,)
        await cursor.execute(sql_statement, values)
        channel_message_id = cursor.lastrowid
        await cursor.close()
        return channel_message_id

    async def set_channel_message_tid(self, channel_message_id, message_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE channel_message SET message_tid = %s WHERE message_tid = "?" AND channel_message_id = %s;
        """
        values = (message_tid, channel_message_id,)
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
            UPDATE user_status SET is_admin = %s, mask_name = %s, is_masked = %s, state = %s, extra = %s, last_message_at = %s WHERE user_id = %s;
        """
        values = (user_status.is_admin, user_status.mask_name, user_status.is_masked, user_status.state, user_status.extra, user_status.last_message_at, user_status.user_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()
    
    async def create_user_status(self, user_tid, is_admin, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            INSERT INTO user_status (user_tid, is_admin, mask_name, is_masked, state, extra, last_message_at) VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        values = (user_tid, is_admin, None, False, 'home', None, None,)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def get_admin(self, user_tid, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM admin WHERE user_tid = %s;
        """
        values = (user_tid,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return Admin(*result)

    async def get_admin_users(self, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM user_status WHERE is_admin = TRUE;
        """
        values = ()
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchall()
        await cursor.close()
        return UserStatus.cook(result)