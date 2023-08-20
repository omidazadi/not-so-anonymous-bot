import pickle

class ChannelMessage:
    def __init__(self, channel_message_id, message_tid, from_user, message, media, verdict, 
                 reviewed_by, sent_at, reviewed_at):
        self.channel_message_id = channel_message_id
        self.message_tid = message_tid
        self.from_user = from_user
        self.message = message
        self.media = pickle.loads(media)
        self.verdict = verdict
        self.reviewed_by = reviewed_by
        self.sent_at = sent_at
        self.reviewed_at = reviewed_at
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(ChannelMessage(*row))
        return result