# example of usage of deepface library for face recognition
# git repo:
# https://github.com/
# for install use pip install deepface
import cv2
import numpy as np
from PIL import Image
from deepface import DeepFace

image_path1 = r"F:\rawimagedb\repository\nsfv repo\drawn\asorted drawn images\mix\mix\$R686AZF.jpg"
image_path2 = r"F:\rawimagedb\repository\nsfv repo\drawn\asorted drawn images\mix\mix\$RB6LKM3.jpg"
detectors_backends = ['opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface']

detector_backend = 'retinaface'

model_names = [
    "VGG-Face",
    "Facenet",
    "Facenet512",
    "OpenFace",
    "DeepFace",
    "DeepID",
    "Dlib",
    "ArcFace",
    "SFace",
]

DeepFace.verify(image_path1, image_path2, model_name=model_names[0], detector_backend=detector_backend)

faces_objs = DeepFace.extract_faces(image_path2, detector_backend=detector_backend)
#image2 = DeepFace.detectFace(image_path2)

# draw face with mathplotlib
import matplotlib.pyplot as plt
for face_obj in faces_objs:
    print(face_obj)
    face = face_obj["face"]
    # revert opperations
    face_unnorm = face.copy()
    face_unnorm *= 255
    pil_image = Image.fromarray(face_unnorm.astype(np.uint8))
    pil_image.show()



