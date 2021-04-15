from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt

from grid.xone import *


class Grid(bt.Strategy):
    params = (
        ('maxpos', 5),
        ('manager', None)
    )

    def __init__(self):
        self.manager = self.p.manager
        self.order = None
        self.orders = {data: None for data in self.datas}
        self.openordercount = 0

    def notify_order(self, order):

        if order.status in [order.Submitted, order.Accepted, order.Partial]:
            return

        data = order.p.data
        stk: str = data._dataname

        try:
            xone: Xone = self.manager.alive[stk]
        except KeyError as k:
            print(k)
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                if xone.islong:
                    self.openordercount -= 1
                    xone.setstate(ENTRY)
                    xone.setsize(order.size)
                    self.manager.p2o(xone)
                else:
                    xone.setstate(xone.nextstate)
                    self.manager.o2c(xone)
            else:
                if xone.islong:
                    xone.setstate(xone.nextstate)
                    self.manager.o2c(xone)
                else:
                    self.openordercount -= 1
                    xone.setstate(ENTRY)
                    xone.setsize(order.size)
                    self.manager.p2o(xone)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order.status == order.Canceled:
                xone.state = CANCELLED
            elif order.status == order.Margin:
                xone.state = MARGIN
            else:
                xone.state = REJECTED
            self.manager.p2c(xone)

        self.orders[data] = None

    def next(self):
        for data in self.datas:
            stk: str = data._dataname

            if stk not in self.manager.alive:
                continue

            if self.orders[data]:
                continue

            x: Xone = self.manager.alive[stk]

            if x.state == PENDING:
                if x.islong:
                    if x.entryhit and data.high[0] >= x.target:
                        x.setstate(MISSED)
                        self.manager.p2c(x)
                        continue
                    if data.low[0] < x.stoploss:
                        x.setstate(FAILED)
                        self.manager.p2c(x)
                        continue
                    if data.low[0] <= x.entry:
                        x.entryhit = 1
                        if (len(self.open) + self.openordercount) < self.p.maxpos:
                            self.orders[data] = self.buy(data=data)
                            self.openordercount += 1

                else:
                    if x.entryhit and data.low[0] <= x.target:
                        x.setstate(MISSED)
                        self.manager.p2c(x)
                        continue
                    if data.high[0] > x.stoploss:
                        x.setstate(FAILED)
                        self.manager.p2c(x)
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


if __name__ == '__main__':

    from mysizers import MySizer

    cerebro = bt.Cerebro()
    store = bt.stores.IBStore(port=7497, _debug=False)

    # datas = [store.getdata(dataname=stk, historical=True,
    #                        fromdate=datetime.now().date()) for stk in NIFTY50LIST]

    datas = [store.getdata(dataname=stk, rtbar=True, backfill_start=False) for stk in contracts]
    for d in datas:
        cerebro.resampledata(d, timeframe=bt.TimeFrame.Seconds, compression=5)

    cerebro.setbroker(store.getbroker())
    # cerebro.broker.setcash(100000.0)
    cerebro.addstrategy(Grid)
    cerebro.addsizer(MySizer)
    cerebro.run()
