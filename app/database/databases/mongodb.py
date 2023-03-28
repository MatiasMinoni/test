from app.database.identity import Identity
from typing import Dict
from pymongo import MongoClient
from app.database import Database
import os


class MongoDB(Database):

    def __init__(self):
        
        self.client = MongoClient(self.auth)
        self._database = self.client[os.environ['DB_NAME']]
        self.users_collection = self._database['users']
        self.urls_collection = self._database['urls']

    def get_data(self, collection_name: str, identity : Identity):
        """make a query for the user and if the user exist return the user_data"""
        return self._database[collection_name].find_one(identity())
    
    def create(self, collection_name : str, data):

        return self._database[collection_name].insert_one(data)
       
    def update(self, collection_name : str, data : Dict, identity: Identity):

        query = self._database[collection_name].find_one(identity())
        return (self._database[collection_name].update_one(query, {'$set': data}) is not None)

    def get_collection(self, collection_name : str):

        return self._database[collection_name]

    def delete(self):
        pass

    @property
    def auth(self):
        return "mongodb+srv://{}:{}@{}{}?ssl=true&ssl_cert_reqs=CERT_NONE&retryWrites=true&w=majority".format(os.environ['DB_USER'], os.environ['DB_PASSWORD'], os.environ['DB_URI'], os.environ['DB_NAME'])