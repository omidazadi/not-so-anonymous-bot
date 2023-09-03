import math
import aiomysql
from model.user_status import UserStatus

class PaginatedPendingListMixin:
    async def get_paginated_pending_messages(self, user_status: UserStatus, db_connection: aiomysql.Connection):
        no_pending_messages = await self.channel_message_repo.get_no_pending_messages(db_connection)
        total_pages = math.ceil(no_pending_messages / self.constant.view.pending_list_page_size)
        if total_pages < int(user_status.extra):
            user_status.extra = total_pages
        if int(user_status.extra) < 1:
            user_status.extra = '1'
        
        messages = await self.channel_message_repo.get_pending_messages_sorted((int(user_status.extra) - 1) * self.constant.view.pending_list_page_size,
                                                                                self.constant.view.pending_list_page_size, db_connection)
        return messages, total_pages