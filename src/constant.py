class Constant:
    def __init__(self):
        self.view = Constant.View()
        self.limit = Constant.Limit()

    class View:
        def __init__(self):
            self.pending_list_preview_length: int = 200
            self.pending_list_page_size: int = 5
        
    class Limit:
        def __init__(self):
            self.rate_limit: int = 30
            self.channel_reply_limit: int = 10
            self.simple_message_size: int = 2048
            self.media_message_size: int = 512