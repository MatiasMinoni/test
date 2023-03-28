from requests import Session
from bs4 import BeautifulSoup
from re import search
from uuid import uuid4


class SoyDeChollosAPi:

    ORIGIN = "https://soydechollos.com/nuevos"
    API_URL = "https://soydechollos.com/api/chollo"
    ENDPOINT = "/getMore"

    PAYLOAD = {"brand": 0, "page": 1, "category_id": 0, "favorites": 0, "popular": 0,
               "new": 1, "sent": 0, "commented": 0, "store": 0, "tag": "0", "user_id": 0}

    HEADERS = {"Cookie": "__cfduid={}; G_ENABLED_IDPS=google; _ga=GA1.2.1766516862.1605661258; XSRF-TOKEN={}; soydechollos_session={}; _gid=GA1.2.574737916.1605855095; _gat_gtag_UA_66485014_1=1",
               "X-XSRF-TOKEN": "eyJpdiI6IlRrZnQrV1kva0NzUlltOUl0a1ZUS1E9PSIsInZhbHVlIjoiQ3FxNis5Qk9lSXJnR0lGa2hHbjN2anFiczREK2hZV2lpSHRpTEM2ejJJRzhrR0NyZWNMY2pTSlVQZnplN1ZJbGJRV0dzRCt0bXpnNFpZRlV6ei83bGhIaEJ4WE51dEZUNmxBUnpudTRKR0RZODc3VHNXMzBkdVZMYnR0RTMwUmciLCJtYWMiOiIxODQ3YWM2YTQ3NGQ1ZDQ5ZTRjODdiMzUyMzBkZjg4NjcwYTNiZTY5ZmQ3ZGIyMjZiNTc3OTc2ZGE2YmI4OGY3In0="}
    FILTERS = ['new', 'popular']

    ISO_CODE = 'EURO'
    SYMBOL = '€'
    SYMBOL_SIDE = 'right'

    def __init__(self):
        self._session = Session()
        self.refresh_headers()

    def refresh_headers(self):

        HEADERS = {"Cookie": "__cfduid={}; G_ENABLED_IDPS=google; _ga=GA1.2.1766516862.1605661258; XSRF-TOKEN={}; soydechollos_session={}; _gid=GA1.2.1177504532.1611779776; _gat_gtag_UA_66485014_1=1",
                   "X-XSRF-TOKEN": "eyJpdiI6IlRrZnQrV1kva0NzUlltOUl0a1ZUS1E9PSIsInZhbHVlIjoiQ3FxNis5Qk9lSXJnR0lGa2hHbjN2anFiczREK2hZV2lpSHRpTEM2ejJJRzhrR0NyZWNMY2pTSlVQZnplN1ZJbGJRV0dzRCt0bXpnNFpZRlV6ei83bGhIaEJ4WE51dEZUNmxBUnpudTRKR0RZODc3VHNXMzBkdVZMYnR0RTMwUmciLCJtYWMiOiIxODQ3YWM2YTQ3NGQ1ZDQ5ZTRjODdiMzUyMzBkZjg4NjcwYTNiZTY5ZmQ3ZGIyMjZiNTc3OTc2ZGE2YmI4OGY3In0="}

        self._session = Session()
        r = self._session.get(self.ORIGIN)
        
        if r.status_code == 200:
            try:
                xsrf_token = r.cookies['XSRF-TOKEN']
                chollos_session = r.cookies['soydechollos_session']
                __cfuid = search(
                    r'__cfduid=(.*);', r.headers['Set-Cookie']).group(1).split(';')[0]
            except:
                __cfuid = ""

            self.HEADERS['Cookie'] = HEADERS['Cookie'].format(
                __cfuid, xsrf_token, chollos_session)
            self.HEADERS['X-XSRF-TOKEN'] = r.cookies['XSRF-TOKEN'].replace(
                '%3D', '=')

    def get_new_items(self, filter='new'):
        items = []
        if filter in self.FILTERS:
            for i in range(2):
                items += self._get_new_items(page=1, filter=filter, index=i+1)

        return items

    def _get_new_items(self, page=1, filter='new', index=1):

        self.switch_to(filter)
        if index == 2:
            self.PAYLOAD['new'] = 0

        self.PAYLOAD['page'] = page

        items = []
        response = self._session.post(
            self.API_URL+self.ENDPOINT, data=self.PAYLOAD, headers=self.HEADERS)
        if response.status_code == 200:
            for (index, item) in enumerate(response.json()['data'], 0):
                try:
                    items.append({"title": item['name'], "description": '', "price": item['price'], "regular_price": item['regular_price'], "is_linked": False, "linked_name": "SoyDeChollos", "is_chollo_linked": True,'is_soydechollos': True, "original_chollo_url":item['full_url'], "linked_url":"https://soydechollos.com/"+item['slug'],
                                  "market": item["store"]['name'], "id": str(uuid4()), "chollo_url": item["full_url"], "index": index, "image_url": item['image'], "original_url": item['image'], "discount": item['discount_code'], "currency": {'iso_code': self.ISO_CODE, 'symbol': self.SYMBOL, 'symbol_side': self.SYMBOL_SIDE}})
                except:
                    continue
            return items
        else:
            self.refresh_headers()

    def switch_to(self, filter: str):
        if filter == 'new':
            self.PAYLOAD['popular'] = 0
            self.PAYLOAD['new'] = 1
        elif filter == 'popular':
            self.PAYLOAD['popular'] = 1
            self.PAYLOAD['new'] = 0

if __name__ == "__main__":
    test = SoyDeChollosAPi()
    print(test.get_new_items(filter='new'))
