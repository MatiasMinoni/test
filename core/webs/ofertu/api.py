from requests import Session, get
from bs4 import BeautifulSoup as bs4
from uuid import uuid4

# https://back-ofertu.herokuapp.com/api/v1/offers?order=ranking&page=2&per_page=10
# https://back-ofertu.herokuapp.com/api/v1/offers/discover

     
class OfertuApi:

    ORIGIN = "https://www.ofertu.co/"
    API_URL = "https://back-ofertu.herokuapp.com/api/v1/"
    ENDPOINT = "offers?order={}&page={}&per_page=20"
    HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36 OPR/85.0.4341.72',}
    FILTERS = ['new', 'popular']
    FILTER = {'new': 'published_at', 'popular': 'ranking'}
    
    ISO_CODE = 'CP'
    SYMBOL = '$'
    SYMBOL_SIDE = 'left'

    def __init__(self):
        self._session = Session()

    def get_new_items(self, filter='new'):
        self.items = []
        if filter in self.FILTERS:
            for i in range(2):
                self._get_new_items(page=i+1, filter=filter)

        return self.items

    def _get_new_items(self, page=1, filter='new'):
        
        response = self._session.get(self.API_URL + self.ENDPOINT.format(self.FILTER[filter], page), headers={'accept': 'application/json'})
        if response.status_code == 200:
            content = response.json()
            if len(content) > 0:
                for (i, item) in enumerate(content):
                    try:
                        if not item['aproved']:
                            continue

                        template = {
                            "title": item['title'],
                            "description": self.format_description(item['description']),
                            "linked_url": self.ORIGIN + self.get_slug(item['title'], str(item['id'])),
                            "price": self.format_price(item.get('actual_price', None)),
                            "regular_price": self.format_price(item.get('normal_price', None)),
                            "market": item['shop'],
                            "id": str(uuid4()),
                            "discount": item.get('code', None),
                            "image_url": item['image_url'],
                            "original_url": item['image_url'],
                            "index": i,
                            "chollo_url": self.get_url(item['url']),
                            "currency": {'iso_code': self.ISO_CODE, 'symbol': self.SYMBOL, 'symbol_side': self.SYMBOL_SIDE},
                        }
                    except:
                        continue
                    self.items.append(template)

    @staticmethod
    def get_slug(title: str, id: str):
        import unicodedata
        title = ''.join(c for c in unicodedata.normalize('NFD', title) if unicodedata.category(c) != 'Mn')

        symbols: str = '+-_()[]{}+=&|!@#$%^&*'
        for symbol in symbols:
            title = title.replace(symbol, ' ')
        return 'ofertas/' + '-'.join(title.split()).lower() + '-' + id

    def get_url(self, url: str):
        try:
            r = get(url, headers=self.HEADERS, timeout=5)
            if r.status_code in [200, 301, 403]:
                return r.url

        except:
            return url
    def format_description(self, description: str):

        if description is None:
            return None
        description = description.split('insert":"')[1].split('"},{"attributes')[0]
        description= description.replace('\n"', '')
        description= description.replace('\n', '')
        return description

    def format_price(self, price: str):
        if price is None:
            return None
        price = str(price)
        price = price.replace(',', '').replace('.', '')
        return f'{int(price):,}'.replace(',', '.') if price.isdigit() else price

if __name__ == "__main__":
    import pprint
    test = OfertuApi()
    pprint.pprint(test.get_new_items(filter='new'))
