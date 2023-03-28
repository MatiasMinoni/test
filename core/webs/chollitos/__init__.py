from re import findall, search, compile, MULTILINE
from typing import Dict, List
from uuid import uuid4

from requests import get

class ItemsArray:
    def __init__(self, max: int = 70):
        self.max = max
        self.items = []
    
    def add(self, item: Dict):
        """ Adds an item to the array """
        if len(self.items) > self.max:
            self.items.pop(-1)
            self.add(item)
            return
        
        self.items.insert(0, item)

    def get(self) -> List[Dict]:
        """ Returns a list of items """

        items = self.items.copy()
        items.reverse() 
        return items


class ItemParser:
    """ Item parser for telegram messages
    
    Format: {
        "title": "",
        "description": "",
        "price": "",
        "regular_price": "",
        "market": "",
        "id": "",
        "chollo_url": "",
        "image_url": "",
        "index": "",
        "linked_url": "",
        "discount": "",
        "currency": DefaultCurrency
    }
    
    """
    CURRENCY = {
        'iso_code': 'EURO',
        'symbol': '€',
        'symbol_side': 'right'
    }
    URL_PATTERN = compile(r'https?://(?!(img|s|cdn|t.me))[a-zA-Z0-9./\-]{10,}')
    def __init__(self, text: str):
        self.text = text
        self.item: Dict = {}

    def is_valid(self):
        """ Check if item is valid """
        return len(self.text) >= 50 and len(self._title()) > 0

    def parse_text(self, username):
        """ Parse text and return item """
        title = self._title()
        description = self._description()
        price = self._price()
        regular_price = self._regular_price()
        market = self._market()
        id = str(uuid4())
        chollo_url = self._chollo_url()
        image_url = self._image_url()
        linked_url = self._linked_url()
        discount = self._discount()
        currency = self._currency()

        self.item = {
            "title": title,
            "description": description,
            "price": price,
            "regular_price": regular_price,
            "market": market,
            "id": id,
            "chollo_url": self.get_url(chollo_url),
            "image_url": image_url,
            "linked_url": linked_url,
            "discount": discount,
            "currency": currency,
            "channel_username": username
        }
        return self.item
    def get_url(self, url: str):
        """ Get url """
        try:
            # user-agent
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'}
            return get(url, headers=headers, allow_redirects=True, timeout=5).url
        except:
            return url

    def _title(self):
        """ Get title """
        
        # [EMOJI] Cortapelos Rowenta Advancer Easy TN5201 solo 12,9€ [EMOJI] (PVP: +35€)
        # how to know emojis in a regex
        for text in self.text.split('\n'):
            size = len(text.replace('*', ''))
            if size >= 45 and size <= 70 and not (text.find('http') > 1):
                return text.replace('*', '')
        return ''
    
    def _description(self):
        for text in self.text.split('\n'):
            size = len(text.replace('*', ''))
            if size >= 120 and not (text.find('https://cdn') > 1) and not text.count('#'):
                return text.replace('*', '')

        return ''    
    def _price(self):
        """ Get price """

        pattern = r'[0-9]{1,3}[,.]{0,1}[0-9]{0,2}€'
        match = findall(pattern, self.text)
        if match:
            converto_to_float = lambda x: float(x.replace(',', '.').replace('€', ''))
            return str(min([converto_to_float(x) for x in match]))
        return None
    
    def _regular_price(self):
        """ Get regular price """

        pattern = r'[0-9]{1,3}[,.]{0,1}[0-9]{0,2}€'
        match = findall(pattern, self.text)
        if match:
            converto_to_float = lambda x: float(x.replace(',', '.').replace('€', ''))
            return str(max([converto_to_float(x) for x in match]))
        return None

    def _market(self):
        """ Get market """

        pattern = r'#[a-zA-Z0-9]{2,}'
        match = search(pattern, self.text)
        if match:
            return match.group()

        return ''
    
    def _chollo_url(self):
        """ Get chollo url """
        # pattern of an url with uri but not img, jpg, png, gif
        pattern = r'https?://(?!img|cdn|t.me)[a-zA-Z0-9./\-]{10,}(?!jpg|png|gif|img)'
        match = findall(pattern, self.text)
        photo_url = self._image_url()
        for url in match:
            if url != photo_url and not max([url.count(x) for x in ['img', 'jpg', 'png', 'gif']]):
                return url
        return ''
    
    def _image_url(self):
        """ Get image url """
        # pattern of an url with uri
        pattern = r'https?://(?!(s|cdn|t.me))[a-zA-Z0-9./\-]{10,}'
        match = search(pattern, self.text)
        if match:
            return match.group()

        return ''
    
    def _linked_url(self):
        return self._chollo_url()
    
    def _discount(self): return None

    def _currency(self):
        return self.CURRENCY



if __name__ == '__main__':
    # REGEX TO GET THE TITLE 🔹 Cortapelos Rowenta Advancer Easy TN5201 solo 12,9€ ❗️💥 (PVP: +35€)
    pattern = r''
    test = ItemParser("""
BARATAS❗️💥 (http://s.chollo.to/lAMJQ6.png) #Aboutyou 🇪🇸 (https://chollo.to/z5g9k)

🔹Chaqueta entretiempo Jack & Jones 11.9€❗️💥 (PVP: +26€)
✨Preciazo para estas chaquetas de entretiempo tipo bomber de la marca Jack & Jones. Tienen los puños acanalados y bolsillos laterales. Disponible en 3 colores.

    🔰Negro (https://chollo.to/k7h5y) 
    🔰Verde clarito (https://chollo.to/13pe6) 
    🔰Verde oscuro (https://chollo.to/g3q5i)

🦋 Chollometro.com
🦄@chollos / @descuentos / @chollometro
    """)
    test.parse_text()
    print(test.item)