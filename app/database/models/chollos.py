from abc import ABC, abstractclassmethod
from logging import getLogger
from sys import stdout
from app.database.models.bot import Bot
from app.database.database import Database
from app.database.identity import Identity
from typing import Dict, List


class ChollosBase(Bot):

    def __init__(self, database: Database):
        super().__init__(database)
        self._logger = getLogger('<ChollosDatabase>')
        self.__database = database

    def is_saved(self, identity: Identity, bot_id: str, chollo: Dict):

        chollos = self.get_chollos(identity, bot_id)
        if chollos is not None:
            for store_chollo in chollos:
                if self.check_chollo_id(store_chollo, chollo):
                    return store_chollo

    def _add_chollo(self, identity: Identity, bot_id: str, chollo: Dict):

        chollos_size = len(self.get_chollos(identity, bot_id))
        chollo['index'] = chollos_size - 1 if chollos_size >= 1 else chollos_size + 1

        return self.__database.users_collection.update_one(identity(), {'$push':{f'bots.{bot_id}.chollos': chollo}})

    def _edit_chollo(self, identity: Identity, bot_id: str, chollo: Dict):
            try:
                return (self.__database.users_collection.update_one(identity(), {'$set':{f'bots.{bot_id}.chollos.$[element]': chollo}}, array_filters=[{'element.id':chollo['id']}]) is not None)
            except:
                self._logger.error(f'on [_update_chollo] BOT_ID -> {bot_id}\ndetails:\n', exc_info=1)

    def _delete_chollo(self, identity: Identity, bot_id: str, chollo: Dict):
        try:
            return self.__database.users_collection.update_one(identity(), {'$pull':{f'bots.{bot_id}.chollos': chollo}})
        except:
            self._logger.error(f'on [_delete_chollo] BOT_ID -> {bot_id}\ndetails:\n', exc_info=1)

    @staticmethod
    def check_chollo_id(store_chollo: Dict, chollo: Dict) -> bool:
        return store_chollo['id'] == chollo['id']


class Chollos(ChollosBase):

    def __init__(self, database: Database):
        super().__init__(database)

    def get_chollos(self, identity: Identity, bot_id: str) -> List:
        return self.get_bots_data(identity)[bot_id].get('chollos', [])

    def add_chollo(self, identity: Identity, bot_id, chollo):

        if not isinstance(self.is_saved(identity, bot_id, chollo), dict):
            return self._add_chollo(identity, bot_id, chollo)

    def edit_chollo(self, identity: Identity, bot_id: str, chollo: Dict) -> bool:
        store_chollo = self.is_saved(identity, bot_id, chollo)

        if store_chollo:
            return self._edit_chollo(identity, bot_id, chollo)

    def delete_chollo(self, identity: Identity, bot_id: str, chollo: Dict):
        store_chollo = self.is_saved(identity, bot_id, chollo)
        if store_chollo:
            return self._delete_chollo(identity, bot_id, store_chollo)