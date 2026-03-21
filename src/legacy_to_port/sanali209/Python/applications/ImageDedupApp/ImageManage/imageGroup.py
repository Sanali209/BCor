import uuid
from enum import Enum

from applications.ImageDedupApp.ImageManage.imageItem import ImageItem


class ImageGroupTypes(Enum):
    FolderItems = "Folder Items"
    CustomGroup = "Custom Group"
    SimilarItems = "Similar Items"


class ImageGroup:
    def __init__(self):
        super().__init__()
        uid = str(uuid.uuid4())
        self._type: str = str(ImageGroupTypes.FolderItems)
        self._id = uid  # type: str
        self._selected = False  # type: bool
        self._label = uid  # type: str
        self._items = []  # type: list[ImageItem]
        self._expanded = True
        self._propositions = []  # type: list[ImageItem]
        self.processoption:str = None
        self.processArgs:str = None
        self.showProposals:bool = False

    def CreatePropositions(self, dupfaindhelper):
        for item in self.items:
            similar = dupfaindhelper.FindTopSimilar(item.path, 6)
            similar = similar[1:]
            self.propositions.extend([ImageItem(sim) for sim in similar if sim not in self.itemPats()])
        # clear duplicates
        copy = self.propositions.copy()
        self.propositions.clear()
        copy = {item.path: item for item in copy}
        self.propositions.extend(copy.values())



    def itemPats(self) -> list[str]:
        return [item.path for item in self.items]

    @property
    def propositions(self) -> list[ImageItem]:
        return self._propositions

    @propositions.setter
    def propositions(self, value):
        self._propositions = value

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def items(self) -> list[ImageItem]:
        return self._items

    @items.setter
    def items(self, value):
        self._items = value

    @property
    def expanded(self):
        return self._expanded

    @expanded.setter
    def expanded(self, value):
        self._expanded = value

    def ClearDubs(self):
        copy = {item.path: item for item in self.items}
        self.items.clear()
        self.items.extend(copy.values())

    def AddPropositionItem(self, item: ImageItem):
        self.items.append(item)
        self._propositions.remove(item)

    def Merge(self, group):
        self.items.extend(group.items)
        self.propositions.extend(group.propositions)
        self.ClearDubs()

    def GetSelImages(self):
        return [item for item in self.items if item.selected]





