# read csv file with file pats and tags
# use https://colab.research.google.com/drive/1m31E0CSLDjkE_i038LAJj0sWHOJx9Ld6#scrollTo=ABreTsYRoDzy
# for train imageView classification model
import os
import shutil

import pandas as pd
from tqdm import tqdm


from SLM.appGlue.iotools.csvHelper import get_filepaths_from_csv, get_filepaths_tags_from_csv
from SLM.appGlue.iotools.pathtools import copy_file_ifExist

csv_path = r"D:\reitfilter.csv"
all_results = get_filepaths_tags_from_csv(csv_path)
target_folder = r"G:\My Drive\rawdb\reitfilter"
tagprefix = 'manual\\reitfilter\\'

maximum_per_tag_category = 2300

if os.path.exists(target_folder):
    print("folder {} exist".format(target_folder))
    # delete folder
    shutil.rmtree(target_folder)

os.makedirs(target_folder)

# create pandas dataframe
cdf = pd.DataFrame(all_results, columns=['path', 'tags'])

tagcount = {}

# iterate over each item in dataframe
for index, row in tqdm(cdf.iterrows(), total=cdf.shape[0]):
    tag = row['tags']
    tag = [t.strip() for t in tag.split(',') if t.strip().startswith(tagprefix)]
    if len(tag) == 0:
        continue
    tag = tag[0]
    if tag[0] == '\\':
        tag = tag[1:]
    tagcount[tag] = tagcount.get(tag, 0) + 1
    if tagcount[tag] > maximum_per_tag_category:
        continue

    ftFolder = os.path.join(target_folder, tag.strip().replace(tagprefix, ''))
    if not os.path.exists(ftFolder):
        os.makedirs(ftFolder)
    target_path = os.path.join(ftFolder, os.path.basename(row['path']))
    try:
        copy_file_ifExist(row['path'], target_path)
    except:
        print("error copy file {}".format(row['path']))
