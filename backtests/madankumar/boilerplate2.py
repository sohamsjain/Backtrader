import backtrader as bt

from analyzers.googlesheets import GoogleSheetReport
from madankumar.strategy import *
from sizers.mysizers import MySizer

fromdate = datetime.now().replace(year=2021, month=12, day=10, hour=0, minute=0, second=0, microsecond=0)
todate = datetime.now().replace(year=2020, month=8, day=20, hour=0, minute=0, second=0, microsecond=0)

cerebro = bt.Cerebro(runonce=False)
cerebro.addstrategy(Madan, trailoffset=40)

store = bt.stores.IBStore(port=7497)

# data 0
data = store.getdata(dataname="NIFTY50-IND-NSE", fromdate=fromdate, historical=True, tz='Asia/Calcutta')
cerebro.resampledata(data,
                     timeframe=bt.TimeFrame.Minutes,
                     compression=1,
                     rightedge=False)

# data 1
cerebro.resampledata(data,
                     timeframe=bt.TimeFrame.Minutes,
                     compression=1,
                     rightedge=False)

# data 2
cerebro.resampledata(data,
                     timeframe=bt.TimeFrame.Minutes,
                     compression=5,
                     rightedge=False,
                     boundoff=1)

cerebro.broker.setcash(300000.0)

print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.addanalyzer(GoogleSheetReport)

cerebro.addsizer(MySizer, margin=2000, lot_size=75, pct_risk=2)

cerebro.broker.setcommission(margin=2000)

thestrats = cerebro.run()

print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.plot(barup='green', style='candle', volume=False)
