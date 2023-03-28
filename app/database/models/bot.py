from abc import ABC, abstractclassmethod
from os import name
from sys import stdout
from app.database.databases.mongodb import MongoDB
from app.database import Database
from app.database.identity import Identity
from typing import Dict, List
from uuid import uuid4


class IBot(ABC):

    @abstractclassmethod
    def create_bot(*args):
        pass

    @abstractclassmethod
    def edit_bot(*args):
        pass

    @abstractclassmethod
    def delete_bot(*args):
        pass


class BotBase(IBot):

    def __init__(self, database: MongoDB) -> None:
        self.colllection_name = 'users'
        self.__database = database

    def get_bots_data(self, identity: Identity) -> Dict:
        data = self.__database.users_collection.find_one(
            identity(), {'bots': 1, 'token': 1})
        bots = data.get('bots')

        if bots is not None and self.bots_count(bots) >= 1:
            return bots
        return {}

    def get_bots_simple_data(self, identity: Identity):
        """Gets the ids and the names of the bots.

        returns [{bot_id: string, name: string}, ...]
        """
        bots_data = self.get_bots_data(identity)
        bots_response = []
        for key in bots_data:
            bots_response.append(
                {'bot_id': bots_data[key].get('bot_id'), 'name': bots_data[key].get('name')})
        return bots_response

    def get_bot_data(self, identity: Identity, bot_id: str):
        try:
            data = self.get_bots_data(identity)
            return data[bot_id]
        except TypeError:
            return

    def get_bot_configs(self, identity: Identity, bot_id: str) -> Dict:
        bot_data = self.get_bot_data(identity, bot_id)
        return bot_data['config']

    def get_bot_shorteners(self, identity: Identity, bot_id: str) -> Dict:
        return self.get_bot_data(identity, bot_id)

    def bot_alive(self, identity: Identity, bot_id: str) -> bool:
        return (bot_id in self.get_bots_data(identity, bot_id))

    def _create_bot(self, identity: Identity, data: Dict) -> bool:
        model = self.create_bot_model()
        bot_id = f'bot_{uuid4()}'
        model['bot_id'] = bot_id
        model['name'] = data.get('name', bot_id[0:14])
        model.update(data)
        self.__database.users_collection.update_one(
            identity(), {'$set': {f'bots.{bot_id}': model}}) is not None
        return {'status': True, 'bot_id': bot_id, 'bot_data':model} 

    def _edit_bot(self, identity: Identity, bot_id: str, data: Dict) -> bool:

        return self.__database.users_collection.update_one(identity(), {'$set': {f'bots.{bot_id}.config', data}})

    def _delete_bot(self, identity: Identity, bot_id: str, data: Dict) -> bool:

        return self.__database.users_collection.update_one(identity(), {'$unset': {f'bots.{bot_id}': ''}})

    def _available_instances(self, identity: Identity):
        return self.__database.users_collection.find_one(identity(), {'available_bot_instances': 1})

    @staticmethod
    def bots_count(data: List) -> int:
        return len(list(data))

    @staticmethod
    def create_bot_model() -> Dict:
        return {
            "name": "",
            "chollos": [],
            "logs": [],
            "votes":[],
            "shortener":"chollito",
            "redirector_url": "https://mars.soydechollos.com/api/redirect?redirect=",
            "config": {
                "telegram": {
                    "chat_id": "",
                    "token": ""
                },
                "twitter": {
                    "consumer_key": "",
                    "consumer_secret": "",
                    "access_token": "",
                    "access_secret": ""
                },
                "facebook": {
                    "access_token": ""
                },
            }}

class Bot(BotBase):

    def __init__(self, database: Database) -> None:
        super().__init__(database)

    def create_bot(self, identity: Identity, data: Dict) -> Dict:
        if self._available_instances(identity):
            return self._create_bot(identity, data)
        return {'status': False, 'bot_data':None}

    def edit_bot(self, identity: Identity, bot_id: str, data: Dict) -> bool:
        return self._edit_bot(identity, bot_id, data)

    def delete_bot(self, identity: Identity, bot_id: str, data: Dict) -> bool:
        return self._delete_bot(identity, bot_id, data)

    def available_instances(self, identity: Identity) -> int:
        return self._available_instances(identity).get('available_bot_instances', 0)
