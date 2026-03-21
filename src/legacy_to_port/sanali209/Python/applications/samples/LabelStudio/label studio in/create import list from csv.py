# create json import file for label studio and use local data storage

import urllib
from tqdm import tqdm


import json
from transformers import pipeline



import_csv_file_path = r"D:\1.csv"
sourcestore = r"F:\rawimagedb"
labelexportfile = r"F:\rawimagedb\chardetector.json"

predictionenable = False


def get_filepaths_from_csv(csvfilepath, column_namber=0,spliter=';',encoding='utf8'):
    filepaths = []
    with open(csvfilepath, 'r', encoding='utf8') as f:
        lines = f.readlines()
        for line in lines:
            line = line.replace('\n', '')
            columns = line.split(spliter)
            filepaths.append(columns[column_namber])
    return filepaths

if predictionenable:
    predpiplinename = "sanali209/imclasif-quality-v001"
    predprefix = 'prediction|sanali209/imquality'
    predpipline = pipeline('imageView-classification', predpiplinename)

allimages = get_filepaths_from_csv(import_csv_file_path)

labeljsondata = []

# create json file for label studio
counter = 0

for image in tqdm(allimages):
    pathtoimagelabelstudio = image.replace('\\', "/")
    # url encode string
    pathtoimagelabelstudio = urllib.parse.quote(pathtoimagelabelstudio)
    pathtoimagelabelstudio = '/data/local-files/?d=' + pathtoimagelabelstudio

    item = {'id': counter,
            'data': {'image': pathtoimagelabelstudio},
            'annotations': [],
            'predictions': []}
    if predictionenable:
        pred = predpipline(image)
        label = pred[0]['label']
        item['predictions'] = [
            {'result': [{'value': label}]}
        ]

    labeljsondata.append(item)
    counter += 1

# ensure utf8
with open(labelexportfile, 'w', encoding='utf8') as f:
    json.dump(labeljsondata, f, ensure_ascii=False, indent=4)
