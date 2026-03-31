# script for quck merge of folders

import os
import shutil
import time

from loguru import logger
from tqdm import tqdm

from Python.SLM.FuncModule import getFolders, get_files

# ProjectSettingsPath to merge folders
inirectory = r"E:\adaulth\_by author\Drawn\Dandon Fuga"


# main function to run the program
def main():
    # get subfolter
    dirs_wizqery = getFolders(inirectory, "\horsecock")

    # iterate through dirs wiz qery and move files to parent folder
    # if file exist in parent folder rename it with adding time stamp and move it to parent folder
    for dir in dirs_wizqery:
        logger.debug("____________________________________________")
        logger.debug(dir)
        # create parent dir varr
        parentdir = os.path.dirname(dir)
        logger.debug(parentdir)
        # get onli files without subdirectories from dir

        files = os.listdir(dir)
        logger.debug(files)
        # iterate through files and move them to parent folder
        for file in files:
            logger.debug(file)
            if os.path.isdir(file):
                logger.debug("is dir")
                continue
            # create file ProjectSettingsPath
            filepath = os.path.join(dir, file)
            # create file ProjectSettingsPath in parent folder
            filepathinparent = os.path.join(parentdir, file)
            # if file exist in parent folder rename it with adding time stamp and move it to parent folder
            if os.path.isfile(filepathinparent):
                # create new file name with time stamp
                newfilename = file + "_" + str(time.time())
                # create new file ProjectSettingsPath with new file name
                newfilepath = os.path.join(parentdir, newfilename)
                # move file to parent folder
                os.rename(filepath, newfilepath)
                logger.debug("file moved to parent folder", newfilepath)
            else:
                # move file to parent folder
                os.rename(filepath, filepathinparent)
                logger.debug("file moved to parent folder", filepathinparent)


# FaindCbrAndSaveToTxt()

# inirectory serch directory recursivli delete folders with names "Pubic Hair version",
# "Steps","Wallpaper" and file contain "lineart" in name
def fainanddel():
    # get subfolter
    dirs_wizqery = getFolders(inirectory, "Futa Cum")
    dirs_wizqery += getFolders(inirectory, "Mr. Tentacle")
    dirs_wizqery += getFolders(inirectory, "Wallpaper")
    dirs_wizqery += getFolders(inirectory, "Magic Mushroom")
    dirs_wizqery += getFolders(inirectory, "Pubes")

    # iterate through dirs wiz qery and delete it
    for dir in dirs_wizqery:
        logger.debug("____________________________________________")
        logger.debug(dir)
        # delete dir and all files contain in it
        shutil.rmtree(dir, ignore_errors=True)

    # get files with name contain "lineart" and delete it
    files_wiz_qery = get_files(inirectory, ["*lineart*"], sub_dirs=True)

    for file in files_wiz_qery:
        logger.debug("____________________________________________")
        logger.debug(file)
        os.remove(file)


fainanddel()
