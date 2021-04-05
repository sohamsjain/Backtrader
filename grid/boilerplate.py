from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from collections import OrderedDict

import backtrader as bt

from grid.mysizer import MySizer
from grid.xone import *
from nifty50list import NIFTY50LIST
from sheets import Sheets

googlesheet = Sheets()


class Grid(bt.Strategy):
    params = (
        ('gsheet', googlesheet),
        ('pending', googlesheet.pxones),
        ('open', googlesheet.oxones),
        ('closed', googlesheet.cxones),
        ('maxpos', 5)
    )

    def __init__(self):
        self.order = None
        self.orders = {data: None for data in self.datas}
        self.pxones = OrderedDict({d['symbol']: Xone(**d) for d in self.p.pending})
        self.oxones = OrderedDict({d['symbol']: Xone(**d) for d in self.p.open})
        self.cxones = OrderedDict({d['symbol']: Xone(**d) for d in self.p.closed})
        self.allx = dict(p=self.pxones, o=self.oxones, c=self.cxones)
        self.alivex = {**self.pxones, **self.oxones}
        self.openordercount = 0

    def notify_order(self, order):

        if order.status in [order.Submitted, order.Accepted, order.Partial]:
            return

        data = order.p.data
        stk = data._dataname

        try:
            x = self.alivex[stk]
        except KeyError as k:
            print(k)
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                if x.islong:
                    self.openordercount -= 1
                    x.setstatus(ENTRY)
                    x.setsize(order.size)
                    self.p2o(x)
                else:
                    x.setstatus(x.nextstatus)
                    self.o2c(x)
            else:
                if x.islong:
                    x.setstatus(x.nextstatus)
                    self.o2c(x)
                else:
                    self.openordercount -= 1
                    x.setstatus(ENTRY)
                    x.setsize(order.size)
                    self.p2o(x)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order.status == order.Canceled:
                x.status = CANCELLED
            elif order.status == order.Margin:
                x.status = MARGIN
            else:
                x.status = REJECTED
            self.p2c(x)

        self.orders[data] = None

    def next(self):
        for data in self.datas:
            stk = data._dataname

            if stk not in self.alivex:
                continue

            if self.orders[data]:
                continue

            x = self.alivex[stk]

            if x.status == PENDING:
                if x.islong:
                    if x.entryhit and data.high[0] >= x.target:
                        x.setstatus(MISSED)
                        self.p2c(x)
                        continue
                    if data.low[0] < x.stoploss:
                        x.setstatus(FAILED)
                        self.p2c(x)
                        continue
                    if data.low[0] <= x.entry:
                        x.entryhit = True
                        if (len(self.oxones) + self.openordercount) < self.p.maxpos:
                            self.orders[data] = self.buy(data=data)
                            self.openordercount += 1

                else:
                    if x.entryhit and data.low[0] <= x.target:
                        x.setstatus(MISSED)
                        self.p2c(x)
                        continue
                    if data.high[0] > x.stoploss:
                        x.setstatus(FAILED)
                        self.p2c(x)
                        continue
                    if data.high[0] >= x.entry:
                        x.entryhit = True
                        if (len(self.oxones) + self.openordercount) < self.p.maxpos:
                            self.orders[data] = self.sell(data=data)
                            self.openordercount += 1

            elif x.status == ENTRY:

                if x.islong:
                    if data.low[0] < x.stoploss:
                        self.orders[data] = self.close(data=data)
                        x.nextstatus = STOPLOSS
                    elif data.high[0] >= x.target:
                        self.orders[data] = self.close(data=data)
                        x.nextstatus = TARGET
                else:
                    if data.high[0] > x.stoploss:
                        self.orders[data] = self.close(data=data)
                        x.nextstatus = STOPLOSS
                    elif data.low[0] <= x.target:
                        self.orders[data] = self.close(data=data)
                        x.nextstatus = TARGET

            else:
                continue

    def p2c(self, x):
        self.alivex.pop(x.symbol)
        self.pxones.pop(x.symbol)
        self.cxones.update({x.symbol: x})
        self.p.gsheet.queue.put(self.allx.copy())

    def p2o(self, x):
        self.pxones.pop(x.symbol)
        self.oxones.update({x.symbol: x})
        self.p.gsheet.queue.put(self.allx.copy())

    def o2c(self, x):
        self.alivex.pop(x.symbol)
        self.oxones.pop(x.symbol)
        self.cxones.update({x.symbol: x})
        self.p.gsheet.queue.put(self.allx.copy())


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
