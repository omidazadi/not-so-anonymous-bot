import aiomysql
from telethon.types import MessageMediaDocument
from model.user_status import UserStatus

class MessageAndMediaMixin:
    async def verify_message_and_media(self, event, return_state, user_status: UserStatus, db_connection: aiomysql.Connection):
        input_sender, media = event.message.input_sender, None
        if event.message.media != None:
            if hasattr(event.message.media, 'photo'):
                media = event.message.media.photo
            elif (hasattr(event.message.media, 'document') and 
                  not self.is_sticker(event.message.media)):
                media = event.message.media.document
            else:
                user_status.state = return_state
                await self.repository.user_status.set_user_status(user_status, db_connection)

                if return_state == 'home':
                    await self.frontend.send_state_message(input_sender, 
                                                           'common', 'not_supported', {},
                                                           'home', { 'button_messages': self.button_messages, 'user_status': user_status })
                elif return_state == 'admin_home':
                    await self.frontend.send_state_message(input_sender, 
                                                           'common', 'not_supported', {},
                                                           'admin_home', { 'button_messages': self.button_messages })
                return (None, None)
            
        if (media != None and MessageAndMediaMixin.utf8len(event.message.message) > self.constant.limit.media_message_size or 
            media == None and MessageAndMediaMixin.utf8len(event.message.message) > self.constant.limit.simple_message_size):
            user_status.state = return_state
            await self.repository.user_status.set_user_status(user_status, db_connection)
            
            if return_state == 'home':
                await self.frontend.send_state_message(input_sender, 
                                                       'common', 'too_big', {},
                                                       'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            elif return_state == 'admin_home':
                await self.frontend.send_state_message(input_sender, 
                                                       'common', 'too_big', {},
                                                       'admin_home', { 'button_messages': self.button_messages })
            return (None, None)
        
        return (event.message.message, media)
    
    def is_voice(self, media: MessageMediaDocument):
        dict = media.to_dict()
        if 'attributes' in dict['document']:
            for attribute in dict['document']['attributes']:
                if attribute['_'] == 'DocumentAttributeAudio':
                    if 'voice' in attribute and attribute['voice'] == True:
                        return True
        return False

    def is_sticker(self, media: MessageMediaDocument):
        dict = media.to_dict()
        if 'attributes' in dict['document']:
            for attribute in dict['document']['attributes']:
                if attribute['_'] == 'DocumentAttributeSticker':
                    return True
        return False
    
    @staticmethod
    def utf8len(s):
        return len(s.encode('utf-8'))