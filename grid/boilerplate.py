from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from typing import Dict

import backtrader as bt

from grid.db import Db
from grid.mysizer import MySizer
from grid.nifty50list import NIFTY50LIST
from grid.util import *
from grid.xone import *

XoneDict = Dict[str, Xone]


class Grid(bt.Strategy):
    params = (
        ('maxpos', 5)
    )

    def __init__(self):
        self.db = Db()
        self.order = None
        self.orders = {data: None for data in self.datas}
        self.pending: XoneDict = OrderedDict({d['symbol']: Xone(**d) for d in self.db.pending})
        self.open: XoneDict = OrderedDict({d['symbol']: Xone(**d) for d in self.db.open})
        self.closed: XoneDict = OrderedDict({d['symbol']: Xone(**d) for d in self.db.closed})
        self.all = dict(pending=self.pending, open=self.open, closed=self.closed)
        self.alive = {**self.pending, **self.open}
        self.openordercount = 0

    def notify_order(self, order):

        if order.status in [order.Submitted, order.Accepted, order.Partial]:
            return

        data = order.p.data
        stk: str = data._dataname

        try:
            x: Xone = self.alive[stk]
        except KeyError as k:
            print(k)
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                if x.islong:
                    self.openordercount -= 1
                    x.setstate(ENTRY)
                    x.setsize(order.size)
                    self.p2o(x)
                else:
                    x.setstate(x.nextstate)
                    self.o2c(x)
            else:
                if x.islong:
                    x.setstate(x.nextstate)
                    self.o2c(x)
                else:
                    self.openordercount -= 1
                    x.setstate(ENTRY)
                    x.setsize(order.size)
                    self.p2o(x)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order.status == order.Canceled:
                x.state = CANCELLED
            elif order.status == order.Margin:
                x.state = MARGIN
            else:
                x.state = REJECTED
            self.p2c(x)

        self.orders[data] = None

    def next(self):
        for data in self.datas:
            stk: str = data._dataname

            if stk not in self.alive:
                continue

            if self.orders[data]:
                continue

            x: Xone = self.alive[stk]

            if x.state == PENDING:
                if x.islong:
                    if x.entryhit and data.high[0] >= x.target:
                        x.setstate(MISSED)
                        self.p2c(x)
                        continue
                    if data.low[0] < x.stoploss:
                        x.setstate(FAILED)
                        self.p2c(x)
                        continue
                    if data.low[0] <= x.entry:
                        x.entryhit = 1
                        if (len(self.open) + self.openordercount) < self.p.maxpos:
                            self.orders[data] = self.buy(data=data)
                            self.openordercount += 1

                else:
                    if x.entryhit and data.low[0] <= x.target:
                        x.setstate(MISSED)
                        self.p2c(x)
                        continue
                    if data.high[0] > x.stoploss:
                        x.setstate(FAILED)
                        self.p2c(x)
                        continue
                    if data.high[0] >= x.entry:
                        x.entryhit = 1
                        if (len(self.open) + self.openordercount) < self.p.maxpos:
                            self.orders[data] = self.sell(data=data)
                            self.openordercount += 1

            elif x.state == ENTRY:

                if x.islong:
                    if data.low[0] < x.stoploss:
                        self.orders[data] = self.close(data=data)
                        x.nextstate = STOPLOSS
                    elif data.high[0] >= x.target:
                        self.orders[data] = self.close(data=data)
                        x.nextstate = TARGET
                else:
                    if data.high[0] > x.stoploss:
                        self.orders[data] = self.close(data=data)
                        x.nextstate = STOPLOSS
                    elif data.low[0] <= x.target:
                        self.orders[data] = self.close(data=data)
                        x.nextstate = TARGET

            else:
                continue

    def p2c(self, x):
        self.alive.pop(x.symbol)
        self.pending.pop(x.symbol)
        self.closed.update({x.symbol: x})
        self.db.q.put(self.all.copy())

    def p2o(self, x):
        self.pending.pop(x.symbol)
        self.open.update({x.symbol: x})
        self.db.q.put(self.all.copy())

    def o2c(self, x):
        self.alive.pop(x.symbol)
        self.open.pop(x.symbol)
        self.closed.update({x.symbol: x})
        self.db.q.put(self.all.copy())


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    store = bt.stores.IBStore(host="", port=7497, _debug=False)

    # datas = [store.getdata(dataname=stk, historical=True,
    #                        fromdate=datetime.now().date()) for stk in NIFTY50LIST]

    datas = [store.getdata(dataname=stk, rtbar=True, backfill_start=False) for stk in NIFTY50LIST]
    for data in datas:
        cerebro.resampledata(data, timeframe=bt.TimeFrame.Seconds, compression=5)

    cerebro.setbroker(store.getbroker())
    # cerebro.broker.setcash(100000.0)
    cerebro.addstrategy(Grid)
    cerebro.addsizer(MySizer)
    cerebro.run()
