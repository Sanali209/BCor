import os
import shutil
import uuid
from line_profiler_pycharm import profile
from whoosh import query
from whoosh.fields import Schema, TEXT
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.index import create_in

schema = Schema(text=TEXT(stored=False), id=TEXT(stored=False))

tempindex_path = 'D:\\index'
if not os.path.exists("D:\\index"):
    os.mkdir("D:\\index")
ix = create_in("D:\\index\\", schema, indexname="temp")


class WhooshMatch:
    def __init__(self):
        self._text_id = str(uuid.uuid4())
        self._text = None
        self.qeryparser = QueryParser("text", schema=schema)
        self.searcher = ix.searcher()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if value == self._text:
            return
        self._text_id = str(uuid.uuid4())
        self._text = value
        writer = ix.writer()
        writer.add_document(
            text=value.lower(),
            id=self._text_id
        )
        writer.commit()
    @profile
    def mach(self, strquery) -> bool:
        strquery = strquery.lower() + ' AND id:"' + self._text_id+'"'
        q = self.qeryparser.parse(strquery)
        #alow_id = query.Term("id", self._text_id)
        #q.add_filter(alow_id)
        self.searcher = ix.searcher()
        with self.searcher as searcher:
            results = searcher.search(q)
            if len(results) == 0:
                return False
            else:
                return True


mach = WhooshMatch()


@profile
def matches_subscription(textstr, strquery) -> bool:
    mach.text = textstr
    return mach.mach(strquery)
