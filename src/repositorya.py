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
