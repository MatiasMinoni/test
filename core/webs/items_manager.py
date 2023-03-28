# Work refactor in progress 16/4/2021

from app.database.models.chollos import Chollos
from dataclasses import dataclass, is_dataclass
from typing import Any, Dict, AnyStr, Union
import logging

@dataclass
class Item:

    item: Dict

    def __post_init__(self):
        self.__logger = logging.getLogger('Item')

    @property
    def id(self) -> AnyStr:
        return self.item.get('id')

    @property
    def scheluded_time(self):
        return self.item.get('time')

    @property
    def status(self):
        return self.item.get('status', 'running')
    
    @status.setter
    def status(self, value):
        self.item['status'] = value

    def update(self, obj : Union[Dict, Any]):
        self.__logger.debug(f"on [update] {obj}")

        if is_dataclass(obj):
            self.item.update(obj.item)
        else:
            self.item.update(obj)

    def get_dict(self) -> Dict:
        return self.item

class _ItemsManager(Chollos):
    _items: Dict = {}

    def __init__(self) -> None:
        self.__logger = logging.getLogger('_ItemsManager')

    def _add_item(self, current_item: Union[Dict, Item]) -> None:

        if not current_item.get('id') in self._items:
            self.__add_current_item_to_queue(current_item)
        
    def _edit_item(self, current_item: Union[Dict, Item]) -> None:

        self.__logger.debug(f'on _edit_item {current_item}')

        if current_item.get('id') in self._items:
            temp_item = self._items[current_item.get('id')]

            if not temp_item.scheluded_time == current_item['time']:
                current_item['status'] = 'running'

            self._items[current_item.get('id')].update(current_item)

    def _delete_item(self, current_item: Dict):

        if current_item.get('id') in self._items:
            del self._items[current_item.get('id')]

    def __add_current_item_to_queue(self, current_item: Union[Dict, Item]) -> None:

        if isinstance(current_item, Item):
            self._items[current_item.id] = current_item
        else:
            self._items[current_item.get('id')] = Item(current_item)

class ItemsManager(_ItemsManager):

    """
        Esta clase se encargara de manejar el proceso de administracion y  publicacion de los items a cada Speaker.
    """

    def __init__(self):
        super().__init__()
    
    def add_item(self, item : Dict) -> None:

        self._add_item(item)
    
    def delete_item(self, item: Dict) -> None:
        
        self._delete_item(item)

    def edit_item(self, item: Dict) -> None:

        self._edit_item(item)
    
    @property
    def items(self):
        items = []
        for key in self._items:
            items.append(self._items[key].get_dict())

        return items

    def get_items_objects(self):
        items = []
        for key in self._items:
            items.append(self._items[key])

        return items