from typing import Dict
from app.database.models import Shortener as ChollitoShortener
from core.speakers.utils import BitlyShortener

class ShortenerManager:

    def __init__(self) -> None:
        self._shorteners = {'bitly':BitlyShortener, 'chollito':ChollitoShortener}
        self.shortener = self._shorteners['bitly']

    def set_shortener(self, value: str, database) -> None:
        if value == 'chollito':
            self.shortener = self._shorteners[value](database)
        else:
            self.shortener = self._shorteners[value]()

    def add_url(self, value: str, **kwargs) -> Dict:
        redirector_url: str = kwargs.get('redirector_url')
        url: str = self.shortener.add_url({'url':value}, from_web_app=kwargs.get('from_web_app', False), redirector_url=redirector_url)

        return url