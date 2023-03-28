from bitlyshortener import Shortener
from os import getenv
from requests import get, post

TWITTER_CHARACTER_LIMIT = 240
DOTS = 3

class BitlyShortener:

    TOKEN = getenv('BITLY_TOKEN', "6caf63a0cba283542cc671e612722579209e566b")

    URL = ""

    def __init__(self):
        self._api = Shortener(tokens=[self.TOKEN], max_cache_size=128)

    def add_url(self, url: str, **kwargs):
        redirector_url = kwargs.get('redirector_url')
        url = redirector_url + url['url']
        try:
            response = 'https://bit.ly/' + self._api.shorten_urls([url])[0].replace('https://j.mp/', '')
            return response
        except:
            return url

def download_image(image_url):

    filename = './temp_image.jpeg'
    with open(filename, 'wb') as image:

        if (r := get(image_url)).status_code == 200:
            image.write(r.content)
            image.close()
            return filename
    return

def get_image(url):
    try:
        token = "3c540132ca5695976f8d09634903bcea"
        assert 'data' in (image_url := post(f"https://api.imgbb.com/1/upload?key={token}", files={'image':get(url).content}).json())

        return image_url['data']['url']
    except:
        return url