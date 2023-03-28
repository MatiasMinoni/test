from requests import Session
from bs4 import BeautifulSoup as bs4
from uuid import uuid4
from requests import get

class ChollosDelSuperApi:

    ORIGIN = "https://chollosdelsuper.com/"
    API_URL = "https://chollosdelsuper.com/pagina/{index}/?jsonResult=true"
    ENDPOINT = "getMore"
    # https://api.chollosdelsuper.com/api/v1/chollos/list?filter=

    FILTERS = ['new']
    HEADERS = {'authorization': 'Bearer LUfnIYXMkcJdKRBhReI3HTBoFFH7laHk78x5p-PVxC4',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36 OPR/85.0.4341.72',
    'accept': 'application/json',
    }



    ISO_CODE = 'EURO'
    SYMBOL = '€'
    SYMBOL_SIDE = 'right'

    def __init__(self):
        self._session = Session()


    def get_new_items(self, filter='new'):
        items = []
        if filter in self.FILTERS:
            for i in range(3):
                items += self._get_new_items(page=1, filter=filter, index=i+1)

        return items

    def _get_new_items(self, page=1, filter='new', index=1):

        items = []
        response = self._session.get(
            self.API_URL.format(index=page), headers=self.HEADERS)

        if response.status_code == 200:
            for (index, item) in enumerate(response.json().get('data').get('data'), 0): #                            "linked_url": self.ORIGIN + item.get('slug'),
                try:
                    items.append({"title": item['name'], "description": '', "price": item['price'], "regular_price": item['regular_price'], "linked_name": "ChollosDelSuper", "is_chollo_linked": True,"is_linked": False, "original_chollo_url":item['full_url'], "linked_url":self.ORIGIN+item['slug'],
                                  "market": item["store"]['name'], "id": str(uuid4()), "chollo_url": item["full_url"], "index": index, "image_url": item['image'], "original_url": item['image'], "discount": item['discount_code'], "currency": {'iso_code': self.ISO_CODE, 'symbol': self.SYMBOL, 'symbol_side': self.SYMBOL_SIDE}})
                except:
                    continue
            return items

if __name__ == "__main__":
    test = ChollosDelSuperApi()
    item = test.get_new_items(filter='new')
    popular = test.get_new_items(filter='popular')
    print(len(item), f'first item: {item[0]}')
    print(len(popular), f'first item: {popular[-1]}')
