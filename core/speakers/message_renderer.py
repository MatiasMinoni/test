from abc import abstractclassmethod, ABC
from typing import Dict
from bs4 import BeautifulSoup
from core.speakers.utils import DOTS, TWITTER_CHARACTER_LIMIT, get_image
from core.webs.items_manager import Item
from os import getenv

class MessageRenderer(ABC):

    REDIRECT_URL = getenv('REDIRECT_URL', 'https://www.soydechollos.com/api/redirect?redirect=')

    @abstractclassmethod
    def get_message(self, speaker_name: str):
        raise NotImplementedError('get_message')

    @abstractclassmethod
    def parse_message(self, speaker_name: str):
        raise NotImplementedError('parse_message')

    @abstractclassmethod
    def get_log_response(self):
        raise NotImplementedError('get_log_response')

class ServerMessageRendererHTML(MessageRenderer):

    def __init__(self, item: Item) -> None:
        super().__init__()
        self.item = item
        self.parse_to_facebook = False

    def get_message(self,  speaker_name: str) -> str:
        self.speaker_name = speaker_name

        return self.parse_message(speaker_name)

    def parse_message(self, speaker_name: str) -> str:

        if speaker_name == 'telegram':
            self.parse_to_facebook = False
            return self.template(character_limit=-1)
        elif speaker_name == 'twitter':
            self.parse_to_facebook = False
            return self._get_twitter_message()
        elif speaker_name == 'facebook':
            self.parse_to_facebook = True
            return self._parse_to_normal_text(-1)

    def template(self, character_limit: int):

        template = f'<a href="{get_image(self.image_url)}">&#8205;</a><strong>{self.title}</strong>🔥 #{self.market}\n<em>{self.regular_price}{self.offer_price}</em>\n🔰Enlace: {self.url+self.discount_code}\n\n{self.description[0::] if character_limit == -1 else self.description[0:character_limit]+"..."}{self.from_web_chollos}'
        return template

    def _parse_to_normal_text(self, character_limit: int):
        return BeautifulSoup(self.template(character_limit), 'lxml').get_text()

    def get_log_response(self):
        pass

    @property
    def url(self):

        url = self.chollo_url
        return url

    @property
    def image_url(self):
        return self.item['image_url']
    
    @property
    def title(self):
        return self.item['title']
    
    @property
    def market(self):
        return self.item['market'].capitalize()
    
    @property
    def space(self):
        return '\n'
    
    @property
    def chollo_url(self):
        return self.item['chollo_url']
    
    @property
    def discount_code(self):
        if self.item['discount'] is not None and len(self.item['discount']) >= 1:
            return f'{self.space}✂️Código: <code>{self.item["discount"]}</code>'
        return ''

    @property
    def regular_price(self):
        regular_price = self.item.get('regular_price') is not None and len(str(self.item.get('regular_price', ''))) >= 1
        currency: Dict = self.item.get('currency', {'iso_code': 'EURO', 'symbol': '€', 'symbol_side': 'right'})
        symbol: str = currency.get('symbol')
        symbol_side: str = currency.get('symbol_side')
        price = f'{symbol if symbol_side == "left" else ""}{self.item["regular_price"]}{symbol if symbol_side == "right" else ""}'

        if regular_price:
            return self.space + f'{"❌Antes: " + price}'
        return ''

    @property
    def offer_price(self):
        offer_price: str = self.item.get('price') is not None and len(str(self.item.get('price', ''))) >= 1
        currency: Dict = self.item.get('currency', {'iso_code': 'EURO', 'symbol': '€', 'symbol_side': 'right'})
        symbol: str = currency.get('symbol')
        symbol_side: str = currency.get('symbol_side')
        price = f'{symbol if symbol_side == "left" else ""}{self.item["price"]}{symbol if symbol_side == "right" else ""}'

        if offer_price:
            return self.space + f'{"🔥<strong>PRECIO OFERTA: "+price+"</strong>🔥"}'
        return self.space + "Descuento💥"

    @property
    def from_web_chollos(self):
        return f"✔️Visto en: {self.item.get('channel_name')}\n" if self.speaker_name == 'telegram' else ''
    
    @property
    def description(self):
        if not self.parse_to_facebook:
            return self.item.get("description", "")+self.space*2 if len(self.item.get("description", "")) >= 1 else ""
        else:
            return ''

    def _get_twitter_message(self, character_limit=-1):

        message = self._parse_to_normal_text(character_limit)
        if len(message) <= TWITTER_CHARACTER_LIMIT:
            return message
        else:
            character_limit = len(self.description) + ((TWITTER_CHARACTER_LIMIT - len(message)) - DOTS)
            return self._get_twitter_message(character_limit=character_limit)

class ClientMessageRenderer(MessageRenderer):

    def get_message(self, item: Item):
        pass
    
    def parse_message(self, item: Item):
        pass