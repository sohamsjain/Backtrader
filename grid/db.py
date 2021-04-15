from queue import Queue
from threading import Thread
from time import sleep
from typing import List, Dict

import pandas as pd
from sqlalchemy import create_engine

pending, _open, closed = 'pending', 'open', 'closed'
xonetypes = {pending, _open, closed}
FILENAME = 'Xones'

ListOfDict = List[dict]


class Db:

    def __init__(self):
        self.engine = create_engine(f'sqlite:///{FILENAME}.db', echo=False)
        self.pending: ListOfDict = pd.read_sql_table(pending, self.engine).to_dict(orient='records')
        self.open: ListOfDict = pd.read_sql_table(_open, self.engine).to_dict(orient='records')
        self.closed: ListOfDict = pd.read_sql_table(closed, self.engine).to_dict(orient='records')
        self.q = Queue()
        self.dbupdater = Thread(target=self.update, daemon=True).start()

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
