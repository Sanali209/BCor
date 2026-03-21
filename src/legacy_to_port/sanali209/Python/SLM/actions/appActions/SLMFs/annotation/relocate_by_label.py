import os
import shutil
import time

from sqlmodel import col, select
from tqdm import tqdm

from SLM.appGlue.images.imagesidecard import ImageSideCard, SideCardDB
from SLM.appGlue.images.image_anotation.predHelper import Image_Prediction_Helper

from_path = r"F:\rawimagedb\repository\nsfv repo\drawn"
to_path = r"F:\rawimagedb\repository\nsfv repo\3d"
job_name = "image genres"
label = "3d renderer"


def retry_commit(session):
    try:
        session.commit()
    except Exception as e:
        print(e)
        time.sleep(1)
        retry_commit(session)


query = select(ImageSideCard).where(col(ImageSideCard.image_path).like(from_path + '%'))
result = SideCardDB().session.exec(query).all()
for image in tqdm(result):
    if not os.path.exists(image.image_path):
        continue
    annotation = Image_Prediction_Helper.get_predictions_by_name(image, job_name)
    if annotation is not None:
        labels = [x.label for x in annotation]
        if label in labels:
            path_diff = os.path.relpath(image.image_path, from_path)
            new_path = os.path.join(to_path, path_diff)
            new_dir = os.path.dirname(new_path)
            os.makedirs(new_dir, exist_ok=True)
            shutil.move(image.image_path, new_path)
            image.image_path = new_path
            retry_commit(SideCardDB().session)
            print(f"moved {image.image_path} to {new_path}")
    else:
        print(f"no annotation for {image.image_path}")
