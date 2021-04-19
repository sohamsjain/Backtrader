import sys
import traceback
from collections import OrderedDict
from threading import Event, Thread
from typing import Dict

import backtrader as bt
import pandas as pd

from grid.db import Db
from grid.mysizer import MySizer
from grid.sheets import Sheets
from grid.strategy import Grid
from grid.workstation import WorkStation
from grid.xone import *
from mytelegram.raven import Raven, raven_json_path, raven_token

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
        self.event.set()

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
            del dfs

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
            try:
                xone: Optional[Xone] = spawn(each_dict)
                dict_to_return.update({xone.symbol: xone})
            except (AssertionError, ValueError) as e:
                # send a raven
                print(each_dict, e, sep="\n")
        return dict_to_return

    def spawn(self, vals):
        try:
            xone: Optional[Xone] = spawn(vals)
            symbol = xone.symbol
            if symbol in self.alive:
                return f"There already exists a xone for symbol {symbol}"
            else:
                self.pending.update({symbol: xone})
                self.alive.update({symbol: xone})
                self.event.set()
                return xone.getvalues()
        except (AssertionError, ValueError) as e:
            return e

    def run(self):
        try:
            cerebro = bt.Cerebro()

            store = bt.stores.IBStore(port=7497)

            datas = [store.getdata(dataname=stk, rtbar=True, backfill_start=False) for stk in contracts]

            for d in datas:
                cerebro.resampledata(d, timeframe=bt.TimeFrame.Seconds, compression=5)

            cerebro.setbroker(store.getbroker())

            cerebro.addstrategy(Grid, manager=self)

            cerebro.addsizer(MySizer)

            cerebro.run()

        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
