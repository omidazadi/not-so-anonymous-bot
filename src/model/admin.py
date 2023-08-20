class Admin:
    def __init__(self, user_tid, password_hash):
        self.user_tid = user_tid
        self.password_hash = password_hash

    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(Admin(*row))
        return result