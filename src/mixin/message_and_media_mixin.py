import aiomysql
from model.user_status import UserStatus

class MessageAndMediaMixin:
    async def verify_message_and_media(self, event, user_status: UserStatus, db_connection: aiomysql.Connection):
        input_sender, media = event.message.input_sender, None
        if event.message.media != None:
            if hasattr(event.message.media, 'photo'):
                media = event.message.media.photo
            elif hasattr(event.message.media, 'document'):
                media = event.message.media.document
            else:
                user_status.state = 'home'
                await self.repository.user_status.set_user_status(user_status, db_connection)
                await self.frontend.send_state_message(input_sender, 
                                                        'sending', 'not_supported', {},
                                                        'home', { 'button_messages': self.button_messages, 'user_status': user_status })
                return (None, None)
            
        if (media != None and MessageAndMediaMixin.utf8len(event.message.message) > self.constant.limit.media_message_size or 
            media == None and MessageAndMediaMixin.utf8len(event.message.message) > self.constant.limit.simple_message_size):
            user_status.state = 'home'
            await self.repository.user_status.set_user_status(user_status, db_connection)
            await self.frontend.send_state_message(input_sender, 
                                                    'sending', 'too_big', {}, 
                                                    'home', { 'button_messages': self.button_messages, 'user_status': user_status })
            return (None, None)
        
        return (event.message.message, media)
    
    @staticmethod
    def utf8len(s):
        return len(s.encode('utf-8'))