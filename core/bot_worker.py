from sys import stdout
from app.database.models.bot import Bot
from core.speakers.utils import get_image
from core.shortener_manager import ShortenerManager
from app.database.models.speakers import ShortenerConfig
from core.speakers.message_renderer import ServerMessageRendererHTML
from core.webs.items_manager import Item
from app.database.database import Database
from app.database.identity import Identity
from core.speakers.facebook.bot import FBot as Facebook
from core.speakers.telegram.bot import TBot as Telegram
from core.speakers.twitter.bot import TWBot as Twitter
from logging import getLogger
from typing import Dict
from threading import _start_new_thread

OK = True

class BotWorker:

    def __init__(self, identity: Identity, database: Database, bot_data: Dict) -> None:
        self.__logger = getLogger(f'<BotWorker> {bot_data["name"]}')
        self.database = database
        self.bot_data = bot_data
        self.bot_name = bot_data.get('name')
        self.bot_id = bot_data['bot_id']
        self.identity = identity
        self.speakers = {'telegram': Telegram(self.database, self.identity, self.bot_id),
         'twitter': Twitter(),
         'facebook': Facebook(self.bot_id)}
        self.start_process()

    def start_process(self):
        self.__init_bot_config()
        for speaker in self.speakers.values():
            try:
                speaker.start_bot()
            except AttributeError:
                continue
            except:
                self.__logger.error('on [start_process] ', exc_info=1)
                continue

    def stop_process(self):
        
        for speaker in self.speakers.values():
            try:
                speaker.stop_bot()
            except AttributeError:
                continue
            except:
                self.__logger.error('on [stop_process] ', exc_info=1)
                continue

    def update_config(self, speaker: str, **kwargs):
        self.speakers[speaker].update_config(**kwargs)

    def send_message(self, item: Item):
        
        item['channel_name'] = self.bot_data['config']['telegram'].get('chat_id', '@chollosweb')
        renderer = ServerMessageRendererHTML(item)
        bot_id = item['bot_id']
        item['chollo_url'] = self.create_link(self.identity, bot_id, item)
        image_url = item.get('image_url')
        chollo_url = item['chollo_url']
        for speaker in item['send_to']:
            for name in speaker:
                try:
                    if speaker[name]['state']:
                        if isinstance(item, Item):
                            item = item.get_dict()
                        message = renderer.get_message(name)
                        self.speakers[name].send_message(message, image_url=get_image(image_url), button_link=chollo_url)
                except:
                    continue

    def send_message_by_api(self, data: Dict) -> Dict:
        try:
            item = self.get_clean_item(data)
            _start_new_thread(self.send_message, (item,))
            return OK
        except:
            self.__logger.error('on [send_message_by_api] details:\n', exc_info=1)

    def create_link(self, identity: Identity, bot_id: str, item: Item):
        
        shortener_config = ShortenerConfig(self.database)
        value = shortener_config.get_config(identity, self.bot_id)
        shortener = ShortenerManager()
        shortener.set_shortener(value, self.database)
        redirector_url: str = shortener_config.get_redirector_url(identity, bot_id)
        return shortener.add_url(item['chollo_url'], from_web_app=True, redirector_url=redirector_url)['data']['url']

    def __init_bot_config(self):

        database_bot_instance = Bot(self.database)
        configs = database_bot_instance.get_bot_data(self.identity, self.bot_id).get('config', {})
        for name in configs:
            self.speakers[name].update_config(**configs[name])


    @staticmethod
    def get_clean_item(data) -> Dict:
        available_channels = {'fb':'facebook', 'tw':'twitter', 'tg':'telegram'}
        channels = data.pop('redes', None)
        data['discount'] = data.get('discount_code', None)
        data['market'] = data['market'].title().replace(' ', '')

        if channels is not None:
            data['send_to'] = []
            for channel in channels.split(','):
                data['send_to'].append({available_channels[channel]:{'state': True}})
            return data 
