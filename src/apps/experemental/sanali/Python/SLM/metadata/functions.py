# use pip install iptcinfo3
# source on git - https://github.com/james-see/iptcinfo3

from iptcinfo3 import IPTCInfo

from PIL import Image
from iptcinfo3 import IPTCInfo



def IPTC_set_keywords(filename, keywords):
    info = IPTCInfo(filename, force=True)
    info['keywords'] = keywords
    info.save()


def IPTC_get_keywords(filename):
    info = IPTCInfo(filename, force=True)
    return info['keywords']

def pil_read_metadata(filename):
    with Image.open(filename) as img:
        info = img.info
    return info


def pil_read_xmp(filename):
    with Image.open(filename) as img:
        meta = img.getxmp()
    return meta

