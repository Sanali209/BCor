"""
converse label studio json dataset to transformers dataset sample
"""
import json
import shutil
import urllib
from pathlib import Path
import datasets
from tqdm import tqdm

imagepathimportroot = r'F:/rawimagedb/repository'
exportPath = r"F:/rawimagedb/export/quality"


if not Path(exportPath).exists():
    Path(exportPath).mkdir(parents=True, exist_ok=True)

if not Path(exportPath+'\\data').exists():
    Path(exportPath+'\\data').mkdir(parents=True, exist_ok=True)

labelstudiojsonimport = r"F:\rawimagedb\project-6-at-2023-05-14-01-50-1199bd68.json"
label_map = {}
# load label studio dataset with json import
with open(labelstudiojsonimport, 'r', encoding='utf8') as f:
    labelstudiojson = json.load(f)

dataset = []

for item in tqdm(labelstudiojson):
    imagepath = item['imageView']
    imagepath  = imagepath.replace('/data/local-files/?d=', '')
    # url decode string
    imagepath = urllib.parse.unquote(imagepath)

    # move to export ProjectSettingsPath +'data'
    newimagepath =  imagepath.replace(imagepathimportroot, '')
    newimagepath = exportPath+r'/data' + newimagepath
    # copy imageView file
    Path(newimagepath).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(imagepath, newimagepath)
    newimagepath = newimagepath.replace(exportPath, '')


    label = item['choice']
    if label not in label_map:
        label_map[label] = len(label_map)

    dataset.append({'imageView': newimagepath, 'label': label})

dataset = datasets.Dataset.from_list(dataset)
dataset.labels = label_map
dataset.features['label'].names = list(label_map.keys())
dataset.features['label'].num_classes = len(label_map)



dataset.save_to_disk(exportPath)


