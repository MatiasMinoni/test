from concurrent.futures import as_completed
from typing import List
from requests_futures.sessions import FuturesSession
from requests import Session, get
from urllib.parse import unquote
from bs4 import BeautifulSoup
from re import search
from uuid import uuid4
from time import sleep

OK = 200
SUCCESS = 'success'
LIMIT = 10


class ChollometroApi:
    FILTER = {'new':'nuevos', 'popular':'populares', 'featured':'/'}
    URL = "https://chollometro.com/{}"
    PARAMS = "?page={}&ajax=false&layout=vertical"
    HEADERS = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 OPR/72.0.3815.487', 'upgrade-insecure-requests':'1'}
    HEADERS_CHOLLOMETRO = {'updgrade-insecure-requests':'1', 'sec-fetch-mode':'navigate', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 OPR/77.0.4054.275'}
    INDICES = 10
    
    ISO_CODE = 'EURO'
    SYMBOL = '€'
    SYMBOL_SIDE = 'right'

    def __init__(self):
        self._create_session()

    def _create_session(self):
        self._session = Session()

    def get_new_items(self, filter='new') -> List:

        items: List = []

        for i in range(1, self.INDICES):
            items.extend(self._get_new_items(filter, page=i))
        return items

    def _get_new_items(self, filter: str, page: int) -> List:

        response = self._session.get(self.URL.format(self.FILTER[filter.lower()])+self.PARAMS.format(page), headers=self.HEADERS_CHOLLOMETRO)
        if response.status_code == OK and (content := response.json())['status'] == SUCCESS:
            document = BeautifulSoup(content['data']['content'], 'lxml').findAll(
                'div', {'class': 'threadGrid thread-clickRoot'})

            return self.get_items(document)

    def get_items(self, document: BeautifulSoup) -> list:

        items = []
        chollos_url = []
        for (index, item) in enumerate(document, 0):
            sleep(0.2)
            if index >= LIMIT:
                break
            tag_a = item.findAll('a')
            try:

                if item.find('div', {'class':'cept-vote-box vote-box vote-box--muted space--h-2 border border--color-borderGrey bRad--a text--color-grey space--mr-3'}):
                    continue
                title = tag_a[0]['title']
                linked_url = tag_a[0].get('href', self.URL.replace('{}',''))
                image_url = item.find('img')['src'].replace('300x300', '1024x1024')
                price = self.get_price(item)

                regular_price = self.get_regular_price(item)
                discount_code = self.get_discount_code(item)
                currency = {'iso_code':self.ISO_CODE, 'symbol':self.SYMBOL, 'symbol_side':self.SYMBOL_SIDE}
                description = item.find('div', {'class': 'userHtml userHtml-content'}).get_text(
                ).replace('\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tLeer más', '').replace('\t', '')
                store = item.find(
                    'span', {'class': 'cept-merchant-name text--b text--color-brandPrimary link'}).get_text()
                chollos_url.append(self.get_chollo_url(item))
                items.append({'title': title, 'description': description, 'linked_url': linked_url, 'price': price, 'regular_price': regular_price, 'market': store, 'id': str(
                    uuid4()), 'index': index, 'chollo_url': '', 'image_url': image_url,'original_url': image_url, 'discount': discount_code, 'currency': currency})

            except:
                continue

        urls = self._get_items(chollos_url)
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
                chollos_url[i] = self.fix_broken_url(response.url)

            except:
                print("[x] error with: " + urls[i])
                chollos_url[i] = urls[i]

        chollos_url = self.sorted(chollos_url)
        assert len(urls) == len(chollos_url)
        return chollos_url
    
    def validate_url(self, url):
        return url.startswith('https://chollometro.com/') or url.startswith('https://www.chollometro.com/')

    def sort_urls(self, urls: List, items: List) -> List:

         for (i, url) in enumerate(urls, 0):
            try:
                if self.validate_url(url):
                    items[i].update({'chollo_url':url})
                    items[i].update({'title': '[VERIFICAR ENLACE]' + items[i]['title']})
                else:
                    items[i].update({'chollo_url':url})
            except:
                continue

    @staticmethod
    def get_price(item):

        try:
            price = item.find('span', {'class': 'thread-price'}).get_text()
            if price.endswith('%'):
                return
        except AttributeError:
            return

        return price.replace('€', '')

    @staticmethod
    def get_regular_price(item):

        try:
            regular_price = item.find(
                'span', {'class': 'mute--text'}).get_text()

            if regular_price.endswith('%'):
                return
        except AttributeError:
            return

        return regular_price.replace('€', '')

    @staticmethod
    def get_discount_code(item):

        try:
            code = item.find('input', {'class': 'lbox--v-4'})['value']
        except:
            return

        return code

    @staticmethod
    def get_chollo_url(item):

        return item.find('a', {'class': 'boxAlign-jc--all-c space--h-3 width--all-12 btn border--mode-round btn--mode-primary'})['href']

    @staticmethod
    def sorted(items):
        _list = []

        for i in range(len(items)):
            _list.append(items[i])
        return _list

    @staticmethod
    def fix_broken_url(url):
        if url.count('tradedoubler') >= 1:
            try:
                return unquote(url).split('url=')[1]
            except:
                return url
        elif url.count('chollometro.digidip.net') >=1:
            try:
                return unquote(url).split('url=')[1]
            except:
                return url
        return url

if __name__ == '__main__':
    from time import time
    api = ChollometroApi()
    init_time = time()
    for item in api.get_new_items(filter='new'):
        if item['chollo_url'].count(item['market'].lower()) >=1:
            print(item['market'], item['chollo_url'], 'SUCCESS')
        else:
            print(item['market'], item['chollo_url'], 'ERROR')

    print(f"execute time with 4 workers {init_time - time()}")
