import os

from tqdm import tqdm

from SLM.appGlue.iotools.pathtools import get_files
from SLM.metadata.MDManager.mdmanager import MDManager
from SLM.vision.imagetotext.ImageCaptioners.ImageCaptioners import DeepDanboruImageCaptioner

worckdir_path = r"F:\rawimagedb\repository\safe repo\presort\the witcher"

seek_count = 0
counter = 0

all_imagesPats = get_files(worckdir_path, ['*.jpg', '*.png', '*.jpeg', '*.bmp', '*.gif'])

DeepDanboruImageCaptioner_s = DeepDanboruImageCaptioner()

for image_path in tqdm(all_imagesPats):
    if counter < seek_count:
        counter += 1
        continue

    XmpReader = MDManager(image_path)
    XmpReader.Read()
    tags = XmpReader.Keywords
    if tags is None:
        tags = []
    # if tagscontain prefix "deepdanboru|" skeep tagging
    if any("deepdanboru|" in tag for tag in tags):
        continue
    result = DeepDanboruImageCaptioner_s.get_caption(image_path)
    result_tags = ["deepdanboru|" + tag for tag in result.split(",")]
    # get file xmp data


    # add tags
    tags.extend(result_tags)
    # remove duplicates
    tags = list(dict.fromkeys(tags))
    XmpReader.Clear()
    XmpReader.Keywords = tags
    XmpReader.Save()
