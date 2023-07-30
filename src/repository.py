import re
import aiosqlite
from datetime import datetime
from model.user_status import UserStatus
from model.message import Message

class Repository:
    def __init__(self, db_name):
        self.db_name = db_name

    async def open_connection(self) -> aiosqlite.Connection:
        db_connection: aiosqlite.Connection = await aiosqlite.connect(f'{self.db_name}.db', isolation_level=None)
        await db_connection.execute('BEGIN')
        return db_connection
    
    async def commit_connection(self, db_connection: aiosqlite.Connection):
        await db_connection.execute('COMMIT')
        await db_connection.close()

    async def rollback_connection(self, db_connection: aiosqlite.Connection):
        await db_connection.execute('ROLLBACK')
        await db_connection.close()

    async def initialize(self):
        db_connection = await self.open_connection()
        init_commands = re.split('(?<=;)', open('src/ddl.sql', 'r').read())
        cursor = await db_connection.cursor()
        for command in init_commands:
            await cursor.execute(command)
        await cursor.close()
        await self.commit_connection(db_connection)

    async def create_message(self, message, db_connection: aiosqlite.Connection):
        cursor = await db_connection.cursor()
        now_date = datetime.now().isoformat()
        sql_statement = """
            INSERT INTO message (message, verdict, reviewed_by, sent_at, reviewed_at) VALUES (?, ?, ?, ?, ?);
        """
        values = (message, 'p', None, now_date, None,)
        await cursor.execute(sql_statement, values)
        await cursor.close()
    
    async def set_verdict(self, verdict, user_id, message_id, db_connection: aiosqlite.Connection):
        cursor = await db_connection.cursor()
        now_date = datetime.now().isoformat()
        sql_statement = """
            UPDATE message SET verdict = ?, reviewed_by = ?, reviewed_at = ? WHERE id = ?;
        """
        values = (verdict, user_id, now_date, message_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def get_no_pending_messages(self, db_connection: aiosqlite.Connection):
        cursor = await db_connection.cursor()
        sql_statement = """
            SELECT COUNT(*) FROM message WHERE verdict = "p";
        """
        values = ()
        result = await (await cursor.execute(sql_statement, values)).fetchone()
        await cursor.close()
        return result[0]
    
    async def get_pending_messages_sorted(self, offset, limit, db_connection: aiosqlite.Connection):
        cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM message WHERE verdict = "p" ORDER BY id DESC LIMIT ? OFFSET ?;
        """
        values = (limit, offset,)
        result = await (await cursor.execute(sql_statement, values)).fetchall()
        await cursor.close()
        return Message.cook(result)
    
    async def get_message(self, id, db_connection: aiosqlite.Connection):
        cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM message WHERE id = ?;
        """
        values = (id,)
        result = await (await cursor.execute(sql_statement, values)).fetchone()
        await cursor.close()
        if result == None:
            return None
        return Message(*result)

    async def get_user_status(self, telegram_id, db_connection: aiosqlite.Connection):
        cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM user_status WHERE telegram_id = ?;
        """
        values = (telegram_id,)
        result = await (await cursor.execute(sql_statement, values)).fetchone()
        await cursor.close()
        if result == None:
            return None
        return UserStatus(*result)
    
    async def set_user_status(self, user_status: UserStatus, db_connection: aiosqlite.Connection):
        cursor = await db_connection.cursor()
        sql_statement = """
            UPDATE user_status SET state = ?, extra = ?, no_messages = ?, last_message_at = ? WHERE telegram_id = ?;
        """
        values = (user_status.state, user_status.extra, user_status.no_messages, user_status.last_message_at, user_status.telegram_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()
    
    async def create_user_status(self, telegram_id, db_connection: aiosqlite.Connection):
        cursor = await db_connection.cursor()
        sql_statement = """
            INSERT INTO user_status (telegram_id, state, extra, no_messages, last_message_at) VALUES (?, ?, ?, ?, ?);
        """
        values = (telegram_id, 'home', None, 0, None,)
        await cursor.execute(sql_statement, values)
        await cursor.close()

    async def get_admins(self, db_connection: aiosqlite.Connection):
        cursor = await db_connection.cursor()
        sql_statement = """
            SELECT * FROM user_status WHERE state IN ("admin-home", "pending-list", "message-review");
        """
        values = ()
        result = await (await cursor.execute(sql_statement, values)).fetchall()
        await cursor.close()
        if result == None:
            return None
        return UserStatus.cook(result)