from diskcache import Index
from tqdm import tqdm

from SLM.appGlue.iotools.pathtools import get_files
from SLM.metadata.MDManager.mdmanager import MDManager


def clear_metadata(images_path):
    index = Index("D:/data/ImageDataManager/index")
    if len(index) == 0:
        files = get_files(images_path, ['*.jpg', '*.png'])
        for file in files:
            index[file] = True
    metamanager = MDManager(None)
    for file in tqdm(index.keys().copy()):

        metamanager.backend.del_tag(file, "all")
        index.pop(file)


if __name__ == '__main__':
    clear_metadata(r'X:\rawdb')
