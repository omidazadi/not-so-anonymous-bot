import logging
import aiomysql
from model.admin import Admin

class AdminRepository:
    def __init__(self):
        self.logger = logging.getLogger('not_so_anonymous')

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