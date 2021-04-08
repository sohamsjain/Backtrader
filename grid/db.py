from queue import Queue
from threading import Thread
from time import sleep
from typing import List, Dict

import pandas as pd
from sqlalchemy import create_engine

from grid.util import *
from grid.xone import Xone
from mygoogle.sprint import GoogleSprint

pending, _open, closed = 'pending', 'open', 'closed'

FILENAME = 'Xones'

ListOfDict = List[dict]


class Db(GoogleSprint):

    def __init__(self):
        super().__init__()
        self.engine = create_engine(f'sqlite:///{FILENAME}.db', echo=False)
        self.spread = self.gs.open(FILENAME)
        self.sheets = AutoOrderedDict()
        self.sheets.pending = self.spread.worksheet(pending.capitalize())
        self.sheets.open = self.spread.worksheet(_open.capitalize())
        self.sheets.closed = self.spread.worksheet(closed.capitalize())
        self.emptydf = pd.DataFrame(columns=Xone.attrs)
        self.pending: ListOfDict = pd.read_sql_table(pending, self.engine).to_dict(orient='records')
        self.open: ListOfDict = pd.read_sql_table(_open, self.engine).to_dict(orient='records')
        self.closed: ListOfDict = pd.read_sql_table(closed, self.engine).to_dict(orient='records')
        self.q = Queue()
        self.gsq = Queue()
        self.dbupdater = Thread(target=self.update_db, daemon=True).start()
        self.gsupdater = Thread(target=self.update_gs, daemon=True).start()

    def to_sql(self, df: pd.DataFrame, tname: str):
        df.to_sql(tname, self.engine, if_exists='replace', index=False)

    def update_db(self):
        while True:
            xone_dicts = self.q.get()
            while not self.q.empty():
                xone_dicts = self.q.get()
            dfs = dict()
            for xtype, xdict in xone_dicts.items():
                if xdict:
                    self.__setattr__(xtype, [x.getvalues() for s, x in xdict.items()])
                    df = pd.DataFrame(self.__getattribute__(xtype), columns=Xone.attrs)
                    self.to_sql(df, xtype)
                    dfs.update({xtype: df})
                else:
                    self.to_sql(self.emptydf, xtype)
                    dfs.update({xtype: self.emptydf})
            self.gsq.put(dfs)

    def update_gs(self):
        while True:
            xone_dfs: Dict[str, pd.DataFrame] = self.gsq.get()
            while not self.gsq.empty():
                xone_dfs: Dict[str, pd.DataFrame] = self.gsq.get()
            for xtype, xdf in xone_dfs.items():
                self.sheets[xtype.capitalize()].clear()
                self.update_sheet(self.sheets[xtype.capitalize()], xdf)
            sleep(6)
