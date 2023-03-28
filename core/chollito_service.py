from app.database.models.bot import Bot
from app.database.identity import Identity, ID
from app.database.models.chollos import Chollos
from logging import getLogger
from core.webs.items_manager import Item
from core.bot_service import BotServiceController
from typing import Dict
from core.webs.items_scheluder import GlobalScheluder
from threading import _start_new_thread

class ChollitoService:
    
    def __init__(self, database, bot_service_controller: BotServiceController) -> None:
        self.__logger = getLogger('<ChollitoService>')
        self.database = database
        self.bot_service_controller = bot_service_controller
        self.items = {}
        self.global_scheluder = GlobalScheluder(self.items, self.send_chollos_callback, self.update_chollos_callback)
        self.chollos_database_instance = Chollos(self.database)
        self.bot_database_instance = Bot(self.database)

    def start_service(self):
        _start_new_thread(self.global_scheluder.start_scheluder, ())
        _start_new_thread(self.update_chollos_data, ())

    def add_chollo(self, user_token: str, item: Dict):
        identity = Identity('token', ID, user_token)
        try:
            bot_id = item.get('bot_id')
            self.items[user_token][bot_id].append(Item(item))
            self.chollos_database_instance.add_chollo(identity, bot_id, item)
        except:
            self.__logger.error(f'on [add_chollo] BOT_ID -> {bot_id}', exc_info=1)

    def update_chollo(self, user_token: str, item: Dict):
        identity = Identity('token', ID, user_token)
        try:
            chollo_id = item.get('id')
            bot_id = item.get('bot_id')
            for chollo in self.items[user_token][bot_id]:
                if chollo.id == chollo_id:
                    chollo.update(item)
                    self.chollos_database_instance.edit_chollo(identity, bot_id, item)
        except:
            self.__logger.error(f'on [update_chollo] BOT_ID -> {bot_id}', exc_info=1)


    def delete_chollo(self, user_token: str, item: Dict):
        try:
            chollo_id = item.get('id')
            bot_id = item.get('bot_id')
            for (index, chollo) in enumerate(self.items[user_token][bot_id], 0):
                if chollo.id == chollo_id:
                    self.chollos_database_instance.delete_chollo(Identity('token', ID, user_token), bot_id, item)
                    self.items[user_token][bot_id].pop(index)
        except:
            self.__logger.error(f'on [delete_chollo] BOT_ID -> {bot_id}', exc_info=1)

    def update_chollos_data(self) -> None:

        users_data = self.database.users_collection.find({})
        for user in users_data:
            if not user['token'] in self.items:
                self.items[user['token']] = {}
            bots = user.get('bots', {})

            for bot_id in bots:
                user_token = user.get('token', '')
                if not bot_id in self.items[user_token]:
                    self.items[user_token][bot_id] = [Item(item) for item in bots[bot_id].get('chollos', [])]
                else:
                    chollos = bots[bot_id].get('chollos', [])
                    for item in chollos:
                        self.update_chollo(user_token, item)

    def get_chollos_bot_data(self, identity: Identity) -> Dict:
        try:
            return self.__get_chollos_bot_data(identity)
        except:
            self.__logger.error(f'on [get_chollos_bot_data] USER_TOKEN -> {identity.value}', exc_info=1)

    def send_chollos_callback(self, user_token: str, item: Item):

        bot_id = item.get_dict().get('bot_id')
        identity = Identity('token', ID, user_token)
        bot = self.bot_service_controller.bot_pool.get_bot(identity, bot_id)
        bot.send_message(item.get_dict())
    
    def update_chollos_callback(self, user_token: str, item: Item):
        item = item.get_dict()
        if item.get('status') == 'off':
            return self.delete_chollo(user_token, item)

        self.update_chollo(user_token, item.get_dict())
    
    def __get_chollos_bot_data(self, identity: Identity) -> Dict:

        items = {}
        for bot_id in self.items[identity.value]:
            for item in self.items[identity.value][bot_id]:
                try:
                    items[bot_id].append(item.get_dict())
                except KeyError:
                    items[bot_id] = [item.get_dict()]
        return items;