import logging
import aiomysql
from model.block import Block

class BlockRepository:
    def __init__(self):
        self.logger = logging.getLogger('not_so_anonymous')

    async def block(self, user_id, blocked, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            INSERT INTO block (user_id, blocked) VALUES (%s, %s);
        """
        values = (user_id, blocked,)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def unblock(self, user_id, blocked, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            DELETE FROM block WHERE user_id = %s AND blocked = %s;
        """
        values = (user_id, blocked,)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def is_blocked_by(self, user_id_1, user_id_2, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM block WHERE user_id = %s AND blocked = %s;
        """
        values = (user_id_1, user_id_2,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return (True if result[0] > 0 else False)
    
    async def get_no_blocked_users(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM block WHERE user_id = %s;
        """
        values = (user_id,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return result[0]
    
    async def get_blocked_users(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT * FROM block WHERE user_id = %s;
        """
        values = (user_id,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchall()
        await cursor.close()
        return Block.cook(result)