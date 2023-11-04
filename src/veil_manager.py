import os
import logging
import csv
import aiomysql
from repository.repository import Repository
from config import Config
from constant import Constant
from model.user_status import UserStatus
from model.veil import Veil

class VeilManager:
    def __init__(self, repository: Repository, config: Config, constant: Constant):
        self.logger = logging.getLogger('not_so_anonymous')
        self.repository = repository
        self.config = config
        self.constant = constant

    async def initialize(self, db_connection: aiomysql.Connection):
        if os.path.exists('config/veils.csv'):
            csv_reader, lno = csv.reader(open('config/veils.csv', 'r')), 0
            for row in csv_reader:
                if lno > 0:
                    await self.repository.veil.load_veil(row[0], row[1], db_connection)
                lno += 1
        else:
            self.logger.warn('config/veils.csv was not found.')

    async def acquire_automatically_reserved_veil(self, user_status: UserStatus, veil: Veil, db_connection: aiomysql.Connection):
        veil.reserved_by = None
        veil.owned_by = user_status.user_id
        veil.reservation_status = 'taken'
        await self.repository.veil.set_veil(veil, db_connection)
        await self.repository.veil.release_automatic_reservations(user_status.user_id, db_connection)

    async def acquire_veil(self, user_status: UserStatus, veil: Veil, db_connection: aiomysql.Connection):
        veil.reserved_by = None
        veil.owned_by = user_status.user_id
        veil.reservation_status = 'taken'
        await self.repository.veil.set_veil(veil, db_connection)

    async def giveaway_tickets(self, no_tickets, db_connection: aiomysql.Connection):
        candidates = await self.repository.user_status.get_ticket_candidates(db_connection)
        candidates_and_scores = [[candidate, 0] for candidate in candidates]
        for candidate_and_score in candidates_and_scores:
            candidate_and_score[1] = await self.user_score_for_tickets(candidate_and_score[0].user_id, db_connection)

        candidates_and_scores = sorted(candidates_and_scores, key=lambda x: x[1], reverse=True)
        if len(candidates_and_scores) <= no_tickets:
            await self.give_ticket_to_users(candidates_and_scores, db_connection)
            return [candidates_and_score[0] for candidates_and_score in candidates_and_scores]
        else:
            await self.give_ticket_to_users(candidates_and_scores[:no_tickets], db_connection)
            return [candidates_and_score[0] for candidates_and_score in candidates_and_scores[:no_tickets]]

    async def user_score_for_tickets(self, user_id, db_connection: aiomysql):
        return (
            await self.repository.channel_message.get_no_user_channel_messages(user_id, db_connection) + 
            await self.repository.peer_message.get_no_user_peer_messages(user_id, db_connection)
        )
    
    async def give_ticket_to_users(self, users, db_connection: aiomysql):
        for [user_status, score] in users:
            user_status.ticket += 1
            await self.repository.user_status.set_user_status(user_status, db_connection)

    async def make_automatic_reservations(self, user_status: UserStatus, db_connection: aiomysql.Connection):
        masculine_veil = await self.repository.veil.get_random_veil('masculine', db_connection)
        feminine_veil = await self.repository.veil.get_random_veil('feminine', db_connection)
        neutral_veil = await self.repository.veil.get_random_veil('neutral', db_connection)

        if masculine_veil == None or feminine_veil == None or neutral_veil == None:
            return False
        
        masculine_veil.reservation_status = 'automatically_reserved'
        masculine_veil.reserved_by = user_status.user_id
        await self.repository.veil.set_veil(masculine_veil, db_connection)

        feminine_veil.reservation_status = 'automatically_reserved'
        feminine_veil.reserved_by = user_status.user_id
        await self.repository.veil.set_veil(feminine_veil, db_connection)

        neutral_veil.reservation_status = 'automatically_reserved'
        neutral_veil.reserved_by = user_status.user_id
        await self.repository.veil.set_veil(neutral_veil, db_connection)

        return True