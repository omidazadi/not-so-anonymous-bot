class UserStatus:
    def __init__(self, user_id, user_tid, gen_is_admin, veil, is_veiled, state, extra, last_message_at):
        self.user_id = user_id
        self.user_tid = user_tid
        self.gen_is_admin = gen_is_admin
        self.veil = veil
        self.is_veiled = is_veiled
        self.state = state
        self.extra = extra
        self.last_message_at = last_message_at

    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(UserStatus(*row))
        return result