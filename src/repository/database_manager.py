import os
import logging
import aiomysql
from config import Config
from model.meta_data import MetaData

class DatabaseManager:
    def __init__(self, config: Config.Mysql):
        self.logger = logging.getLogger('not_so_anonymous')
        self.config = config
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

    async def initialize(self):
        self.db_name = self.config.db
        self.db_pool: aiomysql.Pool = await aiomysql.create_pool(host=self.config.host, port=self.config.port, user=self.config.user, 
                                                                 password=self.config.password, maxsize=self.config.pool_size)

        db_connection: aiomysql.Connection = await self.open_anonymous_connection()
        await self.execute_initial_commands(db_connection)
        version = await self.execute_migration_commands(db_connection)
        await self.execute_final_commands(version, db_connection)
        await self.commit_connection(db_connection)

    async def execute_initial_commands(self, db_connection: aiomysql.Connection):
        cursor: aiomysql.Cursor = await db_connection.cursor()
        await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
        await cursor.execute(f"USE {self.db_name}")
        initial_commands = open('src/sql/initial.sql', 'r').read()
        await cursor.execute(initial_commands)
        await cursor.close()

    async def execute_migration_commands(self, db_connection: aiomysql.Connection):
        version, migration_number = await self.get_meta_data('version', db_connection), '0000'
        while os.path.exists(f'src/sql/migration/migration_{migration_number}.sql'):
            migration_version = (await self.get_meta_data(f'migration_{migration_number}', db_connection)).meta_value
            if version.meta_value >= migration_version:
                migration_number = DatabaseManager.next_migration_number(migration_number)
                continue

            cursor: aiomysql.Cursor = await db_connection.cursor()
            migration_commands = open(f'src/sql/migration/migration_{migration_number}.sql', 'r').read()
            await cursor.execute(migration_commands)
            await cursor.close()

            version.meta_value = migration_version
            migration_number = DatabaseManager.next_migration_number(migration_number)
        
        return version

    async def execute_final_commands(self, version: MetaData, db_connection: aiomysql.Connection):
        await self.set_meta_data(version, db_connection)

    async def get_meta_data(self, key, db_connection: aiomysql.Connection):
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM meta_data WHERE meta_key = %s;
        """
        values = (key,)
        await cursor.execute(sql_statement, values)
        result = await cursor.fetchone()
        await cursor.close()
        if result == None:
            return None
        return MetaData(*result)
    
    async def set_meta_data(self, meta_data: MetaData, db_connection: aiomysql.Connection):
        cursor: aiomysql.Cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE meta_data SET meta_value = %s WHERE meta_key = %s;
        """
        values = (meta_data.meta_value, meta_data.meta_key,)
        await cursor.execute(sql_statement, values)
        await cursor.close()
    
    @staticmethod
    def next_migration_number(migration_number):
        int_migration_number = int(migration_number) + 1
        return ((4 - len(str(int_migration_number))) * '0') + str(int_migration_number)