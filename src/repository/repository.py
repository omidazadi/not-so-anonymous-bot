from repository.admin_repository import AdminRepository
from repository.channel_message_repository import ChannelMessageRepository
from repository.peer_message_repository import PeerMessageRepository
from repository.reservation_repository import ReservationRepository
from repository.user_status_repository import UserStatusRepository
from repository.veil_repository import VeilRepository
from repository.block_repository import BlockRepository

class Repository:
    def __init__(self):
        self.admin = AdminRepository()
        self.channel_message = ChannelMessageRepository()
        self.peer_message = PeerMessageRepository()
        self.reservation = ReservationRepository()
        self.user_status = UserStatusRepository()
        self.veil = VeilRepository()
        self.block = BlockRepository()