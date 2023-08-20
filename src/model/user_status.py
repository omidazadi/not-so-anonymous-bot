class UserStatus:
    def __init__(self, user_id, user_tid, is_admin, mask_name, is_masked, state, extra, last_message_at):
        self.user_id = user_id
        self.user_tid = user_tid
        self.is_admin = is_admin
        self.mask_name = mask_name
        self.is_masked = is_masked
        self.state = state
        self.extra = extra
        self.last_message_at = last_message_at

    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(UserStatus(*row))
        return result