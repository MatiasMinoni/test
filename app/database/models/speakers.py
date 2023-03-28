from sys import stdout
from typing import Dict

from app.database.identity import Identity
from app.database.database import Database
from app.database.models.bot import Bot


class BotConfig(Bot):

    def __init__(self, database: Database) -> None:
        super().__init__(database)
        self.database_instance = database

    def update(self, identity: Identity, bot_id: str, name: str, data: Dict):
        return self.database_instance.users_collection.update_one(identity(), {'$set': {f'bots.{bot_id}.config.{name}': data}})

    def update_shortener(self, identity: Identity, bot_id: str, name: str, data: Dict):
        return self.database_instance.users_collection.update_one(identity(), {'$set': {f'bots.{bot_id}.{name}': data}})


class TelegramConfig(BotConfig):

    def __init__(self, database: Database, data: Dict) -> None:
        super().__init__(database)
        self.config_name = 'telegram'
        self._data = data

    def set_config(self, identity: Identity, bot_id: str):
        return self.update(identity, bot_id, self.config_name, self.data)

    def get_config(self, identity: Identity, bot_id: str):
        return self.get_bot_configs(identity, bot_id).get(self.config_name)

    @property
    def data(self):
        return {'token': self._data.pop('token', ''), 'chat_id': self._data.pop('chat_id')}


class TelegramVotes(TelegramConfig):

    def __init__(self, database: Database) -> None:
        super().__init__(database, data=None)

    def user_exists(self, identity, bot_id, user_id):

        response = self.get_bot_data(identity, bot_id)['votes']

        for (index, user) in enumerate(response):
            try:
                if user_id == user['user_id']:
                    return (index, user)
            except KeyError:
                continue

    def vote(self, identity, bot_id, user_id, message_id):

        response = self.user_exists(identity, bot_id, user_id)

        if response is not None:
            if not self.user_voted(response[1], message_id):
                return self._vote(identity, bot_id, message_id, response[0])
        else:
            return self._new_user_vote(identity, user_id, bot_id, message_id)

    def user_voted(self, response, message_id):
        return message_id in response['messages_id']

    def _vote(self, identity, bot_id, message_id, index):

        response = (self.database_instance.users_collection.update_one(identity(), {
                    '$push': {f'bots.{bot_id}.votes.{index}.messages_id': message_id}}) is not None)
        return response

    def _new_user_vote(self, identity: Identity, user_id, bot_id, message_id):

        return self.database_instance.users_collection.update_one(identity(), {'$push': {f'bots.{bot_id}.votes': {'user_id': user_id, 'messages_id': [message_id]}}})


class TwitterConfig(BotConfig):
    def __init__(self, database: Database, data: Dict) -> None:
        super().__init__(database)
        self.config_name = 'twitter'
        self._data = data

    def set_config(self, identity: Identity, bot_id: str):
        return self.update(identity, bot_id, self.config_name, self.data)

    def get_config(self, identity: Identity, bot_id: str):
        return self.get_bot_configs(identity, bot_id).get(self.config_name)

    @property
    def data(self):
        return {'consumer_key': self._data.pop('consumer_key', ''), 'consumer_secret': self._data.pop('consumer_secret', ''), 'access_token': self._data.pop('access_token', ''), 'secret_token': self._data.pop('secret_token', '')}


class FacebookConfig(BotConfig):
    def __init__(self, database: Database, data: Dict) -> None:
        super().__init__(database)
        self.config_name = 'facebook'
        self._data = data

    def set_config(self, identity: Identity, bot_id: str):
        return self.update(identity, bot_id, self.config_name, self.data)

    def get_config(self, identity: Identity, bot_id: str) -> Dict:
        return self.get_bot_configs(identity, bot_id).get(self.config_name)

    @property
    def data(self):
        return {'access_token': self._data.pop('access_token')}


class ShortenerConfig(BotConfig):

    def __init__(self, database: Database) -> None:
        super().__init__(database)
        self.config_name = 'shortener'

    def set_config(self, identity: Identity, bot_id: str, data: Dict):
        return self.update_shortener(identity, bot_id, self.config_name, data.pop('shortener'))

    def set_redirector_url(self, identity: Identity, bot_id: str, data: Dict):
        return self.update_shortener(identity, bot_id, 'redirector_url', data.pop('redirector_url'))

    def get_config(self, identity: Identity, bot_id: str) -> str:
        return self.get_bot_shorteners(identity, bot_id).get(self.config_name, 'chollito')

    def get_redirector_url(self, identity: Identity, bot_id: str) -> str:
        return self.get_bot_shorteners(identity, bot_id).get('redirector_url', 'https://mars.soydechollos.com/api/redirect?redirect=')
    
