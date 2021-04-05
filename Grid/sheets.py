from queue import Queue
from threading import Thread
from time import sleep

from Grid.xone import Xone
from mygoogle.sprint import *

FILENAME = 'Xones'


class Sheets(GoogleSprint):

    def __init__(self):
        super().__init__()
        self.spread = self.gs.open(FILENAME)
        self.pxl = self.spread.worksheet('Pending')
        self.oxl = self.spread.worksheet('Open')
        self.cxl = self.spread.worksheet('Closed')
        self.pxones = self.fetch_sheet_values(self.pxl).to_dict(orient='records')
        self.oxones = self.fetch_sheet_values(self.oxl).to_dict(orient='records')
        self.cxones = self.fetch_sheet_values(self.cxl).to_dict(orient='records')
        self.queue = Queue()
        self.updater = Thread(target=self.update_xones, daemon=True).start()

    def update_xones(self):
        while True:
            xone_dicts = self.queue.get()
            while not self.queue.empty():
                xone_dicts = self.queue.get()
            p, o, c = xone_dicts['p'], xone_dicts['o'], xone_dicts['c']
            if p:
                self.pxl.clear()
                self.update_sheet(self.pxl, pd.DataFrame([x.getvalues() for s, x in p.items()], columns=Xone.attrs))
            if o:
                self.oxl.clear()
                self.update_sheet(self.oxl, pd.DataFrame([x.getvalues() for s, x in o.items()], columns=Xone.attrs))
            if c:
                self.cxl.clear()
                self.update_sheet(self.cxl, pd.DataFrame([x.getvalues() for s, x in c.items()], columns=Xone.attrs))
            sleep(6)
