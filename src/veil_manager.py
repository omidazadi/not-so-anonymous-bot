import os
import logging
import json
import csv
import aiomysql
from repository.repository import Repository
from config import Config
from constant import Constant

class VeilManager:
    def __init__(self, repository: Repository, config: Config, constant: Constant):
        self.logger = logging.getLogger('not_so_anonymous')
        self.repository = repository
        self.config = config
        self.constant = constant
        self.direct_veils: dict[str, str] = dict()
        self.veils: list[tuple[str, str]] = list()

    async def initialize(self, db_connection: aiomysql.Connection):
        if os.path.exists('config/veils.csv'):
            csv_reader, lno = csv.reader(open('config/veils.csv', 'r')), 0
            for row in csv_reader:
                if lno > 0:
                    await self.repository.veil.load_veil(row[0], row[1], db_connection)
                lno += 1
        else:
            self.logger.warn('config/veils.csv was not found.')

        if os.path.exists('config/direct_veils.json'):
            self.direct_veils = json.load(open('config/direct_veils.json', 'r'))
            for user_tid in self.direct_veils:
                if await self.repository.veil.get_veil(self.direct_veils[user_tid], db_connection) == None:
                    raise ValueError(f'A reserved veil in direct_veils.json is non-existant in the database: {self.direct_veils[user_tid]}')
        else:
            self.logger.warn('config/direct_veils.json was not found.')
        
    