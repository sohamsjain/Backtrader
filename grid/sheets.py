from queue import Queue
from threading import Thread
from time import sleep
from typing import Dict

from grid.util import *
from mygoogle.sprint import *

pending, _open, closed = 'pending', 'open', 'closed'
xonetypes = {pending, _open, closed}
FILENAME = 'Xones'


class Sheets(GoogleSprint):

    def __init__(self):
        super().__init__()
        self.spread = self.gs.open(FILENAME)
        self.sheets = AutoOrderedDict()
        self.sheets.pending = self.spread.worksheet(pending.capitalize())
        self.sheets.open = self.spread.worksheet(_open.capitalize())
        self.sheets.closed = self.spread.worksheet(closed.capitalize())
        self.q = Queue()
        self.updater = Thread(target=self.update, daemon=True)
        self.updater.start()

    def update(self):
        while True:
            xone_dfs: Dict[str, pd.DataFrame] = self.q.get()
            while not self.q.empty():
                xone_dfs: Dict[str, pd.DataFrame] = self.q.get()
            assert set(xone_dfs.keys()) == xonetypes
            for xtype, xdf in xone_dfs.items():
                self.sheets[xtype.capitalize()].clear()
                self.update_sheet(self.sheets[xtype.capitalize()], xdf)
            sleep(6)