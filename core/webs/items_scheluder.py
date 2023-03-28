from app.database.identity import Identity
from core.webs.utils import CTime
from types import FunctionType
from typing import Any, Dict, List, NoReturn
from core.webs.items_manager import Item
from threading import _start_new_thread
from eventlet import sleep
import logging

ONE_SEC = 1


class ItemScheluder:
    item: Dict

    def __init__(self, on_finish : FunctionType):
        self._processing = True
        self.on_finish = on_finish

    def __process(self):

        self._process_scheluder()

    def _process_scheluder(self) -> NoReturn:

        for speaker in self.item['send_to']:
            name = list(speaker.keys())[0]

            if int((current_item := speaker[name])['time']) >= 1 and not current_item.get('status', 'off') == 'running':
                current_item['status'] = 'running'
                _start_new_thread(self.__task_thread, (current_item, name,))
            else:
                if not int(speaker[name]['each_time']) >= 1 and 'status' in speaker[name]:
                    current_item['status'] = 'off'
                    self.dispatcher_items_update()
                    self.on_finish(self.item['id'])

    def __task_thread(self, current_item: Dict, bot_id: str):

        while current_item['status'] == 'running':

            sleep_time = int(current_item['time'])
            sleep(sleep_time)

            if sleep_time >= 1 and current_item['each_time'] >= 1:
                if current_item['state']:
                    current_item['each_time'] -= 1

                    self.dispatcher_message_event(self.item, bot_id)
                    self.dispatcher_items_update(current_item, bot_id)

                else:
                    return self.on_finish(self.item['id'])
            else:
                return self._process_scheluder()


    def schelude(self, item: Item, dispatcher_message_event: FunctionType, dispatcher_items_update: FunctionType, identity_data):

        self.item = item
        self.dispatcher_message_event = dispatcher_message_event

        self.dispatcher_items_update = dispatcher_items_update
        self.__process()


class GlobalScheluder:

    def __init__(self, items: List[Dict], dispatcher_message_event: FunctionType, dispatcher_items_update: FunctionType):
        self.items = items

        self.dispatcher_message_event = dispatcher_message_event
        self.dispatcher_items_update = dispatcher_items_update

        self.GLOBAL_SCHELUDER_STATUS = True
        self.isolateds_scheluders = {}

        self.__logger = logging.getLogger('GlobalScheluder')

    def __process(self):
        self.__logger.info('Thread<__process> started ')

        while self.GLOBAL_SCHELUDER_STATUS:
            try:

                for user_token in self.items:
                    
                    for bot_id in self.items[user_token]:

                        for item in self.items[user_token][bot_id]:

                            self.__logger.debug(f'Thread<__process> {item}')
                            ctime = CTime()
                            if item.scheluded_time == ctime.current_time and item.status == 'running':
                                item.status = 'off'
                                self.dispatcher_items_update(user_token, item)
                                self.dispatcher_message_event(user_token, item)

                                if not self.scheluder_still_alive(item.id):
                                    identity_data = (Identity('token', '', user_token), bot_id)
                                    self.isolateds_scheluders[item.id] = ItemScheluder(on_finish=self.delete_isolated_scheluder)
                                    _start_new_thread(self.isolateds_scheluders[item.id].schelude, (
                                        item.item, self.dispatcher_message_event, self.dispatcher_items_update, identity_data))
            except:
                self.__logger.error("on [__process] ", exc_info=1)

            sleep(ONE_SEC)

    def start_scheluder(self):

        self.__process()

    def delete_isolated_scheluder(self, id):

        del self.isolated_scheluders[id]

    def scheluder_still_alive(self, id):

        return id in self.isolateds_scheluders