import backtrader as bt

from analyzers.myanalyzers import PivotAnalyzer
from madankumar.strategy import *
from sizers.mysizers import MySizer

fromdate = datetime.now().date() - timedelta(days=5)
sessionstart = datetime.now().time().replace(hour=9, minute=15, second=0, microsecond=0)
sessionend = datetime.now().time().replace(hour=15, minute=30, second=0, microsecond=0)

cerebro = bt.Cerebro()
cerebro.addstrategy(MadanTest, trailoffset=40)

store = bt.stores.IBStore(port=7497)
cerebro.setbroker(store.getbroker())


class BackwardLookingFilter(object):

    def __init__(self, data):
        pass

    def __call__(self, data):
        data.datetime[0] = data.date2num(data.datetime.datetime(0) + timedelta(seconds=5))
        return False


# data 0 NIFTY50-FUT-NSE-INR-202112
data0 = store.getdata(dataname="NIFTY50-IND-NSE", fromdate=fromdate, rtbar=True, sessionstart=sessionstart,
                      sessionend=sessionend, historical=True, timeframe=bt.TimeFrame.Seconds,
                      compression=5)
data0.addfilter(BackwardLookingFilter)
cerebro.adddata(data0)

# data 1
data1 = store.getdata(dataname="NIFTY50-IND-NSE", backfill_from=data0, rtbar=True, sessionstart=sessionstart,
                      sessionend=sessionend)
data1.addfilter(BackwardLookingFilter)
cerebro.resampledata(data1,
                     timeframe=bt.TimeFrame.Minutes,
                     compression=1)

# data 2
cerebro.resampledata(data1,
                     timeframe=bt.TimeFrame.Minutes,
                     compression=5)

cerebro.addanalyzer(PivotAnalyzer, filename='report12.xlsx')

cerebro.addsizer(MySizer, margin=2000, lot_size=50, pct_risk=2)

thestrats = cerebro.run()

cerebro.plot(barup='green', style='candle', volume=False)
