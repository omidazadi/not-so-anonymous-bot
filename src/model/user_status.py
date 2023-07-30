class UserStatus:
    def __init__(self, telegram_id, state, extra, no_messages, last_message_at):
        self.telegram_id = telegram_id
        self.state = state
        self.extra = extra
        self.no_messages = no_messages
        self.last_message_at = last_message_at

    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(UserStatus(*row))
        return result