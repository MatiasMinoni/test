from typing import List
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
from requests import Session
from bs4 import BeautifulSoup as BP
from uuid import uuid4


class MicholloApi:
    FILTER = {'new':'new', 'popular':'popular'}
    # new api url : https://app.michollo.com/api/home/popular?limit=10&offset=10&hide_expired=0
    API_URL = "https://app.michollo.com/api/home/{}?limit=10&offset={}&hide_expired=0"
    URL = "https://michollo.com"
    HEADERS = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 OPR/72.0.3815.459' , 'accept':'*/*', 'accept-language':'es-ES,es;q=0.9,en;q=0.8,ca;q=0.7', 'accept-encoding':'gzip, deflate, br', 'x-requested-with':'XMLHttpRequest'}
    INDICES = 100
    FILTERS = ['new', 'popular']

    ISO_CODE = 'EURO'
    SYMBOL = '€'
    SYMBOL_SIDE = 'right'

    def __init__(self):
        self._create_session()

    def _create_session(self):
        self._session = Session()
        self._session.get(self.URL)

    def get_new_items(self, filter='new') -> List:

        items: List = []
        if filter.lower() in self.FILTERS:
            for i in range(0, self.INDICES, 10):
                items.extend(self._get_new_items(filter, offset=i))
        return items
    
    def _get_new_items(self, filter: str, offset: int = 0) -> List:
    
        response = self._session.get(self.API_URL.format(self.FILTER[filter.lower()], offset), headers=self.HEADERS)
        items = []
        urls = []

        if response.status_code == 200:
            content = response.json()
            if content['ok']:
                for (i, item) in enumerate(content['deals']['results'], 0):
                    try:
                        if item.get("status") == "expired":
                            continue

                        discount_code = self.get_coupons(item)
                        description = BP(item['description'], 'lxml').get_text()
                        items.append({"title": item['name'], "description": description, "linked_url":self.URL+'/'+item.get('slug', ''), "price": str(item['sale_price']/100), "regular_price": str(item['old_price']/100),
                                  "market": item["store"][0]['name'], "id": str(uuid4()), "chollo_url": '', "index": i, "image_url":item['image_url'].replace('r/190/', ''),"original_url":item['image_url'], "discount":discount_code, "currency": {'iso_code':self.ISO_CODE, 'symbol':self.SYMBOL, 'symbol_side':self.SYMBOL_SIDE}})
                        urls.append(item['offer_url'])
                    except:
                        continue
        urls = self._get_items(urls)
        self.sort_urls(urls, items)

        return items
    
    def _get_items(self, urls):

        future_session = FuturesSession(session=self._session, max_workers=4)
        futures = []
        chollos_url = {}
        for (i, url) in enumerate(urls, 0):
            futures.append((future_session.get(url, timeout=5, headers=self.HEADERS), i))

        for (future, i) in futures:
            try:
                response = future.result()

                if response.status_code == 200:
                    chollos_url[i] = response.url
                else:
                    chollos_url[i] = response.url

            except:
                print("[x] error with: " + urls[i])
                chollos_url[i] = urls[i]

        chollos_url = self.sorted(chollos_url)
        assert len(urls) == len(chollos_url)
        return chollos_url

    @staticmethod
    def sorted(items):
        _list = []

        for i in range(len(items)):
            _list.append(items[i])
        return _list

    @staticmethod
    def get_coupons(item):
        try:
            coupons = item['coupons'][0]['code']
        except:
            return
        return coupons

    def validate_url(self, url):
        return url.count('https://a.michollo.to') == 1

    def sort_urls(self, urls, items):
        #         _rebase = lambda : [items[i].update({'chollo_url':item}) for (i, item) in enumerate(urls, 0)]
        for (i, url) in enumerate(urls, 0):
            try:
                if self.validate_url(url):
                    items[i].update({'chollo_url':url})
                    items[i].update({'title': '[VERIFICAR ENLACE]' + items[i]['title']})
                else:
                    items[i].update({'chollo_url':url})
            except:
                continue

if __name__ == "__main__":
    from time import time

    test = MicholloApi()
    execute_time = time()
    print(test.get_new_items(filter='popular')[0])
    print(f"Execute time {execute_time - time()}")