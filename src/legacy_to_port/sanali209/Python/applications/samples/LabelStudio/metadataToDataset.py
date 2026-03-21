# conver label studio json dataset to transformers dataset
import json
import shutil
from pathlib import Path
import datasets
from tqdm import tqdm

from SLM.appGlue.iotools.pathtools import get_files
from SLM.metadata.MDManager.mdmanager import MDManager

imagepathimportroot = r'D:\rawdb\repository'
exportPath = r"G:\My Drive\sketchFilterBinary"

if not Path(exportPath).exists():
    Path(exportPath).mkdir(parents=True, exist_ok=True)

if not Path(exportPath + '\\data').exists():
    Path(exportPath + '\\data').mkdir(parents=True, exist_ok=True)

filelist = get_files(imagepathimportroot, ['*.jpg', '*.png', '*.jpeg'])
key_prefix = 'imdb|sketchbinfilter'
label_map = {}
labels = []
dataset = []

for item in tqdm(filelist):
    imagepath = item
    md = MDManager(imagepath)
    md.Read()
    tags = md.getXMPKeywords()
    if tags is None:
        continue
    tags = [x.lower() for x in tags]

    cur_tags = []
    for tag in tags:
        if tag.startswith(key_prefix):
            cur_tags.append(tag)
    if cur_tags is None:
        continue

    # move to export ProjectSettingsPath +'data'
    newimagepath = imagepath.replace(imagepathimportroot, '')
    newimagepath = exportPath + r'/data' + newimagepath
    # copy imageView file
    Path(newimagepath).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(imagepath, newimagepath)
    newimagepath = newimagepath.replace(exportPath, '')

    label = cur_tags[0]
    if label not in label_map:
        label_map[label] = len(label_map)

    dataset.append({'imageView': newimagepath, 'label': label})

dataset = datasets.Dataset.from_list(dataset)
dataset.labels = label_map
dataset.features['label'].names = list(label_map.keys())
dataset.features['label'].num_classes = len(label_map)

dataset.save_to_disk(exportPath)

print(dataset.info)

item1 = dataset[0]
print(item1)
# get dataset labels

