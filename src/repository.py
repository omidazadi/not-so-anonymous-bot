import re
import aiosqlite
from datetime import datetime
from model.user_status import UserStatus
from model.message import Message

class Repository:
    def __init__(self):
        pass

    async def initialize(self, sqlite_db):
        self.db_connection: aiosqlite.Connection = await aiosqlite.connect('{}.db'.format(sqlite_db))
        init_commands = re.split('(?<=;)', open('src/ddl.sql', 'r').read())
        cursor = await self.db_connection.cursor()
        for command in init_commands:
            await cursor.execute(command)
        await cursor.close()
        await self.db_connection.commit()

    async def create_message(self, message):
        cursor = await self.db_connection.cursor()
        now_date = datetime.now().isoformat()
        sql_statement = """
            INSERT INTO message (message, verdict, reviewd_by, issued_at, reviewed_at) VALUES (?, ?, ?, ?, ?);
        """
        values = (message, 'p', None, now_date, None,)
        await cursor.execute(sql_statement, values)
        await cursor.close()
        await self.db_connection.commit()
    
    async def set_verdict(self, message_id, verdict):
        pass

    async def get_no_pending_messages(self):
        cursor = await self.db_connection.cursor()
        sql_statement = """
            SELECT COUNT(*) FROM message WHERE verdict = "p";
        """
        values = ()
        result = await (await cursor.execute(sql_statement, values)).fetchone()
        await cursor.close()
        return result
    
    async def get_pending_messages_sorted(self, offset, limit):
        cursor = await self.db_connection.cursor()
        sql_statement = """
            SELECT * FROM message WHERE verdict = "p" ORDER BY id DESC LIMIT ? OFFSET ?;
        """
        values = (offset, limit,)
        result = await (await cursor.execute(sql_statement, values)).fetchall()
        await cursor.close()
        return Message.cook(result)

    async def get_user_status(self, telegram_id):
        cursor = await self.db_connection.cursor()
        sql_statement = """
            SELECT * FROM user_status WHERE telegram_id = ?;
        """
        values = (telegram_id,)
        result = await (await cursor.execute(sql_statement, values)).fetchone()
        await cursor.close()
        if result == None:
            return None
        return UserStatus(*result)
    
    async def set_user_status(self, user_status: UserStatus):
        cursor = await self.db_connection.cursor()
        sql_statement = """
            UPDATE user_status SET state = ?, no_messages = ? WHERE telegram_id = ?;
        """
        values = (user_status.state, user_status.no_messages, user_status.telegram_id,)
        await cursor.execute(sql_statement, values)
        await cursor.close()
        await self.db_connection.commit()
    
    async def create_user_status(self, telegram_id):
        cursor = await self.db_connection.cursor()
        sql_statement = """
            INSERT INTO user_status (telegram_id, state, no_messages) VALUES (?, ?, ?);
        """
        values = (telegram_id, 'home', 0)
        await cursor.execute(sql_statement, values)
        await cursor.close()
        await self.db_connection.commit()