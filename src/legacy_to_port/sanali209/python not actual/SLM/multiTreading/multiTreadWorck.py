import multiprocessing
from multiprocessing.pool import ThreadPool as Pool

from tqdm import tqdm


class MulthitreadWorckManager:
    def __init__(self, call_back):
        super().__init__()
        self.treads = multiprocessing.cpu_count() - 1
        self.resalts = None
        self.call_back = call_back
        self.pbar = None

    def wrap(self, *args):
        self.pbar.update(1)
        return self.call_back(*args)

    def start(self, args:list):

        pool = Pool(processes=self.treads)
        self.pbar = tqdm(total=len(args))
        self.resalts = pool.map(self.wrap, args)
        pool.close()
        pool.join()

    def start_sinc(self, args:list):
        for arg in tqdm(args, total=len(args)):
            self.call_back(arg)
