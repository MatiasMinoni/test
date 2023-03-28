from sys import stdout
from core.speakers.utils import get_image
from core.webs.web_controller import ChollosWebController
from core.bot_service import BotServiceController
from core.chollito_service import ChollitoService
from app.database.models.speakers import FacebookConfig, ShortenerConfig, TelegramConfig, TwitterConfig
from app.database.models import Shortener, Bot
from app.database.identity import ID, Identity
from flask_jwt_extended.utils import get_jwt
from app.utils import login_required
from flask_socketio import Namespace, emit
from typing import Dict, List

class ChollitoNamespace(Namespace):

    @property
    def token(self):
        return get_jwt().get('token')

    @property
    def identity(self):
        return Identity('token', ID, self.token)

    def set_service(self, name: str, obj: object):

        if name == 'chollito_service':
            self.chollito_service: ChollitoService = obj
        elif name == 'bot_service':
            self.bot_service: BotServiceController = obj
        elif name == 'web_controller':
            self.web_controller: ChollosWebController = obj

    @login_required(by_socket=True)
    def on_connected(self, items: List, **kwargs):
        if not kwargs.get('disconnect'):
            if len(items) <= 0:
                chollos = self.web_controller.get_chollos()
                emit('add_new_items', chollos)
        else:
            emit('disconnect_this_shit')

    @login_required(by_socket=True)
    def on_update_items(self, **kwargs):
        if not kwargs.get('disconnect'):
            chollos = self.web_controller.get_chollos()
            emit('add_new_items', chollos)
        else:
            emit('disconnect_this_shit')

    @login_required()
    def on_add_item(self, item: Dict):
        self.chollito_service.add_chollo(self.token, item)

    @login_required()
    def on_edit_item(self, item: Dict):

        self.chollito_service.update_chollo(self.token, item)
        emit('set_chollos_bot_data', self.chollito_service.chollos_database_instance.get_chollos(
            self.identity, self.item.get('bot_id')))

    @login_required()
    def on_delete_item(self, item: Dict):
        self.chollito_service.delete_chollo(self.token, item)
        data = self.chollito_service.get_chollos_bot_data(self.identity)
        bot = Bot(self.bot_service.database)
        bots = bot.get_bots_simple_data(self.identity)
        emit('set_chollos_bot_data', {'chollos_data':data, 'bots':bots})

    @login_required()
    def on_get_items(self, bot_id: str):
        if isinstance(bot_id, dict):
            bot_id = bot_id.get('bot_id')

        data = self.chollito_service.chollos_database_instance.get_chollos(
            self.identity, bot_id)
        emit('update_saved_items', data)

    @login_required()
    def on_set_telegram_tokens(self, data: Dict):
        bot_id = data.pop('bot_id')
        config_instance = TelegramConfig(self.bot_service.database, data)
        config_instance.set_config(self.identity, bot_id)
        bot = self.bot_service.get_bot(self.identity, bot_id)
        bot.update_config('telegram', **data)

    @login_required()
    def on_set_twitter_tokens(self, data: Dict):
        bot_id = data.pop('bot_id')
        config_instance = TwitterConfig(self.bot_service.database, data)
        config_instance.set_config(self.identity, bot_id)
        bot = self.bot_service.get_bot(self.identity, bot_id)
        bot.update_config('twitter', **data)

    @login_required()
    def on_set_facebook_account(self, data: Dict):

        bot_id = data.pop('bot_id')
        access_token = data.pop('fb_access_token')
        config_instance = FacebookConfig(self.bot_service.database, {'access_token':access_token})
        config_instance.set_config(self.identity, bot_id)
        bot = self.bot_service.get_bot(self.identity, bot_id)
        bot.update_config('facebook', {'access_token':access_token})

    @login_required()
    def on_set_shortener(self, data: Dict):
        bot_id = data.pop('bot_id')
        config_instance = ShortenerConfig(self.bot_service.database)
        config_instance.set_redirector_url(self.identity, bot_id, data)
        config_instance.set_config(self.identity, bot_id, data)
    
    @login_required()
    def on_create_shortener_link(self, data: Dict):
        shortener_instance = Shortener(self.bot_service.database)
        response = shortener_instance.add_url(data, from_web_app=True)
        emit('set_shortener_link', response)

    @login_required()
    def on_publish_item(self, item):
        bot_id = item.get('bot_id')
        bot = self.bot_service.get_bot(self.identity, bot_id)
        bot.send_message(item)

    @login_required()
    def on_get_image_url(self, data: Dict):
        image_url = data.get('url')
        response = {'url': get_image(image_url)}
        emit('add_image', response)

    @login_required()
    def on_get_bots_simple_data(self):
        bot = Bot(self.bot_service.database)
        bots = bot.get_bots_simple_data(self.identity)
        emit('set_bots_simple_data', bots)

    @login_required()
    def on_get_bot_data(self, data: Dict):
        bot_id = data.get('bot_id')
        bot = Bot(self.bot_service.database)
        data = bot.get_bot_data(self.identity, bot_id)
        result = {}
        result.update({'shortener':data.pop('shortener'), 'redirector_url': data.pop('redirector_url', '')})
        data = data.pop('config', {})
        facebook_config_data = {'fb_access_token':data.pop('facebook')['access_token']}
        result.update(data.pop('telegram'))
        result.update(facebook_config_data)
        result.update(data.pop('twitter'))
        emit('on_set_bot_data', result)

    @login_required()
    def on_bot_alive(self, data: Dict):
        bot_id = data.get('bot_id')
        bot_status = self.bot_service.get_bot(self.identity, bot_id)
        emit('set_bot_status', (bot_status is not None))

    @login_required()
    def on_create_bot(self, data: Dict):
        bot = Bot(self.bot_service.database)
        if len(data.get('name', '')) >= 1:
            data = bot.create_bot(self.identity, data)
            if data.get('status'):
                self.bot_service.add_to_bot_pool(
                    self.identity, data.get('bot_data'))
        bot_name = data['bot_data'].get('name')
        bot_id = data['bot_data'].get('bot_id')
        bots = bot.get_bots_simple_data(self.identity)

        emit('create_bot_status', {'status':data.get('status'), 'bot_id':bot_id, 'name':bot_name})
        emit('set_bots_simple_data', bots)

    @login_required()
    def on_get_available_instances_count(self):
        bot = Bot(self.bot_service.database)
        available_instances = bot.available_instances(self.identity)
        emit('set_available_instances_count', available_instances)

    @login_required()
    def on_get_chollos_bot_data(self):
        data = self.chollito_service.get_chollos_bot_data(self.identity)
        bot = Bot(self.bot_service.database)
        bots = bot.get_bots_simple_data(self.identity)
        emit('set_chollos_bot_data', {'chollos_data':data, 'bots':bots})