from datetime import datetime

class UserStatus:
    def __init__(self, user_id, user_tid, gen_is_admin, veil, is_veiled, state, extra, last_message_at,
                 is_banned):
        self.user_id = user_id
        self.user_tid = user_tid
        self.gen_is_admin = gen_is_admin
        self.veil = veil
        self.is_veiled = is_veiled
        self.state = state
        self.extra = extra
        self.last_message_at = UserStatus.convert_time(last_message_at)
        self.is_banned = is_banned

    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(UserStatus(*row))
        return result
    
    @staticmethod
    def convert_time(t):
        if t == None:
            return None
        elif isinstance(t, datetime):
            return t
        elif type(t) == str:
            return datetime.fromisoformat(t)
        raise ValueError('Bad timestamp format.')