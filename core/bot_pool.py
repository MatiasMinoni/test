from core.bot_worker import BotWorker
from app.database.identity import Identity
from sys import stdout

class BotPool:
    """
    BotPool Model

    pool:
        bot_identity -->
                        [bot_instance_1]
                        [bot_instance_2]
                        [bot_instance_3]
                        ...
        ...
    """

    def __init__(self) -> None:
        self.__pool = {}

    def __check_bot_instance(self, identity: Identity, bot_id: str) -> bool:
        if self.__check_bot_in_pool(identity):
            return bot_id in self.__pool[identity.value]    
    
    def __check_bot_in_pool(self, identity: Identity) -> bool:
        return identity.value in self.__pool

    def add_bot(self, identity: Identity, bot_id: str, bot_worker: BotWorker) -> None:
        
        if not self.__check_bot_in_pool(identity):
            self.__pool[identity.value] = {}
        
        if not self.__check_bot_instance(identity, bot_id):
            self.__pool[identity.value][bot_id] =  bot_worker
    
    def get_bot(self, identity: Identity, bot_id: str) -> BotWorker:
        if self.__check_bot_instance(identity, bot_id):
            return self.__pool[identity.value][bot_id]

    def get_pool(self):
        return self.__pool