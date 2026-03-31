from diskcache import Index

from SLM.appGlue.iotools.pathtools import get_files, PathListTask
from SLM.multiTreading.multiTreadWorck import MulthitreadWorckManager

files_path = r'F:\rawimagedb\repository\nsfw onli db'

task = PathListTask(r"D:\data\all_im_task", "files_task")


def get_list():
    return get_files(files_path, ['*.jpg', '*.png'])


tags = Index(r'D:\data\alltags')

task.on_get_list = get_list


def get_tags_for_file(file_path):
    from SLM.metadata.MDManager.mdmanager import MDManager
    manager = MDManager(file_path)
    manager.Read()
    exif_tags = manager.metadata.get('EXIF:XPKeywords', [])
    exif_tags_subj = manager.metadata.get('EXIF:XPSubject', [])
    if isinstance(exif_tags_subj, str):
        exif_tags_subj = exif_tags_subj.split(",")
    xmp_tags = manager.metadata.get('XMP:Subject', [])
    if isinstance(exif_tags, str):
        exif_tags = exif_tags.split(",")
    if isinstance(xmp_tags, str):
        xmp_tags = xmp_tags.split(",")
    xmp_tags.extend(exif_tags)
    xmp_tags.extend(exif_tags_subj)
    xmp_tags = list(set(xmp_tags))
    tags[file_path] = xmp_tags
    task.remove_path(file_path)


multitridWorker = MulthitreadWorckManager(get_tags_for_file)
multitridWorker.start(task.get_list())

task.clear()

def build_tag_list_txt(save_path):
    tags = Index(r'D:\data\alltags')
    tags_list = []
    for key in tags.keys():
        tags_list.extend(tags[key])
    tags_list = list(set(tags_list))
    tags_list.sort()
    with open(save_path, "w",encoding="utf-8") as file:
        for tag in tags_list:
            file.write(tag + "\n")
    return tags_list

build_tag_list_txt(r"D:\data\alltags.txt")

