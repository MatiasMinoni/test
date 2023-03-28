from abc import ABC, abstractmethod
from app.database.models.bot import Bot
from app.database.databases.mongodb import MongoDB
from typing import Dict
from app.database.identity import Identity
from json import load
from app.database import Database


class IAccount(ABC):

    @abstractmethod
    def create_account(self, identity: Identity, data: Dict):
        pass

    @abstractmethod
    def delete_account(self, identity: Identity, data: Dict):
        pass


class Account(IAccount):

    def __init__(self, database) -> None:
        self.collection_name = 'users'
        self.database: MongoDB = database

    def _user_model(self):
        with open(r'./app/database/system_model.json', 'r') as user_model:
            self.new_user_model = load(user_model)
            user_model.close()

    def create_account(self, data: Dict):
        self._user_model()
        self.new_user_model.update(data)
        return self.database.users_collection.insert_one(self.new_user_model)

    def delete_account(self, identity: Identity, data: Dict):

        return self.database.delete(self.collection_name, identity, data)

    def update_data(self, identity: Identity, data: Dict):

        return self.database.update(self.collection_name, identity, data)

    def get_data(self):

        return self.database.users_collection.find({}, {'_id':0})

    def get_password_hash(self, identity: Identity) -> bool:

        user_passw = self.database.users_collection.find_one(identity(), {'password':1})
        return user_passw

    def is_registered(self, identity: Identity) -> MongoDB:

        user_data = self.database.users_collection.find_one(identity())
        return user_data

    def create_bot(self, identity: Identity, name: str) -> bool:

        collection = self.database.get_collection(self.collection_name)
        bot = Bot(collection)
        return bot.create_bot(identity, name)

    def update_bot(self, identity: Identity, name: str, data: Dict) -> bool:

        collection = self.database.get_collection(self.collection_name)
        bot = Bot(collection)
        return bot.edit_bot(identity, name, data)
    
    def get_user_info(self, identity: Identity):

        return self.database.users_collection.find_one(identity(), {'_id':0, 'role':1, 'token':1})
