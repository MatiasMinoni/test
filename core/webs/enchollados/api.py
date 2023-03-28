from requests import Session, get
from typing import List
from uuid import uuid4
from bs4 import BeautifulSoup as bs4
from requests.exceptions import ConnectionError, ReadTimeout

class EncholladosApi:

    FILTER = {'new': 'featured', 'popular': 'popular'}
    URL = 'https://enchollados-2c131.appspot.com'
    ENDPOINT = '/_ah/api/productApi/v1/getProducts_v2?page=1&itemsPage=40&productType=featured'
    DEFAULT_ENDPOINT = '/_ah/api/productApi/v1/getTrending?limit=40&page=1'
    ENDPOINT_PACK_AHORRO = '/_ah/api/productApi/v1/getProducts_v2?itemsPage=40&page=1&category=%23PackAhorro&productType=all'
    HEADERS = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 OPR/72.0.3815.459'}
    FILTERS = ['new', 'popular']

    ISO_CODE = 'EURO'
    SYMBOL = '€'
    SYMBOL_SIDE = 'right'

    def __init__(self, pack_ahorro=False):
        self._create_session()
        self.endpoint = lambda type: self.DEFAULT_ENDPOINT if type == 'popular' else self.ENDPOINT
        if pack_ahorro:
            self.FILTERS = ['new']
            self.endpoint = lambda type: self.ENDPOINT_PACK_AHORRO

    def _create_session(self):
        self._session = Session()
        self._session.get(self.URL)

    def get_new_items(self, filter='new') -> List:
        self.items = []
        if filter in self.FILTERS:
            self._get_new_items(filter)
        return self.items

    def _get_new_items(self, filter: str, offset: int = 0) -> List:
        response = self._session.get(
            self.URL+self.endpoint(filter), headers=self.HEADERS)
        if response.status_code == 200:
            content = response.json()
            if content.get('products'):
                for (i, item) in enumerate(content['products']['items']):
                    try:
                        if item['productStatus']['availabilityCode'] != 'AVAILABLE':
                            continue

                        template = {
                            "title": item['name'],
                            "description": bs4(item['description'], 'lxml').get_text(),
                            "linked_url": 'https://enchollados.es/chollo/' + item.get('name').replace(' ', '-').lower() + '-' + item.get('id'),
                            "price": str(item['price']),
                            "regular_price": str(item['oldPrice']),
                            "market": item['shop'],
                            "id": str(uuid4()),
                            "discount": item.get('discountCode', None),
                            "image_url": item['images'][0],
                            "original_url": item['images'][0],
                            "index": i,
                            "chollo_url": self.get_url(item['url']),
                            "currency": {'iso_code': self.ISO_CODE, 'symbol': self.SYMBOL, 'symbol_side': self.SYMBOL_SIDE},
                        }
                    except:
                        continue

                    self.items.append(template)

    def get_url(self, url: str) -> str:
        
        try:
            response = self._session.get(url, headers=self.HEADERS, timeout=2.5)
            if response.status_code == 200:
                return response.url
        except:
            return url
        return url

if __name__ == '__main__':
    from pprint import pprint
    api = EncholladosApi(pack_ahorro=False)
    items = api.get_new_items(filter='popular')
    # check repeated items
    pprint(items)