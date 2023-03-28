import asyncio
from os import getenv
from typing import List, Dict

from core.webs.chollitos import ItemsArray, ItemParser
from ez_telegram import EzClient


def get_channels() -> List[str]:

    channels = getenv('TELEGRAM_CHANNELS')
    channels = channels.split(',')
    return channels

class ChollitosApi:

    def __init__(self):
        self.items = ItemsArray(max=70)

        self.client = EzClient()

    def get_new_items(self, *args, **kwargs) -> List[Dict]:

        self._get_new_items()
        return self.items.get()

    def _get_new_items(self):
        self.items.items = []

        for channel in get_channels():
            messages = self.client.get_messages(channel=channel)
            for message in messages:
                parser = ItemParser(message)
                if parser.is_valid():
                    self.items.add(parser.parse_text(channel))