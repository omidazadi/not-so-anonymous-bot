from telethon.hints import EntityLike
from telethon.tl.functions.users import GetUsersRequest

class MemberCheckMixin:
    async def is_member_of_channel(self, user_tid):
        sender_entity = (await self.telethon_bot(GetUsersRequest(id=[int(user_tid)])))[0]
        input_channel = await self.telethon_bot.get_input_entity(self.config.channel.id)
        async for user in self.telethon_bot.iter_participants(input_channel, search=sender_entity.first_name):
            if user.id == sender_entity.id:
                return True
        return False