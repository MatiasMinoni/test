from sys import stdout
from core.bot_pool import BotPool
from app.database.identity import Identity
from app.database.databases.mongodb import MongoDB
from core.bot_worker import BotWorker
from typing import Dict, Union
from app.database import Database
from typing import List

class BotService:

    def __init__(self, database: Union[Database, MongoDB]) -> None:
        self.database = database
        self.bot_pool = BotPool()

    def get_bot(self, identity: Identity, bot_id: str) -> BotWorker:
        bot_worker = self.bot_pool.get_bot(identity, bot_id)
        return bot_worker

    def add_to_bot_pool(self, identity: Identity, bot_data: Dict):

        self.bot_pool.add_bot(identity, bot_data['bot_id'], BotWorker(identity, self.database, bot_data))

    def get_bot_by_api(self, bot_id: str) -> BotWorker:
        bots = self.bot_pool.get_pool()
        for identity in bots:
            for bot_server_id in bots[identity]:
                if bot_server_id == bot_id:
                    return bots[identity][bot_server_id]

    def get_active_running_bots(self) -> List:
        response = []
        bots = self.bot_pool.get_pool()
        for identity in bots:
            for bot_id in bots[identity]:
                response.append({'name': bots[identity][bot_id].bot_name, 'bot_id':bots[identity][bot_id].bot_id})
        return response
    

    # this func needs to be remove from here in the future.
    def check_user_in_raffle(self, user_id: int, uuid: str):
        """
        Check if user is in raffle

        model:
            {
                uuid: str,
                clicks_by_users: list,
                ...
            }
        
        """
        response = self.database.urls_collection.find_one({'uuid':uuid, 'clicks_by_user':{'$in': [user_id]}})
        return (response is not None)

class BotServiceController(BotService):

    def __init__(self, database: Database) -> None:
        super().__init__(database)
    
    def start_service(self):
        self._start_service()

    def _start_service(self):
        users_data = self.get_users_data()
        for key in users_data:
            for bot_id in users_data[key]:
                self.add_to_bot_pool(Identity('token', None, key), users_data[key][bot_id])

    def get_users_data(self):
        data = self.database.users_collection.find({}, {'token':1, 'bots':1})
        users_data = {}
        for user_data in data:
            try:
                users_data[user_data['token']] = user_data['bots']
            except:
                continue
        return users_data
