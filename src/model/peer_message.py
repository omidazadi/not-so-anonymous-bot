import pickle
from datetime import datetime

class PeerMessage:
    def __init__(self, peer_message_id, channel_message_reply, peer_message_reply, 
                 answer_message_reply, from_message_tid, to_notification_tid, to_message_tid, 
                 from_user, from_user_veil, message, media, message_status, sent_at, 
                 is_reported, is_report_reviewed):
        self.peer_message_id = peer_message_id
        self.channel_message_reply = channel_message_reply
        self.peer_message_reply = peer_message_reply
        self.answer_message_reply = answer_message_reply
        self.from_message_tid = from_message_tid
        self.to_notification_tid = to_notification_tid
        self.to_message_tid = to_message_tid
        self.from_user = from_user
        self.from_user_veil = from_user_veil
        self.message = message
        self.media = pickle.loads(media)
        self.message_status = message_status
        self.sent_at = PeerMessage.convert_time(sent_at)
        self.is_reported = is_reported
        self.is_report_reviewed = is_report_reviewed
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(PeerMessage(*row))
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