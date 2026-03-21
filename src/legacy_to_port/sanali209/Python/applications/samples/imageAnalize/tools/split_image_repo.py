# script for spliting repository by 1000 files to directories


import os
from pathlib import Path
from tqdm import tqdm

from SLM.appGlue.iotools.pathtools import get_files

repoPath = r'F:\rawimagedb\repository\safe repo'
indirPath = r'F:\rawimagedb\repository\safe repo\mix'

filelist = get_files(indirPath, ['*.jpg', '*.png', '*.jpeg'])


# get free name directory starts with 0 if exists get next free name
# if not exists muve 1000 files to directory and get next free name and so on
def split_repo():
    counter = 0
    for file in tqdm(filelist):
        if counter % 1000 == 0:
            newdir = os.path.join(repoPath, str(counter))
            if not Path(newdir).exists():
                Path(newdir).mkdir(parents=True, exist_ok=True)
        newfile = os.path.join(newdir, os.path.basename(file))
        muve_file_ifExist(file, newfile)
        counter += 1


split_repo()
