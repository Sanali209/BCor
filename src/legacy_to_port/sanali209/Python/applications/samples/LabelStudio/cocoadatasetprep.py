# script for postproces dataset exported from label studio as cocoa dataset
import json
import os

from datasets import load_dataset

datasetpath = r'G:\My Drive\rawdb\face_head_char\result.json'

# load with json import
datasettext = ''

with open(datasetpath, 'r', encoding='utf8') as f:
    datasettext = f.read()

datasettext = datasettext.replace(r'\/', '/')

jsondata = json.loads(datasettext)

for item in jsondata['images']:
    filename = item['file_name']
    filename = os.path.basename(filename)
    item['file_name'] = filename

# save as utf8
with open(datasetpath, 'w', encoding='utf8') as f:
    json.dump(jsondata, f, ensure_ascii=False, indent=4)
