class Message:
    def __init__(self, id, message, verdict, reviewed_by, sent_at, reviewed_at):
        self.id = id
        self.message = message
        self.verdict = verdict
        self.reviewed_by = reviewed_by
        self.sent_at = sent_at
        self.reviewed_at = reviewed_at
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(Message(*row))
        return result