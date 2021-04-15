from queue import Queue
from threading import Thread
from time import sleep
from typing import List, Dict, Optional

import pandas as pd
from sqlalchemy import create_engine

pending, _open, closed = 'pending', 'open', 'closed'
xonetypes = {pending, _open, closed}
FILENAME = 'Xones'

ListOfDict = List[dict]


class Db:

    def __init__(self):
        self.engine = create_engine(f'sqlite:///{FILENAME}.db', echo=False)
        self.pending: Optional[ListOfDict] = list()
        self.open: Optional[ListOfDict] = list()
        self.closed: Optional[ListOfDict] = list()

        for xtype in xonetypes:
            try:
                xdcts: Optional[ListOfDict] = pd.read_sql_table(xtype, self.engine).to_dict(orient='records')
            except ValueError as ve:
                print(ve)
                xdcts: Optional[ListOfDict] = list()
            self.__setattr__(xtype, xdcts)

        self.q = Queue()
        self.updater = Thread(target=self.update, daemon=True)
        self.updater.start()

    def to_sql(self, df: pd.DataFrame, tname: str):
        df.to_sql(tname, self.engine, if_exists='replace', index=False)

    def update(self):

        while True:

            # Jump to last state
            xone_dfs: Dict[str, pd.DataFrame] = self.q.get()
            while not self.q.empty():
                xone_dfs: Dict[str, pd.DataFrame] = self.q.get()

            # Check
            assert set(xone_dfs.keys()) == xonetypes

            # Write
            for xtype, xdf in xone_dfs.items():
                self.to_sql(xdf, xtype)

            sleep(3)
