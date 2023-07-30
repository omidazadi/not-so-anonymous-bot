import json
from telethon import TelegramClient
from telethon.tl.custom.button import Button

class Frontend():
    def __init__(self, telethonBot: TelegramClient, pending_preview_length: int):
        self.telethonBot = telethonBot
        self.pending_preview_length = pending_preview_length
        self.button_messages = json.load(open('resources/button.json', 'r', encoding='utf-8'), )
        self.ui_messages = json.load(open('resources/ui.json', 'r', encoding='utf-8'))

    async def maintenance_mode(self, user):
        message = self.ui_messages['maintenance']
        await self.telethonBot.send_message(user, message)

    async def notify_admin(self, user):
        message = self.ui_messages['notify-admin']
        await self.telethonBot.send_message(user, message)

    async def send_to_channel(self, channel_id, message):
        await self.telethonBot.send_message(channel_id, message)

    def generate_pending_list_view(self, arguments):
        if len(arguments[0]) == 0:
            return self.ui_messages['states']['pending-list']['main']['empty']
        text = self.ui_messages['states']['pending-list']['main']['header'].format(arguments[1], arguments[2]) + '\n\n'
        for i in range(len(arguments[0])):
            message = arguments[0][i]
            preview_message = message.message
            if len(preview_message) > self.pending_preview_length:
                preview_message = preview_message[0:self.pending_preview_length] + '...'
            text += self.ui_messages['states']['pending-list']['main']['line'].format(message.id, preview_message)
            if i < len(arguments[0]) - 1:
                text += '\n\n'
        return text

    async def answer(self, user, from_state, to_state, edge, special_generation=None, arguments=[], no_buttons=False):
        message: str = None
        if special_generation == None:
            if edge != 'yield':
                message = self.ui_messages['states'][from_state][edge]
            else:
                message = self.ui_messages['states'][to_state]['main']

            message = message.format(*arguments)
        else:
            if special_generation == 'pending-list':
                message = self.generate_pending_list_view(arguments)

        if no_buttons:
            await self.telethonBot.send_message(user, message)
        else:
            buttons = []
            for button_option in self.button_messages[to_state]:
                if button_option.startswith('hidden'):
                    continue
                buttons.append(Button.text(self.button_messages[to_state][button_option], resize=True))

            if special_generation != None:
                if special_generation == 'pending-list':
                    if len(arguments[0]) > 0:
                        buttons = [buttons, []]
                        for message_object in arguments[0]:
                            buttons[1].append(Button.text(str(message_object.id), resize=True))

            await self.telethonBot.send_message(user, message, buttons=buttons)