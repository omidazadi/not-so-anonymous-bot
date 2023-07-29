class UserStatus:
    def __init__(self, telegram_id, state, extra, no_messages):
        self.telegram_id = telegram_id
        self.state = state
        self.extra = extra
        self.no_messages = no_messages