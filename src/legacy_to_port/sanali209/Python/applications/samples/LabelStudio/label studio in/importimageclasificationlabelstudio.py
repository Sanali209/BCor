# create json import file for label studio and use local data storage
import os
import urllib
from tqdm import tqdm


import json
from transformers import pipeline

from SLM.appGlue.iotools.pathtools import get_files
from SLM.metadata.MDManager.mdmanager import MDManager


importdir = r"F:\rawimagedb\repository\safe repo\presort"
sourcestore = r"F:\rawimagedb"
labelexportfile = r"F:\rawimagedb\face.json"
labelexportpath = os.path.join(importdir, labelexportfile)

predictionenable = False
xmppredsave = False
predpiplinename = "sanali209/imclasif-quality-v001"
predprefix='prediction|sanali209/imquality'
predpipline = pipeline('imageView-classification', predpiplinename)

allimages = get_files(importdir, ['*.jpg', '*.png', '*.jpeg'])

labeljsondata = []

# create json file for label studio
counter = 0
for image in tqdm(allimages):
    pathtoimagelabelstudio = image.replace('\\', "/")
    # url encode string
    pathtoimagelabelstudio = urllib.parse.quote(pathtoimagelabelstudio)
    pathtoimagelabelstudio = '/data/local-files/?d=' + pathtoimagelabelstudio

    if predictionenable:
        pred = predpipline(image)
        label = pred[0]['label']
        if xmppredsave:
            tags = [predprefix + "|" + label]
            mdm = MDManager(image)
            mdm.Read()
            ntags = mdm.Keywords
            mdm.Clear()
            if ntags is None or ntags == "":
                ntags = []
            ntags.extend(tags)
            tags = list(dict.fromkeys(ntags))
            mdm.Keywords = tags
            mdm.Save()
        item = {'id': counter,
                'data': {'imageView': pathtoimagelabelstudio},
                'annotations': [],
                'predictions': [
                    {'result': [{'value': label}]}
                ]}
    else:
        item = {'id': counter,
                'data': {'imageView': pathtoimagelabelstudio},
                'annotations': [],
                'predictions': []}
    labeljsondata.append(item)
    counter += 1

# ensure utf8
with open(labelexportpath, 'w', encoding='utf8') as f:
    json.dump(labeljsondata, f, ensure_ascii=False, indent=4)
