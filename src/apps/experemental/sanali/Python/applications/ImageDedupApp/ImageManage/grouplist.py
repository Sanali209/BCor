import hashlib
import json
import os
import subprocess

from tqdm import tqdm

from SLM.FuncModule import deleteFile_to_recycle_bin
from SLM.appGlue.iotools.pathtools import move_file_ifExist
from applications.ImageDedupApp.ImageManage.imageGroup import ImageGroup
from applications.ImageDedupApp.ImageManage.imageItem import ImageItem
from applications.ImageDedupApp.ImageManage.jsonconverters import ImageGroupAndImageItemJSONEncoder, \
    ImageGroupAndImageItemJSONDecoder


def faindOrNewGroupByName(groups, grname):
    for group in groups:
        if group.label == grname:
            return group
    newGroup = ImageGroup()
    newGroup.label = grname
    groups.append(newGroup)
    return newGroup


class GroupList:
    saveFileName = "groupList.json"

    def __init__(self):
        self._groups: list[ImageGroup] = []
        self._lastSavedMd5 = ""

    @property
    def groups(self):
        return self._groups

    def GetMd5(self):
        liststr = ""
        for group in self.groups:
            liststr += group.id
            for image in group.items:
                liststr += image.id
            for pr in group.propositions:
                liststr += pr.id
        return hashlib.md5(liststr.encode()).hexdigest()

    def Load(self, path):
        loadPath = os.path.join(path, self.saveFileName)
        if not os.path.exists(loadPath):
            return
        with open(loadPath, 'r') as f:
            data: list[ImageGroup] = json.load(f, cls=ImageGroupAndImageItemJSONDecoder)
            self._groups.clear()
            self._groups.extend(data)
            self._lastSavedMd5 = self.GetMd5()

    def Save(self, path):
        if self._lastSavedMd5 == self.GetMd5():
            return
        savePath = os.path.join(path, self.saveFileName)
        with open(savePath, 'w') as f:
            json.dump(self.groups, f, indent=4, cls=ImageGroupAndImageItemJSONEncoder)
            self._lastSavedMd5 = self.GetMd5()

    def GetSelGroups(self):
        for group in self.groups:
            if group.selected:
                yield group

    def GetSelImages(self):
        for group in self.groups:
            for image in group.items:
                if image.selected:
                    yield image

    def ClearSel(self):
        for group in self.groups:
            group.selected = False
            for image in group.items:
                image.selected = False

    def GroupMoveSelectedUp(self):
        selected = self.GetSelGroups()
        for group in selected:
            index = self.groups.index(group)
            if index > 0:
                self.groups.remove(group)
                self.groups.insert(index - 1, group)

    def GroupMoveSelectedDown(self):
        selected = self.GetSelGroups()
        for group in selected:
            index = self.groups.index(group)
            if index < len(self.groups) - 1:
                self.groups.remove(group)
                self.groups.insert(index + 1, group)

    def GroupMoveSelectedToTop(self):
        selected = self.GetSelGroups()
        for group in selected:
            index = self.groups.index(group)
            if index > 0:
                self.groups.remove(group)
                self.groups.insert(0, group)

    def GroupMoveSelectedToBottom(self):
        selected = self.GetSelGroups()
        for group in selected:
            index = self.groups.index(group)
            if index < len(self.groups) - 1:
                self.groups.remove(group)
                self.groups.append(group)

    def GroupDeleteSelected(self):
        for group in self.groups.copy():
            if group.selected:
                self.groups.remove(group)

    def GroupMergeSelected(self):
        selected = list(self.GetSelGroups())
        if len(selected) < 2:
            return
        first = selected[0]
        selected = selected[1:]
        for group in selected:
            first.Merge(group)
            self.groups.remove(group)
        self.ClearSel()

    def GroupDeleteWithOneoreNullImage(self):
        for group in self.groups.copy():
            if len(group.items) <= 1:
                self.groups.remove(group)

    def GroupRemuveExistedImages(self):
        for group in tqdm(self.groups):
            for image in group.items.copy():
                if not os.path.exists(image.path):
                    group.items.remove(image)

    def ImageMoveToGroup(self, sourceGroup: ImageGroup, targetGroup: ImageGroup):
        for image in sourceGroup.items:
            if image.selected:
                sourceGroup.items.remove(image)
                targetGroup.items.append(image)
                targetGroup.ClearDubs()
        self.ClearSel()

    def ImageGetParentGroup(self, image: ImageItem):
        for group in self.groups:
            if image in group.items:
                return group
        return None

    def ImageMoveSelectedToNewGroup(self):
        selected = list(self.GetSelImages())
        if len(selected) == 0:
            return
        newGroup = ImageGroup()
        for image in selected:
            newGroup.items.append(image)
            self.ImageGetParentGroup(image).items.remove(image)

        newGroup.ClearDubs()
        self.groups.append(newGroup)
        self.ClearSel()

    def ImageMoveSelToFirstSelGroup(self):
        selected = list(self.GetSelImages())
        if len(selected) == 0:
            return
        firstGroup = next(self.GetSelGroups())
        if firstGroup is None:
            return
        for image in selected:
            self.ImageGetParentGroup(image).items.remove(image)
            firstGroup.items.append(image)

        firstGroup.ClearDubs()
        self.ClearSel()

    def ImageRemoveSelectedFromGroups(self):
        for group in self.groups:
            for image in group.items.copy():
                if image.selected:
                    group.items.remove(image)
        self.ClearSel()

    def ImageDeleteSelectedFromHdd(self):
        selectedimages = list(self.GetSelImages())
        selectedpats = set()
        for image in selectedimages:
            selectedpats.add(image.path)
        for group in self.groups:
            for image in group.items.copy():
                if image.path in selectedpats:
                    group.items.remove(image)
        for image in selectedimages:
            deleteFile_to_recycle_bin(image.path)
        self.ClearSel()

    def ImageOpenSelectedInExplorer(self):
        selectedimages = list(self.GetSelImages())
        first = selectedimages[0]
        # locate imageView in internet explorer
        subprocess.Popen(r'explorer /select,"' + first.path + '"')

    def ImageSelectAll(self):
        for group in self.groups:
            for image in group.items:
                image.selected = True

    def RemoveFromOthers(self, imageGroup: ImageGroup):
        items = imageGroup.items
        items = [item.path for item in items]
        for group in self.groups:
            if group is not imageGroup:
                for item in group.items.copy():
                    if item.path in items:
                        group.items.remove(item)

    def AddSimilar(self, dubf):
        selected = list(self.GetSelGroups())
        if len(selected) == 0:
            return
        for group in selected:
            group.CreatePropositions(dubf)
            for pr in group.propositions:
                group.AddPropositionItem(pr)

    def AddSimilar2(self, dubf):
        selected_images = list(self.GetSelImages())
        group_of_first_selected = self.ImageGetParentGroup(selected_images[0])
        sel_paths = [image.path for image in selected_images]
        ans = dubf.FindTopSimilarForList(sel_paths, 5)
        # delete dublikates
        existed_paths = [image.path for image in group_of_first_selected.items]
        ans = [path for path in ans if path not in existed_paths]
        for image_path in ans:
            image = ImageItem(image_path, 0.0)
            group_of_first_selected.items.append(image)

    def GroupSelMuveToFolder(self, folder=""):
        """
        Move all items from groups to folders with group name.

        todo: posibility for set behavorior of DubGroupsToFolders
        """
        allgroups = self.groups

        for Group in allgroups:
            Group: ImageGroup
            if not Group.selected:
                continue
            if len(Group.items) > 1:
                GropName = Group.label
                # if GropName contain extension on end remove it
                GropName, ext = os.path.splitext(GropName)
                if folder == "":
                    if len(Group.items) == 0:
                        continue
                    folder = os.path.dirname(Group.items[0].path)
                GropFoldername = os.path.join(folder, GropName)

                for item in Group.items:
                    # get filename with extension
                    filename = os.path.basename(item.path)
                    newpath = os.path.join(GropFoldername, filename)
                    if newpath == item.path:
                        continue
                    if not os.path.exists(GropFoldername):
                        os.makedirs(GropFoldername)
                    # todo:review logic of used function move_file_ifExist
                    # fixme: logic of item movement if the item in multiple groups
                    move_file_ifExist(item.path, newpath)
                    item.path = newpath
        # clear selected groups
        self.ClearSel()

    def ImageMoveSelToNamedGroup(self, grname):
        selected = list(self.GetSelImages())
        if len(selected) == 0:
            return
        group = faindOrNewGroupByName(self.groups, grname)

        for image in selected:
            group.items.append(image)
            self.ImageGetParentGroup(image).items.remove(image)

        group.ClearDubs()

        self.ClearSel()

    def AddImageToSelGroup(self, image_path: str):
        selected = list(self.GetSelGroups())
        if len(selected) == 0:
            return
        group = selected[0]
        image = ImageItem(image_path, 0.0)
        group.items.append(image)
        group.ClearDubs()
        self.ClearSel()
