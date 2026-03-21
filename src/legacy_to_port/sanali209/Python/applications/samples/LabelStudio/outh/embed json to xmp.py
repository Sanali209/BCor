# conver label studio json(json min formant) dataset to xmp metadata
import json

import urllib
from tqdm import tqdm

labelstudiojsonimport = r"F:\rawimagedb\nsfw filter export.json"

label_map = {}
# load label studio dataset with json import
with open(labelstudiojsonimport, 'r', encoding='utf8') as f:
    labelstudiojson = json.load(f)

dataset = []

xmpprefix = 'label studio|nsfw|'



for item in tqdm(labelstudiojson):
    imagepath = item['imageView']
    imagepath = imagepath.replace('/data/local-files/?d=', '')
    # url decode string
    imagepath = urllib.parse.unquote(imagepath)
    try:
        label = item['choice']
        if label not in label_map:
            label_map[label] = len(label_map)
        #md_manager = ExifToolMetadata(imagepath)
        #md_manager.ReplaceOrAddXMPSubject(xmpprefix, [xmpprefix+label])
    except:
        continue
