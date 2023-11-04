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
            INSERT IGNORE INTO veil (name, category, reserved_by, owned_by, reservation_status) VALUES(%s, %s, %s, %s, %s);
        """
        values = (name, category, None, None, 'free')
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def get_veil(self, name, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM veil WHERE name = %s;
        """
        values = (name)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return Veil(*result)
    
    async def set_veil(self, veil: Veil, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE veil SET reserved_by = %s, owned_by = %s, reservation_status = %s WHERE name = %s;
        """
        values = (veil.reserved_by, veil.owned_by, veil.reservation_status, veil.name)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def craft_veil(self, name, category, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            INSERT INTO veil (name, category, reserved_by, owned_by, reservation_status) VALUES(%s, %s, %s, %s, %s);
        """
        values = (name, category, None, None, 'manually_reserved')
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def modify_veil(self, old_name, new_name, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE veil SET name = %s WHERE name = %s;
        """
        values = (new_name, old_name)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def destroy_veil(self, name, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            DELETE FROM veil WHERE name = %s
        """
        values = (name)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def manually_reserve_veil(self, name, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE veil SET reservation_status = %s WHERE reservation_status = %s AND name = %s;
        """
        values = ('manually_reserved', 'free', name)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def free_veil(self, name, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE veil SET reservation_status = %s WHERE reservation_status = %s AND name = %s;
        """
        values = ('free', 'manually_reserved', name)
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def has_automatically_reserved_veils(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT COUNT(*) FROM veil WHERE reserved_by = %s AND reservation_status = %s;
        """
        values = (user_id, 'automatically_reserved')
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        return (True if result[0] > 0 else False)
    
    async def get_automatically_reserved_veils(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()

        sql_statement = """
            SELECT * FROM veil WHERE reserved_by = %s AND reservation_status = %s;
        """
        values = (user_id, 'automatically_reserved')
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchall()
        return Veil.cook(result)
    
    async def release_automatic_reservations(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE veil SET reserved_by = %s, reservation_status = %s WHERE reserved_by = %s AND reservation_status = %s;
        """
        values = (None, 'free', user_id, 'automatically_reserved')
        await cursor.execute(sql_statement, values)
        
        is_ok = (True if cursor.rowcount > 0 else False)
        await cursor.close()
        return is_ok
    
    async def get_random_veil(self, category, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM veil WHERE reservation_status = %s AND category = %s ORDER BY RAND() LIMIT 1 FOR SHARE;
        """
        values = ('free', category)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return Veil(*result)
    
    async def get_owned_veils(self, user_id, db_connection: aiomysql.Connection):
        self.logger.info('Repository has been accessed!')
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM veil WHERE owned_by = %s;
        """
        values = (user_id)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchall()
        return Veil.cook(result)