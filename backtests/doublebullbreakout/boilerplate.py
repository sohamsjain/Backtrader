# from CSVData.nifty import *
import datetime

import backtrader as bt

from indicators.doublebull import BarType


class TestStrat(bt.Strategy):
    def __init__(self):
        self.myindicator = BarType(self.data0)

    def next(self):
        print(self.data0.close[0])


fromdate = datetime.datetime.now().replace(year=2011, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
todate = datetime.datetime.now().replace(year=2021, month=1, day=10, hour=0, minute=0, second=0, microsecond=0)

cerebro = bt.Cerebro()
cerebro.addstrategy(TestStrat)

store = bt.stores.IBStore(port=7497)
cerebro.setbroker(store.getbroker())

# data0
data = store.getdata(dataname="NIFTY50-IND-NSE", historical=True, fromdate=fromdate)  # , todate=todate)
cerebro.resampledata(data,
                     timeframe=bt.TimeFrame.Minutes,
                     compression=5)

thestrats = cerebro.run()

cerebro.plot(barup='green', style='candle', volume=False)
