import logging
import aiomysql
from model.veil import Veil

class VeilRepository:
    def __init__(self):
        self.logger = logging.getLogger('not_so_anonymous')

    async def load_veil(self, name, category, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            INSERT IGNORE INTO veil (name, category) VALUES(%s, %s)
        """
        values = (name, category)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def get_veil(self, name, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM veil WHERE name = %s
        """
        values = (name)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return Veil(*result)