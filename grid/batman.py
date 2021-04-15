from collections import OrderedDict
from threading import Event, Thread
from typing import Dict

import pandas as pd

from db import Db
from grid.xone import *
from grid.xone import Xone
from mytelegram.raven import Raven, raven_token, raven_json_path
from sheets import Sheets
from workstation import WorkStation

pending, _open, closed = 'pending', 'open', 'closed'
xonetypes = {pending, _open, closed}
FILENAME = 'Xones'

ListOfDict = List[dict]
DictOfXones = Dict[str, Xone]


class BaTMan:

    def __init__(self):
        self.database = Db()
        self.googlesheet = Sheets()
        self.workstation = WorkStation()
        self.workstation.set_manager(self)
        self.raven = Raven(raven_token, raven_json_path)
        self.raven.set_manager(self)

        self.emptydf = pd.DataFrame(columns=Xone.attrs)

        self.pending: DictOfXones = OrderedDict(self.spawn_multiple(self.database.pending))
        self.open: DictOfXones = OrderedDict(self.spawn_multiple(self.database.open))
        self.closed: DictOfXones = OrderedDict(self.spawn_multiple(self.database.closed))

        self.all = dict(pending=self.pending, open=self.open, closed=self.closed)
        self.alive = {**self.pending, **self.open}

        self.event = Event()
        self.updater = Thread(target=self.update, daemon=True)
        self.updater.start()

    def update(self):
        while self.event.wait():
            self.event.clear()
            dfs = dict()
            for xonetype, xonedict in self.all.items():
                if len(xonedict) > 0:
                    df = pd.DataFrame([x.getvalues() for s, x in xonedict.items()], columns=Xone.attrs)
                    dfs.update({xonetype: df})
                else:
                    dfs.update({xonetype: self.emptydf})
            self.put(dfs)

    def put(self, dfs):
        self.database.q.put(dfs)
        self.googlesheet.q.put(dfs)
        self.workstation.q.put(dfs)

    def p2c(self, x):
        self.alive.pop(x.symbol)
        self.pending.pop(x.symbol)
        self.closed.update({x.symbol: x})
        self.event.set()

    def p2o(self, x):
        self.pending.pop(x.symbol)
        self.open.update({x.symbol: x})
        self.event.set()

    def o2c(self, x):
        self.alive.pop(x.symbol)
        self.open.pop(x.symbol)
        self.closed.update({x.symbol: x})
        self.event.set()

    @staticmethod
    def spawn_multiple(listofdict: ListOfDict) -> dict:
        dict_to_return = dict()
        for each_dict in listofdict:
            xone: Optional[Xone] = spawn(each_dict)
            if isinstance(xone, Xone):
                dict_to_return.update({xone.symbol: xone})
            else:
                # send a raven
                print(each_dict, xone, sep="\n")
        return dict_to_return

    def spawn(self, vals):
        xone: Optional[Xone] = spawn(vals)
        if isinstance(xone, Xone):
            symbol = xone.symbol
            if symbol in self.alive:
                return f"There already exists a xone for symbol {symbol}"
            else:
                self.pending.update({symbol: xone})
        else:
            return xone
