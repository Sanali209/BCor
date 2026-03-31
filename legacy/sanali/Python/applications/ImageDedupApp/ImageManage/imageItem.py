import uuid


class ImageItem:
    def __init__(self, path="", score=0.0):
        self._id = str(uuid.uuid4())
        self._path = path
        self._score = score
        self._selected = False

    @property
    def id(self):
        return self._id

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        self._score = value

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value


