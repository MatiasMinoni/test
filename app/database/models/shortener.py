from secrets import token_urlsafe
from typing import Dict, List
from bs4 import BeautifulSoup

from requests import get
from app.database.database import Database
from app.database.constans import *
from datetime import datetime
from calendar import month_abbr
from random import randint
from logging import getLogger

class ShortenerBase:

    def __init__(self, database: Database):

        self.__database = database
        self.__logger = getLogger('<ShortenerBase>')

    def __url_in_database(self, url: str) -> dict:
        return self.__database.urls_collection.find_one({'data.original_url': url}, {'_id':0})

    def _get_one_url(self, uuid: str) -> Dict:
        return self.__database.urls_collection.find_one({'uuid': uuid}, {'_id':0})

    def _add_url(self, data: Dict, from_web_app=False, redirector_url: str = '') -> Dict:

        url = redirector_url + data.get('url')
        name = self.get_title(data.get('title', ''), url)

        uuid = self.generate_url_uuid()
        url_alive = self.__url_in_database(url)
        payload = self.get_payload(name=name, url=url, uuid=uuid)

        if not from_web_app:
            if url_alive:
                return MAIN_URL + url_alive['uuid']

        uuid_alive = self._get_one_url(uuid)

        if url_alive:
            payload = self.update_payload_info(
                payload, url_alive, '¡La URL ya existe!')
            return payload

        if not uuid_alive:
            self.__database.urls_collection.insert_one(payload)
            payload.pop('_id')
            return payload

        return self._add_url(data)

    def _add_click(self, uuid: str, **kwargs):

        telegram_user_id_param = kwargs.get('telegram_user_id')

        if telegram_user_id_param and len(str(telegram_user_id_param)) < 100:
            self.__database.urls_collection.update_one({'uuid': uuid}, {'$inc': {'clicks': 1}, '$push': {'clicks_by_user': telegram_user_id_param}})
            return
        try:
            self.__database.urls_collection.update_one({'uuid': uuid}, {'$inc': {'clicks': 1}})
        except:
            self.__logger.error('An error ocurred in _add_click function', exc_info=1)

    def _delete_url(self, uuid: str):

        try:
            self.__database.urls_collection.delete_one({'uuid': uuid})
        except:
            self.__logger.error('An error ocurred in _delete_url function', exc_info=1)

    def _get_total_urls(self) -> int:

        try:
            return self.__database.urls_collection.count()
        except:
            self.__logger.error('An error ocurred in _get_total_urls function', exc_info=1)
            return 0

    def _get_all_urls(self) -> List:
        data = self.__database.urls_collection.find({}, {'_id':False})
        if data is not None:
            return list(data)
        return []

    def get_payload(self, **kwargs) -> Dict:
        payload = {'uuid': kwargs.get('uuid'), 'info': '¡Link Creado!', 'clicks': 0, 'data': {'url': MAIN_URL+kwargs.get('uuid'),
                                                                                              'title': kwargs.get('name', ''), 'created': self.created_date(), 'original_url': kwargs.get('url'), 'clicks': 0}}
        return payload

    def get_title(self, title: str, url: str)-> str:
        if not self.title_available(title):
            title = self.get_title_from_url(url)
        return title

    @staticmethod
    def is_valid_url(url: str) -> bool:

        return url.count('http') or url.count('https')

    @staticmethod
    def created_date():
        time = datetime.today()
        return {'day': time.day, 'month': month_abbr[time.month], 'year': time.year}

    @staticmethod
    def get_title_from_url(url):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 OPR/72.0.3815.487'}
        
        title = 'Sin titulo'
        try:
            response = get(url, headers=headers, timeout=3)

            if response.status_code == 200:
                document = BeautifulSoup(response.content, 'lxml')
                title = document.findAll('title')[0].get_text()[0:70]
        except:
            return title
        return title

    @staticmethod
    def title_available(title: str) -> bool:
        return len(title) >= 1

    @staticmethod
    def generate_url_uuid():
        return token_urlsafe(randint(5, 6)).replace('_', '').replace('-', '')

    @staticmethod
    def update_payload_info(payload: Dict, data: Dict, info: str) -> Dict:
        payload.update(data)
        payload['info'] = info

        if '_id' in payload:
            payload.pop('_id')
        return payload


class Shortener(ShortenerBase):
    def __init__(self, database: Database):
        super().__init__(database)

    def add_url(self, data: Dict, from_web_app=False, **kwargs) -> Dict:
        return self._add_url(data, from_web_app=from_web_app, redirector_url=kwargs.get('redirector_url', ''))
    
    def delete_url(self, uuid: str):
        return self._delete_url(uuid)

    def get_all_urls(self) -> List:
        return self._get_all_urls()

    def get_one_url(self, uuid: str) -> Dict:
        return self._get_one_url(uuid)

    def add_click(self, uuid: str, **kwargs)-> None:

        self._add_click(uuid, **kwargs)

    def get_total_urls(self) -> int:
        return self._get_total_urls()