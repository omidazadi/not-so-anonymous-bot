from telethon.hints import EntityLike
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors.rpcerrorlist import UserNotParticipantError
from model.user_status import UserStatus

class MemberCheckMixin:
    async def is_member_of_channel(self, user_status: UserStatus):
        sender_entity = await self.telethon_bot.get_input_entity(int(user_status.user_tid))
        input_channel = await self.telethon_bot.get_input_entity(self.config.channel.id)
        try:
            await self.telethon_bot(GetParticipantRequest(channel=input_channel, participant=sender_entity))
            return True
        except Exception as e:
            if isinstance(e, UserNotParticipantError):
                return False
            raise e