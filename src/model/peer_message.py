import pickle

class PeerMessage:
    def __init__(self, peer_message_id, channel_message_reply, peer_message_reply, 
                 from_message_tid, to_message_tid, from_user, message, media,
                 condition, sent_at):
        self.peer_message_id = peer_message_id
        self.channel_message_reply = channel_message_reply
        self.peer_message_reply = peer_message_reply
        self.from_message_tid = from_message_tid
        self.to_message_tid = to_message_tid
        self.from_user = from_user
        self.message = message
        self.media = pickle.loads(media)
        self.condition = condition
        self.sent_at = sent_at
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(PeerMessage(*row))
        return result