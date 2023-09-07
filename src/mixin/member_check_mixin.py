from telethon.hints import EntityLike

class MemberCheckMixin:
    async def is_member_of_channel(self, sender_entity: EntityLike):
        input_channel = await self.telethon_bot.get_input_entity(self.config.channel.id)
        async for user in self.telethon_bot.iter_participants(input_channel, search=sender_entity.first_name):
            if user.id == sender_entity.id:
                return True
        return False