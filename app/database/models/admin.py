from app.database.identity import Identity
from typing import Dict, List
from app.database.database import Database
from app.database.models.account import Account

class Admin(Account):

    def __init__(self, database: Database) -> None:
        super().__init__(database)
    
    def get_all_users(self):
        
        data = self.database.get_data(self.collection_name)
        users = []
        
        for user_data in data:
            users.append({'token':user_data['token'], 'name':user_data['email'].split('@')[0]})
        return users

    def get_all_bots(self) -> List:

        data = self.database.get_data(self.collection_name)
        bots = {}

        for user_data in data:
            for bot_name in list(user_data['bots']):
                try:
                    bots[user_data['token']].append(bot_name)
                except AttributeError:
                    bots[user_data] = [bot_name]
        return bots
