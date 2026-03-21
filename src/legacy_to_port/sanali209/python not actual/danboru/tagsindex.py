from diskcache import Index


from SLM.files_data_cache.imageToLabel import ImageToTextCache
from SLM.appGlue.iotools.pathtools import get_files, PathListTask
from SLM.metadata.MDManager.mdmanager import MDManager
from SLM.multiTreading.multiTreadWorck import MulthitreadWorckManager

files = get_files(r'F:\rawimagedb\repository\nsfv repo\drawn\presort\_by races', ['*.jpg', '*.png'])

path_task = PathListTask(r"D:\data\list_task", "dipdanboru")


def get_list():
    return files


path_task.on_get_list = get_list

tags_dict = Index("tags_dict")


def step(path):
    res = ImageToTextCache.instance().get_by_path(path, "text_DeepDanbury")
    print(res)
    tags = res.split(',')
    metadata = MDManager(path)
    metadata.Read()
    keywords = metadata.Keywords
    metadata.Clear()
    for tag in tags:
        if tag not in tags_dict:
            tags_dict[tag] = 1
        else:
            tags_dict[tag] += 1
    if keywords is not None:
        keywords = []
    keywords.extend([("auto|deepdanboru|" + tag) for tag in tags])
    keywords = list(set(keywords))
    metadata.setXMPKeywords(keywords)
    metadata.Save()
    path_task.remove_path(path)


multitridWorker = MulthitreadWorckManager(step)
multitridWorker.start(path_task.get_list())

path_task.clear()

all = tags_dict.keys()

# save to txt file
with open("tags.txt", "w") as f:
    for tag in all:
        f.write(f"{tag}\n")
