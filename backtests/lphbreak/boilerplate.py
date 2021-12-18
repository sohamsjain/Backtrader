from analyzers.myanalyzers import PivotAnalyzer
from database.nifty import *
from lphbreak.strategy import *
from sizers.mysizers import MySizer

cerebro = bt.Cerebro(runonce=False)
cerebro.addstrategy(Pivot, trailoffset=40)

# data0
cerebro.adddata(spotdata)

# data1
cerebro.resampledata(spotdata,
                     timeframe=bt.TimeFrame.Minutes,
                     compression=5)

cerebro.broker.setcash(300000.0)

print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.addanalyzer(PivotAnalyzer, filename='report2.xlsx')

cerebro.addsizer(MySizer, margin=2000, lot_size=75, pct_risk=2)

cerebro.broker.setcommission(margin=2000)

thestrats = cerebro.run()

print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.plot(barup='green', style='candle', volume=False)
