import aiomysql

class ReportMixin:
    async def notify_admins_new_report(self, db_connection: aiomysql.Connection):
        admin_states = ['admin_home', 'pending_list', 'message_review', 'ban_menu', 'veil_menu', 'direct_admin_id_phase', 'direct_admin_message_phase']
        admin_users = await self.repository.user_status.get_admin_users(db_connection)
        for admin_user in admin_users:
            if (admin_user.state in admin_states or
                (admin_user.state == 'channel_reply' and admin_user.extra.split(',')[0] == 'admin_home') or
                (admin_user.state == 'peer_reply' and admin_user.extra.split(',')[0] == 'admin_home')):
                input_user = await self.telethon_bot.get_input_entity(int(admin_user.user_tid))
                await self.frontend.send_inline_message(input_user, 'notification', 'admin_new_report', 
                                                        {},
                                                        {})