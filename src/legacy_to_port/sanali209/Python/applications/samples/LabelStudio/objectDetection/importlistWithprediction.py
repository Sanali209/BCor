# create json import file for label studio and use local data storage
import os
import urllib

import torch
from tqdm import tqdm

import json
from transformers import  DetrImageProcessor, DetrForObjectDetection

from SLM.files_data_cache.pool import PILPool

import_csv_file_path = r"D:\1.csv"
sourcestore = r"F:\rawimagedb"
labelexportfile = r"F:\rawimagedb\chardetector1.json"
from PIL import Image

predictionenable = True


def get_filepaths_from_csv(csvfilepath, column_namber=0, spliter=';', skip_header=True, encoding='utf8'):
    filepaths = []
    with open(csvfilepath, 'r', encoding='utf8') as f:
        lines = f.readlines()
        firstline = True
        for line in lines:
            if firstline and skip_header:
                firstline = False
                continue
            line = line.replace('\n', '')
            columns = line.split(spliter)
            filepaths.append(columns[column_namber])
    return filepaths


# Convert outputs (bounding boxes and class logits) to COCO API format
score_threshold = 0.5
if predictionenable:
    predpiplinename = "sanali209/DT_face_head_char"
    tprocessor = DetrImageProcessor.from_pretrained(predpiplinename)
    tmodel = DetrForObjectDetection.from_pretrained(predpiplinename)

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
        imageF = PILPool.get_pil_image(image)
        # Prepare the image for inference
        inputs = tprocessor(images=imageF, return_tensors="pt")
        outputs = tmodel(**inputs)
        target_sizes = torch.tensor([imageF.size[::-1]])
        result_all = tprocessor.post_process_object_detection(outputs, target_sizes=target_sizes,
                                                              threshold=score_threshold)
        results = result_all[0]
        resalts = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            box = [round(i, 2) for i in box.tolist()]
            label_value = tmodel.config.id2label[label.item()]
            label_text = f"{label_value} ({round(score.item(), 3)})"
            rel_x = box[0] / imageF.size[0] * 100
            rel_y = box[1] / imageF.size[1] * 100
            rel_width = (box[2] - box[0]) / imageF.size[0] * 100
            rel_height = (box[3] - box[1]) / imageF.size[1] * 100
            resalts.append(
                {
                    "original_width": imageF.size[0],
                    "original_height": imageF.size[1],
                    "image_rotation": 0,
                    "from_name": "label",
                    "to_name": "image",
                    "type": "rectanglelabels",
                    "origin": "manual",
                    'value': {
                        'x': rel_x,
                        'y': rel_y,
                        'width': rel_width,
                        'height': rel_height,
                        'rectanglelabels': [label_value]
                    }
                })

        item['predictions'] = [
            {'result': resalts}
        ]

    labeljsondata.append(item)
    counter += 1

# ensure utf8
with open(labelexportfile, 'w', encoding='utf8') as f:
    json.dump(labeljsondata, f, ensure_ascii=False, indent=4)
