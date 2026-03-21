import json

from applications.ImageDedupApp.ImageManage.imageGroup import ImageGroup
from applications.ImageDedupApp.ImageManage.imageItem import ImageItem


class ImageGroupAndImageItemJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ImageGroup):
            od = o.__dict__
            od['__class__'] = 'ImageGroup'
            return od

        if isinstance(o, ImageItem):
            od = o.__dict__
            od['__class__'] = 'ImageItem'
            # convert source_property score to string
            if '_score' in od and od['_score'] is not None:
                od['_score'] = str(od['_score'])
            return od

        return json.JSONEncoder.default(self, o)


class ImageGroupAndImageItemJSONDecoder(json.JSONDecoder):
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dict_to_object)

    def dict_to_object(self, d):
        if '__class__' in d:
            class_name = d.pop('__class__')
            if class_name == 'ImageGroup':
                inst = ImageGroup()
            elif class_name == 'ImageItem':
                inst = ImageItem()

                # parse score
                if '_score' in d and d['_score'] is not None:
                    try:
                        d['_score'] = float(d['_score'])
                    except:
                        d['_score'] = 0.0
            else:
                inst = d
            for key, value in d.items():
                setattr(inst, key, value)
        else:
            inst = d
        return inst
