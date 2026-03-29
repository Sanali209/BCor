import os



from diskcache import  Index

from SLM.appGlue.iotools.pathtools import get_files, PathListTask, move_file_ifExist
from SLM.multiTreading.multiTreadWorck import MulthitreadWorckManager

# todo refactor this

files_path = r'F:\rawimagedb\repository\safe repo\presort\3d'

task = PathListTask(r"F:\data\list_task", "aiRename")


def get_list():
    return get_files(files_path, ['*.jpg', '*.png'])


tags = Index(r'D:\data\alltags')

task.on_get_list = get_list


def get_tags_for_file(file_path):

    rename_data = get_image_GPT_data(file_path)
    if rename_data is None:
        task.remove_path(file_path)
        return



    file_parenth_path, file_name = os.path.split(file_path)
    file_parenth_path = os.path.join(file_parenth_path, "gptrename")
    if not os.path.exists(file_parenth_path):
        os.mkdir(file_parenth_path)
    new_name = rename_data['name']
    new_name_withouth_extension, extension = os.path.splitext(new_name)
    old_name_withouth_extension, extension = os.path.splitext(file_name)
    move_file_ifExist(file_path, os.path.join(file_parenth_path, new_name_withouth_extension + extension))
    task.remove_path(file_path)


multitridWorker = MulthitreadWorckManager(get_tags_for_file)
multitridWorker.start_sinc(task.get_list())

task.clear()
