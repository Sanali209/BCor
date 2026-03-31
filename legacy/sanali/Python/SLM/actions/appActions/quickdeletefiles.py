"""
This script deletes all images in a specified folder. The folder is specified by the "analizepath" variable.
The folder must be specified as an absolute path, not a relative path. The progress bar shows the progress of the deletion.

Imports:
    os: Provides a way of using operating system dependent functionality.
    tqdm: Instantly makes loops show a smart progress meter.
    get_files from SLM.FuncModule: A function to get all files in a directory.

Variables:
    analizepath: The path to the folder that will be analyzed.
    imagelist: A list of all files in the folder.
    progress: A progress bar showing the progress of the deletion.

Exceptions:
    IsADirectoryError: Raised when expected a file but found a directory.
    Exception: Catches all other exceptions.
"""

import os
from tqdm import tqdm

from SLM.actions import AppAction
from SLM.appGlue.iotools.pathtools import get_files


class AppActionQuickDeleteFiles(AppAction):
    def __init__(self):
        super().__init__(name="quick_file_delete", description="Deletes all files in a folder.")

    def run(self, *args, **kwargs):
        path = args[0]
        files = get_files(path, [r"*"])
        for file in tqdm(files):
            try:
                os.remove(file)
            except IsADirectoryError as ex:
                continue
            except Exception as e:
                print(f"Error deleting file: {e}")
        for root, dirs, files in os.walk(path, topdown=False):
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except Exception as e:
                    print(f"Error deleting directory: {e}")


if __name__ == "__main__":
    AppActionQuickDeleteFiles().run(r"D:\data\ImageDataManager\thumbs")
