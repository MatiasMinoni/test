import asyncio
import logging
from core.webs.chollitos.api import ChollitosApi
from core.webs.chollosdelsuper.api import ChollosDelSuperApi
from core.webs.items_scheluder import GlobalScheluder
from core.webs.items_manager import ItemsManager
from core.webs.soydechollos.api import SoyDeChollosAPi
from core.webs.chollometro.api import ChollometroApi
from core.webs.michollo.api import MicholloApi
from core.webs.enchollados.api import EncholladosApi
from core.webs.ofertu.api import OfertuApi
from threading import _start_new_thread
from time import sleep
from os import getenv
from typing import Any, Dict, NoReturn, List

QUEUE_SLEEP_TIME = getenv('QUEUE_SLEEP_TIME', 60)


class ChollosSpeakerController(ItemsManager):

    def __init__(self, socketio, db : Any):
        super().__init__()

        self.speaker_controller = None # SpeakerController(db)
        self.socketio = socketio
        self.current_user = None

    def publish_now(self, item):
        self.send_message(item)

    def send_message(self, item: Dict, **kwargs) -> NoReturn:

        log_response = self.speaker_controller.send_message(
            item, self.current_user, **kwargs)
        if log_response is not None:
            self.send_log_response(log_response)

    def send_message_by_api(self, item: Dict, **kwargs) -> Dict:

        item = self.get_clean_item(item)
        if item is not None:
            try:
                response = self.speaker_controller.send_message(item, kwargs.pop('token'))

                if response is not None:
                    return ({'status':'success', 'data':response}, 200)
            except:
                return ({'status':'error', 'msg':'Bad payload format!'}, 400)

        return ({'status':'error', 'msg':'There are no channels in the payload!'}, 400)

    def send_log_response(self, log: Dict) -> NoReturn:

        self.socketio.emit('add_to_logs', log, namespace='/app')

    def run(self) -> NoReturn:

        global_dispatcher_items_update = lambda : self.socketio.emit(
            'update_saved_items', self.items, namespace='/app')
        global_dispatcher_message_event = lambda message, **kwargs: self.send_message(
            message, **kwargs)
        global_scheluder = GlobalScheluder(self.get_items_objects, global_dispatcher_message_event, global_dispatcher_items_update)

        _start_new_thread(global_scheluder.start_scheluder, ())

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

class ChollosWebController:

    def __init__(self) -> None:
        self.filters = ['new', 'popular', 'featured']
        self.webs = {
            'soy_de_chollos':
            {
                'controller': SoyDeChollosAPi(),
                'items': {
                    'new': [],
                    'popular': []
                }
            },
            'chollometro':
            {
                'controller': ChollometroApi(),
                'items':
                {
                    'new': [],
                    'popular': []
                }
            },
            'michollo':
            {
                'controller': MicholloApi(),
                'items':
                {
                    'new': [],
                    'popular': []
                }},
            'enchollados':
            {'controller': EncholladosApi(),
             'items':
             {
                'new': [],
                'popular': []
            }},
            'enchollados_pack_ahorro':
            {
                'controller': EncholladosApi(pack_ahorro=True),
                'items':
                {
                    'new': [],
                    'popular': []
                }},
            'chollosdelsuper': {
                'controller': ChollosDelSuperApi(),
                'items':
                {
                    'new': [],
                }},
            'ofertu': {
                'controller': OfertuApi(),
                'items':{
                    'new': [],
                    'popular': [],
                    'featured': []
                }
            },
            'chollitos': {
                'controller': ChollitosApi(),
                'items': {
                    'new': [],
                    'popular': [],
                    'featured': []
                }
            }
        }

        self.__logger = logging.getLogger('ChollosWebController') 
        self.MAX_KEY_SIZE = 25
        self.MAX_LIST_SIZE = 8

    def _queue_process(self, controllers: List):
        
        self.__logger.info('Thread<_queue_process> started')
        while True:

            for name in controllers:
                try:
                    for filter in self.filters:
                        items = self.webs[name]['controller'].get_new_items(filter=filter)
                        if items is not None:
                            self.webs[name]['items'][filter] = items
                except:
                    self.__logger.error('Thread<_queue_process>', exc_info=1)

            sleep(QUEUE_SLEEP_TIME)

    def get_chollos(self, _web=False):

        chollos = {}

        for name in list(self.webs.keys()):
            if not _web:
                return self._format_to_webapp()
            else:
                chollos[name] = self.webs[name]['items']
        return chollos

    def run(self) -> None:
        _start_new_thread(self._queue_process, (['soy_de_chollos', 'chollometro'],))
        _start_new_thread(self._queue_process, (['enchollados', 'enchollados_pack_ahorro', 'michollo'],))
        _start_new_thread(self._queue_process, (['chollitos', 'chollosdelsuper', 'ofertu'],))
    
    def get_web_chollos(self, key, filter='new'):

        if isinstance(key, str):
            items = self.get_chollos(_web=True)
            if filter == 'featured' and key != 'chollometro' and key != 'chollosdelsuper':
                filter = 'new'

            if len(key) <= self.MAX_KEY_SIZE and key in self.webs:
                return {key:items[key].get(filter, [])}

            elif len(key) <= self.MAX_KEY_SIZE and key == 'all':
                return {
                    'soy_de_chollos': items['soy_de_chollos'].get(filter, []), 
                    'chollometro': items['chollometro'].get(filter, []), 
                    'michollo': items['michollo'].get(filter, []), 
                    'enchollados': items['enchollados'].get(filter, []), 
                    'enchollados_pack_ahorro': items['enchollados_pack_ahorro'].get(filter, []), 
                    'chollosdelsuper': items['chollosdelsuper'].get(filter, []), 
                    'ofertu': items['ofertu'].get(filter, []),
                    'chollitos': items['chollitos'].get(filter, [])
                    }
        else:
            if isinstance(key, list) and len(key) <= self.MAX_LIST_SIZE:
                response = []
                chollos = self.get_chollos(_web=True)

                for name in key:
                    if name in chollos:
                        response.append({name:chollos[name][filter]})

                if len(response) >= 1:
                    return response
    
    def _format_to_webapp(self):
        """make a new format for the webapp

        {
            new:
                soy_de_chollos:{},
                chollometro:{},
                michollo:{}
            popular:
                soy_de_chollos:{},
                chollometro:{},
                michollo:{}
        }
        """
        response = {'new':{}, 'popular':{}, 'featured': {}}
        for sort in response.keys():
            for key in self.webs:
                try:
                    response[sort].update({key:self.webs[key]['items'][sort]})
                except KeyError:
                    continue
        return response
