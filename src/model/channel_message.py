from datetime import datetime
import pickle

class ChannelMessage:
    def __init__(self, channel_message_id, message_tid, channel_message_tid, 
                 discusison_message_tid, from_user, from_user_veil, message, 
                 media, can_reply, is_public, verdict, reviewed_by, sent_at, reviewed_at):
        self.channel_message_id = channel_message_id
        self.message_tid = message_tid
        self.channel_message_tid = channel_message_tid
        self.discusison_message_tid = discusison_message_tid
        self.from_user = from_user
        self.from_user_veil = from_user_veil
        self.message = message
        self.media = pickle.loads(media)
        self.can_reply = can_reply
        self.is_public = is_public
        self.verdict = verdict
        self.reviewed_by = reviewed_by
        self.sent_at = ChannelMessage.convert_time(sent_at)
        self.reviewed_at = ChannelMessage.convert_time(reviewed_at)
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(ChannelMessage(*row))
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