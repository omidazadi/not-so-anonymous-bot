class Block:
    def __init__(self, user_id, blocked):
        self.user_id = user_id
        self.blocked = blocked
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(Block(*row))
        return result