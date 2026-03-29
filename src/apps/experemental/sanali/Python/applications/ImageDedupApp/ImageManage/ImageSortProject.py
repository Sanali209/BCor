import os

from diskcache import Cache
from tqdm import tqdm
from transformers import pipeline


from SLM.appGlue.DesignPaterns.MessageSystem import MessageSystem
from SLM.appGlue.DesignPaterns.SingletonAtr import singleton
from SLM.appGlue.iotools.pathtools import get_files
from SLM.fileTumbHash.filetumbhash import FileTumbHash
from SLM.vision.dubFileHelper import DuplicateFindHelper
from applications.ImageDedupApp.ImageManage.grouplist import GroupList
from applications.ImageDedupApp.ImageManage.imageGroup import ImageGroup
from applications.ImageDedupApp.ImageManage.imageItem import ImageItem


@singleton
class ImageSortProject:
    def __init__(self):
        self._ProjectSettingsPath = r'F:\rawimagedb\repository\nsfv repo\drawn\drawn xxx autors\Palcomix'
        self.WorckPath = r'E:\rawimagedb\repository\nsfv repo\drawn\_site rip\Alazarsart.com'
        self.hashPath = "data/hash"
        self.worckDirPath = "data/worckDir"
        self.fileThumbHash = FileTumbHash()
        self.dublicateFinder = DuplicateFindHelper()
        self.imageGroups = GroupList()
        self._dubsThreshold = 0.95
        self.dubsTresholdWeak = 0.99
        self.prCache = Cache("D:\data\ImSortPrCache")
        self._tresholdMin = 0.9
        self._tresholdMax = 1.0



    # source_property ProjectSettingsPath
    @property
    def ProjectSettingsPath(self):
        return self._ProjectSettingsPath

    def CacheNNFilterValue(self, filtername, values):
        self.prCache['nnf' + filtername] = values

    def GetCacheNNFilterValue(self, filtername):
        return self.prCache.get('nnf' + filtername, default=[])

    @ProjectSettingsPath.setter
    def ProjectSettingsPath(self, value):
        if self._ProjectSettingsPath == value:
            return
        self._ProjectSettingsPath = value
        MessageSystem.SendMessage("ImageSortProjectPropChanged", propname="ProjectSettingsPath", value=value)

    # source_property dubTreshold
    @property
    def dubsThreshold(self):
        return self._dubsThreshold

    @dubsThreshold.setter
    def dubsThreshold(self, value):
        if self._dubsThreshold == value:
            return
        self._dubsThreshold = value
        MessageSystem.SendMessage("ImageSortProjectPropChanged", propname="dubsThreshold", value=value)

    def CreateDubList(self):
        listOfFiles: list[str] = get_files(self.WorckPath, exts=['*.jpg', '*.png', '*.jpeg'])

        self.dublicateFinder.RefreshIndex(listOfFiles)
        scoreEnable = False
        find_duplicates_cnn = self.dublicateFinder.FaindCNNDubs(self.dublicateFinder.futuresMap,
                                                                similarity=self.dubsThreshold, score=scoreEnable)

        self.dublicateFinder.ClearEmptyDubsGroup(find_duplicates_cnn)
        while True:
            removed = self.dublicateFinder.ClearFullCollidedDubsGroup(find_duplicates_cnn, score=False)
            if removed[0] == 0:
                break

        self.dublicateFinder.HidePairs(find_duplicates_cnn, self.prCache.get('hidenpairs', default=[]))

        find_duplicates_cnn_list = []

        for key, value in find_duplicates_cnn.items():
            grop = ImageGroup()
            grop.label = os.path.basename(key)

            grop.items.append(ImageItem(key, 0.0))

            for i in value:
                if scoreEnable:
                    itemPath = i[0]
                    itemSimilarity = i[1]
                else:
                    itemPath = i
                    itemSimilarity = 0.0
                grop.items.append(ImageItem(itemPath, itemSimilarity))
            find_duplicates_cnn_list.append(grop)

        self.imageGroups.groups.clear()
        self.imageGroups.groups.extend(find_duplicates_cnn_list)
        self.SolveCollision_FolderAsImageSet()
        self.imageGroups.GroupDeleteWithOneoreNullImage()
        self.SortBySourceFolder(self.imageGroups.groups)

    def CreateDubListByFaces(self):
        pass

    def SortBySourceFolder(self, groups):
        sortedGroups = sorted(groups, key=lambda x: x.items[0].path)
        groups.clear()
        groups.extend(sortedGroups)

    def CreateAdvisionList(self):
        listOfFiles: list[str] = get_files(self.WorckPath, exts=['*.jpg', '*.png', '*.jpeg'])

        self.dublicateFinder.RefreshIndex(listOfFiles)
        advision_list = []

        for filepath in tqdm(listOfFiles):

            group = ImageGroup()
            group.label = os.path.basename(filepath)
            group.items.append(ImageItem(filepath, 0.0))
            sim = self.dublicateFinder.FindTopSimilar(filepath, 6)
            sim = sim[1:]
            group.items.extend([ImageItem(simi) for simi in sim])
            advision_list.append(group)

        self.imageGroups.groups.clear()
        self.imageGroups.groups.extend(advision_list)

    def Save(self):
        self.imageGroups.Save(self.ProjectSettingsPath)

    def Load(self):
        self.imageGroups.Load(self.ProjectSettingsPath)
        self.dublicateFinder.RefreshIndeksDir(self.WorckPath)

    def AddHideItemPair(self, key: str, hiden: str):
        hidenpairs = self.prCache.get('hidenpairs', default=[])
        if (key, hiden) not in hidenpairs:
            hidenpairs.append((key, hiden))
        self.prCache['hidenpairs'] = hidenpairs

    def AddHideItemAll(self):

        for group in ImageSortProject().imageGroups.groups.copy():
            # get selected images
            items = group.items
            if len(items) < 2:
                continue
            # get key imageView
            key = items[0]
            # iterate trout all selected images
            for item in items[1:]:
                # add hiden pair
                ImageSortProject().AddHideItemPair(key.ProjectSettingsPath, item.ProjectSettingsPath)
            ImageSortProject().imageGroups.groups.remove(group)

    # todo:move to app document
    def AddFolderAsImageSet(self, path):
        imagesetsList = self.prCache.get('imagesets', default=[])
        if path not in imagesetsList:
            imagesetsList.append(path)
        self.prCache['imagesets'] = imagesetsList

    def HidePairs(self, pairs: list[tuple[str, str]]):
        progress = tqdm(self.imageGroups.groups)
        for group in progress:
            for pair in pairs:
                if len(group.items) < 2:
                    continue
                if pair[0] == group.items[0].path:
                    for item in group.items[1:]:
                        # scored end not scored
                        if item == pair[1]:
                            group.items.remove(item)
                            break

    def SolveCollision_FolderAsImageSet(self):
        self.HidePairs(self.prCache.get('hidenpairs', default=[]))
        imagesetsList = self.prCache.get('imagesets', default=[])
        collisions = []
        for path in imagesetsList:
            # iterate over groups
            for group in self.imageGroups.groups:
                # iterate over items
                for item in group.items:
                    if item.path.startswith(path):
                        # solve in group collision
                        # create pair from all items in group
                        for item2 in group.items:
                            if item2.path != item.path:
                                if item2.path.startswith(path):
                                    collisions.append(item)
                group.items = [x for x in group.items if x not in collisions]

    def CreateListByNeiroFilter(self, paiplainname):
        pipline = pipeline(model=paiplainname)
        imagelist = get_files(self.WorckPath, [r"*.jpg", r"*.png"])
        progress = tqdm(imagelist)
        groups = {}
        for imagepath in progress:
            tags = pipline(imagepath)[0]['label']
            if tags not in groups:
                groups[tags] = ImageGroup()
                groups[tags].label = tags
            groups[tags].items.append(ImageItem(imagepath, 0.0))
        self.imageGroups.groups.clear()
        self.imageGroups.groups.extend(groups.values())

@singleton
class ImageSortProject2:
    def __init__(self):
        self.WorckPath = r'F:\rawimagedb\repository\nsfv repo\drawn'
        self.dublicateFinder = DuplicateFindHelper()
        self.imageGroups = GroupList()
        self._dubsThreshold = 0.93


    def CacheNNFilterValue(self, filtername, values):
        self.prCache['nnf' + filtername] = values

    def GetCacheNNFilterValue(self, filtername):
        return self.prCache.get('nnf' + filtername, default=[])

    def create_cnn_index(self):
        pass

    def CreateDubList(self):
        listOfFiles: list[str] = get_files(self.WorckPath, exts=['*.jpg', '*.png', '*.jpeg'])

        self.dublicateFinder.RefreshIndex(listOfFiles)
        scoreEnable = False
        find_duplicates_cnn = self.dublicateFinder.FaindCNNDubs(self.dublicateFinder.futuresMap,
                                                                similarity=self.dubsThreshold, score=scoreEnable)

        self.dublicateFinder.ClearEmptyDubsGroup(find_duplicates_cnn)
        while True:
            removed = self.dublicateFinder.ClearFullCollidedDubsGroup(find_duplicates_cnn, score=False)
            if removed[0] == 0:
                break

        self.dublicateFinder.HidePairs(find_duplicates_cnn, self.prCache.get('hidenpairs', default=[]))

        find_duplicates_cnn_list = []

        for key, value in find_duplicates_cnn.items():
            grop = ImageGroup()
            grop.label = os.path.basename(key)

            grop.items.append(ImageItem(key, 0.0))

            for i in value:
                if scoreEnable:
                    itemPath = i[0]
                    itemSimilarity = i[1]
                else:
                    itemPath = i
                    itemSimilarity = 0.0
                grop.items.append(ImageItem(itemPath, itemSimilarity))
            find_duplicates_cnn_list.append(grop)

        self.imageGroups.groups.clear()
        self.imageGroups.groups.extend(find_duplicates_cnn_list)
        self.SolveCollision_FolderAsImageSet()
        self.imageGroups.GroupDeleteWithOneoreNullImage()
        self.SortBySourceFolder(self.imageGroups.groups)


    def SortBySourceFolder(self, groups):
        sortedGroups = sorted(groups, key=lambda x: x.items[0].path)
        groups.clear()
        groups.extend(sortedGroups)

    def CreateAdvisionList(self):
        listOfFiles: list[str] = get_files(self.WorckPath, exts=['*.jpg', '*.png', '*.jpeg'])

        self.dublicateFinder.RefreshIndex(listOfFiles)
        advision_list = []

        for filepath in tqdm(listOfFiles):

            group = ImageGroup()
            group.label = os.path.basename(filepath)
            group.items.append(ImageItem(filepath, 0.0))
            sim = self.dublicateFinder.FindTopSimilar(filepath, 6)
            sim = sim[1:]
            group.items.extend([ImageItem(simi) for simi in sim])
            advision_list.append(group)

        self.imageGroups.groups.clear()
        self.imageGroups.groups.extend(advision_list)

    def AddHideItemPair(self, key: str, hiden: str):
        hidenpairs = self.prCache.get('hidenpairs', default=[])
        if (key, hiden) not in hidenpairs:
            hidenpairs.append((key, hiden))
        self.prCache['hidenpairs'] = hidenpairs

    def AddHideItemAll(self):

        for group in ImageSortProject().imageGroups.groups.copy():
            # get selected images
            items = group.items
            if len(items) < 2:
                continue
            # get key imageView
            key = items[0]
            # iterate trout all selected images
            for item in items[1:]:
                # add hiden pair
                ImageSortProject().AddHideItemPair(key.ProjectSettingsPath, item.ProjectSettingsPath)
            ImageSortProject().imageGroups.groups.remove(group)

    # todo:move to app document
    def AddFolderAsImageSet(self, path):
        imagesetsList = self.prCache.get('imagesets', default=[])
        if path not in imagesetsList:
            imagesetsList.append(path)
        self.prCache['imagesets'] = imagesetsList

    def HidePairs(self, pairs: list[tuple[str, str]]):
        progress = tqdm(self.imageGroups.groups)
        for group in progress:
            for pair in pairs:
                if len(group.items) < 2:
                    continue
                if pair[0] == group.items[0].path:
                    for item in group.items[1:]:
                        # scored end not scored
                        if item == pair[1]:
                            group.items.remove(item)
                            break

    def SolveCollision_FolderAsImageSet(self):
        self.HidePairs(self.prCache.get('hidenpairs', default=[]))
        imagesetsList = self.prCache.get('imagesets', default=[])
        collisions = []
        for path in imagesetsList:
            # iterate over groups
            for group in self.imageGroups.groups:
                # iterate over items
                for item in group.items:
                    if item.path.startswith(path):
                        # solve in group collision
                        # create pair from all items in group
                        for item2 in group.items:
                            if item2.path != item.path:
                                if item2.path.startswith(path):
                                    collisions.append(item)
                group.items = [x for x in group.items if x not in collisions]

    def CreateListByNeiroFilter(self, paiplainname):
        pipline = pipeline(model=paiplainname)
        imagelist = get_files(self.WorckPath, [r"*.jpg", r"*.png"])
        progress = tqdm(imagelist)
        groups = {}
        for imagepath in progress:
            tags = pipline(imagepath)[0]['label']
            if tags not in groups:
                groups[tags] = ImageGroup()
                groups[tags].label = tags
            groups[tags].items.append(ImageItem(imagepath, 0.0))
        self.imageGroups.groups.clear()
        self.imageGroups.groups.extend(groups.values())

