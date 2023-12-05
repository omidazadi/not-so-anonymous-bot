from datetime import datetime
import pickle

class AnswerMessage:
    def __init__(self, answer_message_id, channel_message_reply, from_message_tid, to_notification_tid, 
                 to_message_tid, discussion_message_tid, from_user, from_user_veil, message, media, 
                 can_reply, message_status, is_reported, is_report_reviewed, sent_at):
        self.answer_message_id = answer_message_id
        self.channel_message_reply = channel_message_reply
        self.from_message_tid = from_message_tid
        self.to_notification_tid = to_notification_tid
        self.to_message_tid = to_message_tid
        self.discussion_message_tid = discussion_message_tid
        self.from_user = from_user
        self.from_user_veil = from_user_veil
        self.message = message
        self.media = pickle.loads(media)
        self.can_reply = can_reply
        self.message_status = message_status
        self.is_reported = is_reported
        self.is_report_reviewed = is_report_reviewed
        self.sent_at = AnswerMessage.convert_time(sent_at)
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(AnswerMessage(*row))
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
    