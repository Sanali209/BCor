
# link prewiew by http://api.linkpreview.net/?key=123456&q=https://www.google.com 60 requests per hour

# link preview by https://get-link-preview.vercel.app/

# link preview by https://www.peekalink.io/ 100 requests per hour


import hashlib
import re

from diskcache import Cache


def get_previewjson(url):
    # need be registered on https://my.linkpreview.net/access_keys
    # on free 60 requests per hour
    import requests
    import json
    key = "83ba3a2728b3d0062c6631497c183315"
    url = url
    r = requests.get("http://api.linkpreview.net/?key=" + key + "&q=" + url)
    data = r.json()
    return data


class PreviewCache:
    def __init__(self):
        self.diskCache = Cache("D:\data\PreviewCache")

def get_first_words_count(string, count):
    return ' '.join(string.split(' ')[:count])

class PreviewGeneratorEngine:
    def __init__(self):
        self.name = "PreviewGeneratorEngine"

    def get_preview(self, url):
        response_data = {}
        if url is None:
            response_data['done'] = False
            return response_data
        data = get_previewjson(url)

        image_url = data['image']
        if image_url is not None and image_url != '':
            #if image url not contains extension download localy
            if not re.search(r'\.\w+$', image_url):
                import requests
                from PIL import Image
                from io import BytesIO
                response = requests.get(image_url)
                img = Image.open(BytesIO(response.content))
                img.save('temp.jpg')
                image_url = 'temp.jpg'

                import imgbbpy
                # for get api key need be registered on https://api.imgbb.com/

                client = imgbbpy.SyncClient('0eb8dc2bc4877cfbe8a4dc2ead24975e')
                image = client.upload(file=image_url)
                print(image.url)
                data['image'] = image.url

        # load page by url to beautiful soup and get html title
        import requests
        from bs4 import BeautifulSoup
        page = requests.get(url)
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, 'html.parser')
            if soup.title is not None:
                data['title'] = soup.title.string+" "+data['title']
            response_data['full text'] = soup.get_text()
            response_data['full text'] = re.sub(r'\n+', '\n', response_data['full text'])



        response_data['done'] = True
        response_data['url'] = url
        response_data['title'] = data['title']
        response_data['description'] = data['description']
        response_data['image_url'] = data['image']
        response_data['hashed'] = False
        return response_data


class PreviewGenerator:
    def __init__(self):
        self.cache = PreviewCache()
        self.engine = PreviewGeneratorEngine()
        self.name = "PreviewGenerator"

    def get_preview(self, url,use_cache=True):
        url_md5 = hashlib.md5(url.encode('utf-8')).hexdigest()
        if use_cache:
            cached_result = self.cache.diskCache.get(url_md5, default=None)
            if cached_result is not None:
                cached_result['hashed'] = True
                return cached_result
        result = self.engine.get_preview(url)
        if result['done']:
            self.cache.diskCache[url_md5] = result
        return result

    def update_hash_value(self, resalt):
        url_md5 = hashlib.md5(resalt['url'].encode('utf-8')).hexdigest()
        resalt['hashed'] = True
        self.cache.diskCache[url_md5] = resalt
