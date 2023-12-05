import os
import asyncio
import logging
import json
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from telethon import TelegramClient, utils
from telethon.tl.functions.channels import DeleteMessagesRequest as DeleteMessagesRequestChannel
from telethon.tl.functions.messages import SendMediaRequest, SendMessageRequest, EditMessageRequest, \
    DeleteMessagesRequest
from telethon.tl.types import KeyboardButton, KeyboardButtonCallback, KeyboardButtonRow, \
    KeyboardButtonUrl, ReplyKeyboardMarkup, ReplyInlineMarkup, InputReplyToMessage, \
    UpdateShortSentMessage, Updates, UpdateMessageID
from config import Config
from constant import Constant
from decorator.ignore_rpc_errors import IgnoreRPCErrors

class Frontend():
    def __init__(self, telethon_bot: TelegramClient, config: Config, constant: Constant):
        self.logger = logging.getLogger('not_so_anonymous')
        self.telethon_bot = telethon_bot
        self.config = config
        self.constant = constant
        self.jinja_env = Environment(loader=FileSystemLoader('ui/template'), lstrip_blocks=True, trim_blocks=True)
        self.file_lock = asyncio.Lock()

        IgnoreRPCErrors.set_logger(self.logger)

    def generate_keyboard_buttons(self, buttons_json):
        rows = []
        for button_row in buttons_json:
            row = []
            for button_text in button_row:
                row.append(KeyboardButton(text=button_text))
            rows.append(KeyboardButtonRow(buttons=row))

        buttons = ReplyKeyboardMarkup(rows=rows, resize=True, persistent=True)
        return buttons
    
    def generate_inline_buttons(self, buttons_json):
        if len(buttons_json) == 0:
            return None
        
        rows = []
        for button_row in buttons_json:
            row = []
            for inline_button in button_row:
                row.append(KeyboardButtonCallback(text=inline_button['text'], data=inline_button['data']))
            rows.append(KeyboardButtonRow(buttons=row))

        buttons = ReplyInlineMarkup(rows=rows)
        return buttons
    
    def generate_url_buttons(self, buttons_json):
        if len(buttons_json) == 0:
            return None
        
        rows = []
        for button_row in buttons_json:
            row = []
            for url_button in button_row:
                row.append(KeyboardButtonUrl(text=url_button['text'], url=url_button['url']))
            rows.append(KeyboardButtonRow(buttons=row))

        buttons = ReplyInlineMarkup(rows=rows)
        return buttons
    
    @IgnoreRPCErrors
    async def send_discussion_message(self, discussion, message_type, message_kws, button_kws, reply_to=None, media=None):
        self.logger.info('Frontend send_discussion_message!')

        message, reply_to_obj = self.jinja_env.get_template(f'discussion_message/{message_type}.j2').render(**message_kws), None
        message_text, message_entities = utils.sanitize_parse_mode('md').parse(message)
        if reply_to != None:
            reply_to_obj = InputReplyToMessage(reply_to_msg_id=int(reply_to))
        buttons_json = json.loads(self.jinja_env.get_template(f'discussion_button/{message_type}.j2').render(**button_kws))
        buttons = self.generate_url_buttons(buttons_json)

        updates = None
        if media == None:
            updates = await self.telethon_bot(SendMessageRequest(peer=discussion, message=message_text, entities=message_entities, reply_to=reply_to_obj, 
                                                                 reply_markup=buttons))
        else:
            updates = await self.telethon_bot(SendMediaRequest(peer=discussion, message=message_text, media=media, entities=message_entities, 
                                                               reply_to=reply_to_obj, reply_markup=buttons))

        return Frontend.extract_message_tid_from_updates(updates)
    
    @IgnoreRPCErrors
    async def delete_discussion_message(self, discussion, message_tid):
        self.logger.info('Frontend delete_inline_message!')

        await self.telethon_bot(DeleteMessagesRequestChannel(channel=discussion, id=[int(message_tid)]))
    
    @IgnoreRPCErrors
    async def send_channel_message(self, channel, message_type, message_kws, button_kws, media=None):
        self.logger.info('Frontend send_channel_message!')

        message = self.jinja_env.get_template(f'channel_message/{message_type}.j2').render(**message_kws)
        message_text, message_entities = utils.sanitize_parse_mode('md').parse(message)
        buttons_json = json.loads(self.jinja_env.get_template(f'channel_button/{message_type}.j2').render(**button_kws))
        buttons = self.generate_url_buttons(buttons_json)

        updates = None
        if media == None:
            updates = await self.telethon_bot(SendMessageRequest(peer=channel, message=message_text, entities=message_entities, reply_markup=buttons))
        else:
            updates = await self.telethon_bot(SendMediaRequest(peer=channel, message=message_text, media=media, entities=message_entities, reply_markup=buttons))

        return Frontend.extract_message_tid_from_updates(updates)

    @IgnoreRPCErrors
    async def send_state_message(self, user, message_state, message_edge, message_kws, button_state, button_kws, 
                                 reply_to=None, media=None):
        self.logger.info('Frontend send_state_message!')

        message, buttons, reply_to_obj = self.jinja_env.get_template(f'state_message/{message_state}/{message_edge}.j2').render(**message_kws), None, None
        message_text, message_entities = utils.sanitize_parse_mode('md').parse(message)
        if reply_to != None:
            reply_to_obj = InputReplyToMessage(reply_to_msg_id=int(reply_to))
        if button_state != None:
            buttons_json = json.loads(self.jinja_env.get_template(f'state_button/{button_state}.j2').render(**button_kws))
            buttons = self.generate_keyboard_buttons(buttons_json)

        if media == None:
            await self.telethon_bot(SendMessageRequest(peer=user, message=message_text, entities=message_entities, reply_markup=buttons,
                                                       reply_to=reply_to_obj))
        else:
            await self.telethon_bot(SendMediaRequest(peer=user, message=message_text, media=media, entities=message_entities, reply_markup=buttons, 
                                                     reply_to=reply_to_obj))
            
    @IgnoreRPCErrors
    async def send_state_message_as_xlsx(self, user, message_state, message_edge, message_kws, button_state, button_kws):
        self.logger.info('Frontend send_state_message_as_xlsx!')

        message, buttons = self.jinja_env.get_template(f'state_message/{message_state}/{message_edge}.j2').render(**message_kws), None
        if button_state != None:
            buttons_json = json.loads(self.jinja_env.get_template(f'state_button/{button_state}.j2').render(**button_kws))
            buttons = self.generate_keyboard_buttons(buttons_json)

        async with self.file_lock:
            csv_file = open('temp/result.csv', 'w')
            csv_file.write(message)
            csv_file.close()

            pd_read_file = pd.read_csv('temp/result.csv')
            pd_read_file.to_excel('temp/result.xlsx', index = None, header=True)

            await self.telethon_bot.send_file(user, 'temp/result.xlsx', buttons=buttons)

            os.remove('temp/result.csv')
            os.remove('temp/result.xlsx')

    @IgnoreRPCErrors
    async def send_inline_message(self, user, inline_type, inline_senario, message_kws, button_kws, 
                                  reply_to=None, media=None):
        self.logger.info('Frontend send_inline_message!')

        message, reply_to_obj, updates = self.jinja_env.get_template(f'inline_message/{inline_type}/{inline_senario}.j2').render(**message_kws), None, None
        message_text, message_entities = utils.sanitize_parse_mode('md').parse(message)
        if reply_to != None:
            reply_to_obj = InputReplyToMessage(reply_to_msg_id=int(reply_to))
        buttons_json = json.loads(self.jinja_env.get_template(f'inline_button/{inline_type}/{inline_senario}.j2').render(**button_kws))
        buttons = self.generate_inline_buttons(buttons_json)

        if media == None:
            updates = await self.telethon_bot(SendMessageRequest(peer=user, message=message_text, entities=message_entities, reply_markup=buttons,
                                                                 reply_to=reply_to_obj))
        else:
            updates = await self.telethon_bot(SendMediaRequest(peer=user, message=message_text, media=media, entities=message_entities, reply_markup=buttons,
                                                               reply_to=reply_to_obj))
            
        return Frontend.extract_message_tid_from_updates(updates)
    
    @IgnoreRPCErrors
    async def edit_inline_message(self, user, message_tid, inline_type, inline_senario, message_kws, button_kws, 
                                  media=None):
        self.logger.info('Frontend edit_inline_message!')

        message = self.jinja_env.get_template(f'inline_message/{inline_type}/{inline_senario}.j2').render(**message_kws)
        message_text, message_entities = utils.sanitize_parse_mode('md').parse(message)
        buttons_json = json.loads(self.jinja_env.get_template(f'inline_button/{inline_type}/{inline_senario}.j2').render(**button_kws))
        buttons = self.generate_inline_buttons(buttons_json)

        await self.telethon_bot(EditMessageRequest(peer=user, id=int(message_tid), message=message_text, entities=message_entities, reply_markup=buttons,
                                                   media=media))
        
    @IgnoreRPCErrors
    async def delete_inline_message(self, message_tid):
        self.logger.info('Frontend delete_inline_message!')

        await self.telethon_bot(DeleteMessagesRequest(id=[int(message_tid)], revoke=True))
        
    @staticmethod
    def extract_message_tid_from_updates(updates):
        if isinstance(updates, UpdateShortSentMessage):
            return updates.id
        elif isinstance(updates, Updates):
            for update in updates.updates:
                if isinstance(update, UpdateMessageID):
                    return update.id
        raise ValueError('TL updates have unexpected structure.')