import logging
import json
from telethon import TelegramClient, utils
from telethon.tl.functions.messages import SendMediaRequest, SendMessageRequest
from telethon.tl.types import KeyboardButton, KeyboardButtonCallback, KeyboardButtonRow, \
    ReplyKeyboardMarkup, ReplyInlineMarkup, InputReplyToMessage, UpdateShortSentMessage, \
    Updates, UpdateMessageID

class Frontend():
    def __init__(self, telethonBot: TelegramClient, pending_preview_length: int, channel_id: str):
        self.logger = logging.getLogger('not_so_anonymous')
        self.telethonBot = telethonBot
        self.pending_preview_length = pending_preview_length
        self.channel_id = channel_id
        self.button_messages = json.load(open('resources/button.json', 'r', encoding='utf-8'))
        self.inline_messages = json.load(open('resources/inline.json', 'r', encoding='utf-8'))
        self.ui_messages = json.load(open('resources/ui.json', 'r', encoding='utf-8'))

    async def internal_error(self, user):
        message = self.ui_messages['internal-error']
        await self.telethonBot.send_message(user, message)

    async def maintenance_mode(self, user):
        message = self.ui_messages['maintenance']
        await self.telethonBot.send_message(user, message)

    async def notify_admin(self, user):
        message = self.ui_messages['notify-admin']
        await self.telethonBot.send_message(user, message)

    async def notify_sender_approved(self, user, message_tid):
        message = self.ui_messages['notify-sender-approved']
        await self.telethonBot.send_message(user, message, reply_to=int(message_tid))

    def make_final_name(self, user_status):
        if not user_status.is_masked or not user_status.mask_name:
            return self.ui_messages['default-mask-name']
        return user_status.mask_name

    def make_final_message(self, message, user_status, plain=False):
        decorated_message = (self.ui_messages['channel-header'].format(self.make_final_name(user_status)) + 
                             '\n\n' + message + '\n\n' +
                             self.ui_messages['channel-footer'].format(self.channel_id))
        if plain:
            return decorated_message
        message_text, message_entities = utils.sanitize_parse_mode('md').parse(decorated_message)
        return message_text, message_entities

    async def send_to_channel(self, channel_id, message, user_status):
        message_text, message_entities = self.make_final_message(message.message, user_status)
        inline_buttons = self.generate_inline_buttons('channel-message', str(message.channel_message_id))
        if message.media == None:
            await self.telethonBot(SendMessageRequest(peer=channel_id, message=message_text, entities=message_entities, 
                                                      reply_markup=inline_buttons))
        else:
            await self.telethonBot(SendMediaRequest(peer=channel_id, message=message_text, media=message.media, 
                                                    entities=message_entities, reply_markup=inline_buttons))
            
    async def send_user_message_preview(self, user, channel_message_id, message_text, media, user_status):
        updates, inline_buttons = None, self.generate_inline_buttons('user-message-preview',
                                                                     str(channel_message_id) + ',' + str(user_status.user_id))
        message_text, message_entities = self.make_final_message(message_text, user_status)
        if media == None:
            updates = await self.telethonBot(SendMessageRequest(peer=user, message=message_text, entities=message_entities, 
                                                               reply_markup=inline_buttons))
        else:
            updates = await self.telethonBot(SendMediaRequest(peer=user, message=message_text, media=media, 
                                                    entities=message_entities, reply_markup=inline_buttons))
        print(updates)
        if isinstance(updates, UpdateShortSentMessage):
            return updates.id
        elif isinstance(updates, Updates):
            for update in updates.updates:
                if isinstance(update, UpdateMessageID):
                    return update.id
        raise ValueError

    def generate_pending_list_view(self, extras):
        if len(extras[0]) == 0:
            return self.ui_messages['states']['pending-list']['main']['empty']
        text = self.ui_messages['states']['pending-list']['main']['header'].format(extras[1], extras[2]) + '\n\n'
        for i in range(len(extras[0])):
            channel_message = extras[0][i]
            preview_message = channel_message.message
            if len(preview_message) > self.pending_preview_length:
                preview_message = preview_message[0:self.pending_preview_length] + '...'
            media_status = self.ui_messages['states']['pending-list']['main']['yes-no'][('yes' if channel_message.media != None else 'no')]
            text += self.ui_messages['states']['pending-list']['main']['line'].format(media_status, channel_message.channel_message_id, preview_message)
            if i < len(extras[0]) - 1:
                text += '\n\n'
        return text
    
    def generate_inline_buttons(self, senario, data_payload):
        if not senario in self.inline_messages:
            return None
        
        rows = []
        for button_row in self.inline_messages[senario]['buttons']:
            row = []
            for button_option in button_row:
                row.append(KeyboardButtonCallback(text=self.inline_messages[senario][button_option]['text'], 
                                                  data=bytes(self.inline_messages[senario][button_option]['data_header'] + data_payload, 'utf-8')))
            rows.append(KeyboardButtonRow(buttons=row))

        buttons = ReplyInlineMarkup(rows=rows)
        return buttons
    
    def generate_keyboard_buttons(self, to_state, special_generation, extras):
        rows = []
        for button_row in self.button_messages[to_state]['hidden-buttons']:
            row = []
            for button_option in button_row:
                row.append(KeyboardButton(text=self.button_messages[to_state][button_option]))
            rows.append(KeyboardButtonRow(buttons=row))

        if special_generation != None:
            if special_generation == 'pending-list':
                if len(extras[0]) > 0:
                    row = []
                    for channel_message in extras[0]:
                        row.append(KeyboardButton(text=str(channel_message.channel_message_id)))
                    rows.append(KeyboardButtonRow(buttons=row))
        
        buttons = ReplyKeyboardMarkup(rows=rows, resize=True, persistent=True)
        return buttons

    async def answer(self, user, user_status, from_state, to_state, edge, special_generation=None, arguments=[], extras=[], no_buttons=False, reply_to=None):
        self.logger.info('Frontend answer!')

        message, media, reply_to_object = None, None, None
        if special_generation == None:
            if edge != 'yield':
                message = self.ui_messages['states'][from_state][edge]
            else:
                message = self.ui_messages['states'][to_state]['main']

            message = message.format(*arguments)
        else:
            if special_generation == 'pending-list':
                message = self.generate_pending_list_view(extras)
            elif special_generation == 'message-review':
                message = self.make_final_message(extras[0].message, user_status, plain=True)
                media = extras[0].media

        if reply_to != None:
            reply_to_object = InputReplyToMessage(reply_to_msg_id=int(reply_to))
        message_text, message_entities = utils.sanitize_parse_mode('md').parse(message)

        if no_buttons:
            await self.telethonBot(SendMessageRequest(peer=user, message=message_text, entities=message_entities, reply_to=reply_to_object))
        else:
            buttons = self.generate_keyboard_buttons(to_state, special_generation, extras)

            if special_generation != None:
                if special_generation == 'message-review':
                    if extras[0].media == None:
                        await self.telethonBot(SendMessageRequest(peer=user, message=message_text, reply_markup=buttons, 
                                                                  entities=message_entities, reply_to=reply_to_object))
                    else:
                        await self.telethonBot(SendMediaRequest(peer=user, message=message_text, media=media, reply_markup=buttons, 
                                                                entities=message_entities, reply_to=reply_to_object))
                elif special_generation == 'pending-list':
                    await self.telethonBot(SendMessageRequest(peer=user, message=message_text, reply_markup=buttons, entities=message_entities, 
                                                          reply_to=reply_to_object))
            else:
                await self.telethonBot(SendMessageRequest(peer=user, message=message_text, reply_markup=buttons, entities=message_entities, 
                                                          reply_to=reply_to_object))
    
    async def answer_inline(self, user, senario, key, reply_to=None):
        self.logger.info('Frontend inline answer!')
        await self.telethonBot.send_message(user, self.ui_messages['inline'][senario][key], reply_to=(None if reply_to == None else int(reply_to)))

    async def edit_inline(self, user, message_tid, senario, key, data_payload = ''):
        self.logger.info('Frontend inline edit!')
        message_text, inline_buttons = self.ui_messages['inline'][senario][key], self.generate_inline_buttons(senario, data_payload)
        if senario == 'user-message-queue':
            message_text = None
        if senario == 'user-message-approved':
            message_text = None
        await self.telethonBot.edit_message(user, int(message_tid), text=message_text, buttons=inline_buttons)