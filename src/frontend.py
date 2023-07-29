import json
from telethon import TelegramClient
from telethon.tl.custom.button import Button

class Frontend():
    def __init__(self, telethonBot: TelegramClient):
        self.telethonBot = telethonBot
        self.button_messages = json.load(open('resources/button.json', 'r'))
        self.ui_messages = json.load(open('resources/ui.json', 'r'))

    async def maintenance_mode(self, user):
        message = self.ui_messages['maintenance']
        await self.telethonBot.send_message(user, message)

    async def answer(self, user, from_state, to_state, edge, arguments=[], no_buttons=False):
        message: str = None
        if edge != 'yield':
            message = self.ui_messages['states'][from_state][edge]
        else:
            message = self.ui_messages['states'][to_state]['main']
        message.format(*arguments)

        buttons = []
        if not no_buttons:
            for button_option in self.button_messages[to_state]:
                if button_option.startswith('hidden'):
                    continue
                buttons.append(Button.text(self.button_messages[to_state][button_option], resize=True))
        await self.telethonBot.send_message(user, message, buttons=buttons)