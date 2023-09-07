from datetime import datetime
from model.user_status import UserStatus

class RateLimitMixin:
    async def is_rate_limited(self, user_status: UserStatus):
        if user_status.last_message_at == None:
            return False
        now = datetime.utcnow()
        time_passed = now - user_status.last_message_at
        if time_passed.total_seconds() < self.constant.limit.rate_limit:
            return True
        return False