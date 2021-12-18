import pandas as pd
import pytz
from backtrader import Analyzer
from backtrader.analyzers import TradeAnalyzer, DrawDown, SQN, SharpeRatio, SharpeRatio_A
from backtrader.utils import AutoOrderedDict, AutoDict
from backtrader.utils.dateintern import num2date, num2dt, num2time

tdcols = ['tsin', 'entry', 'position', 'tsout', 'exit', 'size', 'gross_pnl', 'net_pnl', 'capital']
pivot_cols = ['din', 'tin', 'dout', 'tout', 'entry_point', 'stoploss_point', 'btentry', 'exit_point', 'btexit', 'atr',
              'reason', 'position', 'size', 'urisk', 'gross_pnl', 'net_pnl', 'capital']
custompivot_cols = ['din', 'tin', 'dout', 'tout', 'entry_point', 'stoploss_point', 'secondsl', 'distance', 'btentry',
                    'exit_point', 'btexit', 'reason', 'position', 'size', 'urisk', 'gross_pnl', 'net_pnl', 'capital',
                    'dtrend', 'trend75', 'trend60', 'trend15', 'open', 'high', 'low', 'close', 'close1526', 'close1529']
woncols = ['won', 'freq']
lostcols = ['lost', 'freq']
exitcols = ['exittype', 'freq']

asiacalcutta = pytz.timezone(r"Asia/Calcutta")


class MyAnalyzer(Analyzer):
    params = (
        ('filename', 'report.xlsx'),
    )

    def __init__(self):
        self.tradeanalyzer = TradeAnalyzer()
        self.drawdown = DrawDown()
        self.sqn = SQN()

    def create_analysis(self):
        self.rets = AutoOrderedDict()
        self.trades = list()
        self.trade = dict()

    def stop(self):
        super(MyAnalyzer, self).stop()
        self.rets.trades = self.trades
        self.rets.starting_value = self.strategy.broker.startingcash
        self.rets.value = self.strategy.broker.get_value()
        self.rets.max_value = self.drawdown._maxvalue
        self.rets.tarets = self.tradeanalyzer.rets
        self.rets.ddrets = self.drawdown.rets
        self.rets.sqn = self.sqn.rets.sqn
        trades = self.rets.tarets.total.total
        won = self.rets.tarets.won.total
        lost = self.rets.tarets.lost.total
        winrate = won / trades
        lossrate = lost / trades
        maxwon = self.rets.tarets.won.pnl.max
        averagewon = self.rets.tarets.won.pnl.average
        totalwon = self.rets.tarets.won.pnl.total
        maxlost = self.rets.tarets.lost.pnl.max
        averagelost = self.rets.tarets.lost.pnl.average
        totallost = self.rets.tarets.lost.pnl.total
        self.rets.expectancy = winrate * abs(averagewon / averagelost) - lossrate
        stats = [
            ("Starting Cash", self.rets.starting_value),
            ("Cash", self.rets.value),
            ("Max Cash", self.rets.max_value),
            ("Max Moneydown", self.rets.ddrets.max.moneydown),
            ("Max Drawdown", self.rets.ddrets.max.drawdown),
            ("Winning Streak", self.rets.tarets.streak.won.longest),
            ("Losing Streak", self.rets.tarets.streak.lost.longest),
            ("Total Trades", trades),
            ("Trades Won", won),
            ("Trades Lost", lost),
            ("Win Rate", winrate),
            ("Loss Rate", lossrate),
            ("Max Won", maxwon),
            ("Average Won", averagewon),
            ("Total Won", totalwon),
            ("Max Lost", maxlost),
            ("Average Lost", averagelost),
            ("Total Lost", totallost),
            ("Expectancy", self.rets.expectancy),
            ("SQN", self.rets.sqn)
        ]
        w = pd.ExcelWriter(self.p.filename)
        statsdf = pd.DataFrame(stats, columns=["Keys", "Values"])
        df = pd.DataFrame(self.rets.trades, columns=tdcols)
        print(df)
        print(statsdf)
        df.to_excel(w, index=False, sheet_name='Trades')
        statsdf.to_excel(w, index=False, sheet_name="Stats")
        w.save()
        w.close()

    def notify_trade(self, trade):

        if trade.status == trade.Closed:
            self.trade.update(
                dict(
                    tsin=num2date(trade.dtopen),
                    tsout=num2date(trade.dtclose),
                    position="Long" if trade.long else "Short",
                    gross_pnl=trade.pnl,
                    net_pnl=trade.pnlcomm,
                    capital=self.strategy.broker.get_value(),
                )
            )

            self.trades.append(self.trade.copy())
            self.trade.clear()

    def notify_order(self, order):

        if order.status in [order.Completed]:
            if self.strategy.position:
                self.trade.update(
                    dict(
                        entry=order.executed.price,
                        size=order.executed.size,
                    )
                )
            else:
                self.trade.update(
                    dict(
                        exit=order.executed.price,
                    )
                )


class PivotAnalyzer(Analyzer):
    params = (
        ('filename', 'report.xlsx'),
    )

    def __init__(self):
        self.tradeanalyzer = TradeAnalyzer()
        self.drawdown = DrawDown()
        self.sqn = SQN()
        self.sharpe = SharpeRatio()
        self.sharpeA = SharpeRatio_A()
        self.streakpro = StreakProfile()
        self.exitpro = ExitProfile()

    def create_analysis(self):
        self.rets = AutoOrderedDict()
        self.trades = list()
        self.trade = dict()

    def stop(self):
        super(PivotAnalyzer, self).stop()
        self.rets.trades = self.trades
        self.rets.starting_value = self.strategy.broker.startingcash
        self.rets.value = self.strategy.broker.get_value()
        self.rets.max_value = self.drawdown._maxvalue
        self.rets.tarets = self.tradeanalyzer.rets
        self.rets.ddrets = self.drawdown.rets
        self.rets.sqn = self.sqn.rets.sqn
        trades = self.rets.tarets.total.total
        won = self.rets.tarets.won.total
        lost = self.rets.tarets.lost.total
        winrate = won / trades
        lossrate = lost / trades
        maxwon = self.rets.tarets.won.pnl.max
        averagewon = self.rets.tarets.won.pnl.average
        totalwon = self.rets.tarets.won.pnl.total
        maxlost = self.rets.tarets.lost.pnl.max
        averagelost = self.rets.tarets.lost.pnl.average
        totallost = self.rets.tarets.lost.pnl.total
        self.rets.expectancy = winrate * abs(averagewon / averagelost) - lossrate
        stats = [
            ("Starting Cash", self.rets.starting_value),
            ("Cash", self.rets.value),
            ("Max Cash", self.rets.max_value),
            ("Max Moneydown", self.rets.ddrets.max.moneydown),
            ("Max Drawdown", self.rets.ddrets.max.drawdown),
            ("Winning Streak", self.rets.tarets.streak.won.longest),
            ("Losing Streak", self.rets.tarets.streak.lost.longest),
            ("Total Trades", trades),
            ("Trades Won", won),
            ("Trades Lost", lost),
            ("Win Rate", winrate),
            ("Loss Rate", lossrate),
            ("Max Won", maxwon),
            ("Average Won", averagewon),
            ("Total Won", totalwon),
            ("Max Lost", maxlost),
            ("Average Lost", averagelost),
            ("Total Lost", totallost),
            ("Expectancy", self.rets.expectancy),
            ("SQN", self.rets.sqn),
            ("Sharpe", self.sharpe.rets['sharperatio']),
            ("Sharpe Annual", self.sharpeA.rets['sharperatio']),
        ]
        w = pd.ExcelWriter(self.p.filename)
        statsdf = pd.DataFrame(stats, columns=["Keys", "Values"])
        df = pd.DataFrame(self.rets.trades, columns=pivot_cols)
        print(df)
        print(statsdf)
        won = pd.DataFrame([[k, v] for k, v in self.streakpro.rets.won.items() if type(k) == int], columns=woncols)
        lost = pd.DataFrame([[k, v] for k, v in self.streakpro.rets.lost.items() if type(k) == int], columns=lostcols)
        exitpro = pd.DataFrame([[k, v] for k, v in self.exitpro.rets.items() if not k.startswith('_')],
                               columns=exitcols)
        df.to_excel(w, index=False, sheet_name='Trades')
        statsdf.to_excel(w, index=False, sheet_name="Stats")
        won.to_excel(w, index=False, sheet_name="Stats", startcol=3)
        lost.to_excel(w, index=False, sheet_name="Stats", startcol=5)
        exitpro.to_excel(w, index=False, sheet_name="Stats", startcol=7)
        w.save()
        w.close()

    def notify_trade(self, trade):

        if trade.status == trade.Closed:
            self.trade.update(
                dict(
                    din=num2dt(trade.dtopen, tz=asiacalcutta),
                    tin=num2time(trade.dtopen, tz=asiacalcutta),
                    dout=num2dt(trade.dtclose, tz=asiacalcutta),
                    tout=num2time(trade.dtclose, tz=asiacalcutta),
                    position="Long" if trade.long else "Short",
                    gross_pnl=trade.pnl,
                    net_pnl=trade.pnlcomm,
                    capital=self.strategy.broker.getvalue(),
                )
            )

            self.trades.append(self.trade.copy())
            self.trade.clear()

    def notify_order(self, order):

        if order.status in [order.Completed]:
            if self.strategy.position:
                self.trade.update(
                    dict(
                        entry_point=self.strategy.entry,
                        stoploss_point=self.strategy.stoploss,
                        btentry=order.executed.price,
                        size=order.executed.size,
                        urisk=self.strategy.urisk,
                        atr=self.strategy.atr[0]
                    )
                )
            else:
                self.trade.update(
                    dict(
                        exit_point=self.strategy.trailing_stoploss,
                        btexit=order.executed.price,
                        reason=self.strategy.exittype,
                    )
                )


class CustomPivotAnalyzer(Analyzer):
    params = (
        ('filename', 'report.xlsx'),
    )

    def __init__(self):
        self.tradeanalyzer = TradeAnalyzer()
        self.drawdown = DrawDown()
        self.sqn = SQN()
        self.sharpe = SharpeRatio()
        self.sharpeA = SharpeRatio_A()
        self.streakpro = StreakProfile()
        self.exitpro = ExitProfile()

    def create_analysis(self):
        self.rets = AutoOrderedDict()
        self.trades = list()
        self.daytrades = list()
        self.trade = dict()

    def stop(self):
        super(CustomPivotAnalyzer, self).stop()
        self.rets.trades = self.trades
        self.rets.starting_value = self.strategy.broker.startingcash
        self.rets.value = self.strategy.broker.get_value()
        self.rets.max_value = self.drawdown._maxvalue
        self.rets.tarets = self.tradeanalyzer.rets
        self.rets.ddrets = self.drawdown.rets
        self.rets.sqn = self.sqn.rets.sqn
        trades = self.rets.tarets.total.total
        won = self.rets.tarets.won.total
        lost = self.rets.tarets.lost.total
        winrate = won / trades
        lossrate = lost / trades
        maxwon = self.rets.tarets.won.pnl.max
        averagewon = self.rets.tarets.won.pnl.average
        totalwon = self.rets.tarets.won.pnl.total
        maxlost = self.rets.tarets.lost.pnl.max
        averagelost = self.rets.tarets.lost.pnl.average
        totallost = self.rets.tarets.lost.pnl.total
        self.rets.expectancy = winrate * abs(averagewon / averagelost) - lossrate
        stats = [
            ("Starting Cash", self.rets.starting_value),
            ("Cash", self.rets.value),
            ("Max Cash", self.rets.max_value),
            ("Max Moneydown", self.rets.ddrets.max.moneydown),
            ("Max Drawdown", self.rets.ddrets.max.drawdown),
            ("Winning Streak", self.rets.tarets.streak.won.longest),
            ("Losing Streak", self.rets.tarets.streak.lost.longest),
            ("Total Trades", trades),
            ("Trades Won", won),
            ("Trades Lost", lost),
            ("Win Rate", winrate),
            ("Loss Rate", lossrate),
            ("Max Won", maxwon),
            ("Average Won", averagewon),
            ("Total Won", totalwon),
            ("Max Lost", maxlost),
            ("Average Lost", averagelost),
            ("Total Lost", totallost),
            ("Expectancy", self.rets.expectancy),
            ("SQN", self.rets.sqn),
            ("Sharpe", self.sharpe.rets['sharperatio']),
            ("Sharpe Annual", self.sharpeA.rets['sharperatio']),
        ]
        w = pd.ExcelWriter(self.p.filename)
        statsdf = pd.DataFrame(stats, columns=["Keys", "Values"])
        df = pd.DataFrame(self.rets.trades, columns=custompivot_cols)
        print(df)
        print(statsdf)
        won = pd.DataFrame([[k, v] for k, v in self.streakpro.rets.won.items() if type(k) == int], columns=woncols)
        lost = pd.DataFrame([[k, v] for k, v in self.streakpro.rets.lost.items() if type(k) == int], columns=lostcols)
        exitpro = pd.DataFrame([[k, v] for k, v in self.exitpro.rets.items() if not k.startswith('_')],
                               columns=exitcols)
        df.to_excel(w, index=False, sheet_name='Trades')
        statsdf.to_excel(w, index=False, sheet_name="Stats")
        won.to_excel(w, index=False, sheet_name="Stats", startcol=3)
        lost.to_excel(w, index=False, sheet_name="Stats", startcol=5)
        exitpro.to_excel(w, index=False, sheet_name="Stats", startcol=7)
        w.save()
        w.close()

    def notify_trade(self, trade):

        if trade.status == trade.Closed:
            self.trade.update(
                dict(
                    din=num2dt(trade.dtopen),
                    tin=num2time(trade.dtopen),
                    dout=num2dt(trade.dtclose),
                    tout=num2time(trade.dtclose),
                    position="Long" if trade.long else "Short",
                    gross_pnl=trade.pnl,
                    net_pnl=trade.pnlcomm,
                    capital=self.strategy.broker.get_value(),
                )
            )

            self.daytrades.append(self.trade.copy())
            self.trade.clear()

    def notify_order(self, order):

        if order.status in [order.Completed]:
            if self.strategy.position:
                self.trade.update(
                    dict(
                        entry_point=self.strategy.entry,
                        stoploss_point=self.strategy.stoploss,
                        btentry=order.executed.price,
                        size=order.executed.size,
                        urisk=self.strategy.urisk,
                        secondsl=self.strategy.secondsl,
                        distance=self.strategy.distance,
                        dtrend=self.strategy.fd.trend,
                        trend75=self.strategy.f75.trend,
                        trend60=self.strategy.f60.trend,
                        trend15=self.strategy.f15.trend,
                    )
                )
            else:
                self.trade.update(
                    dict(
                        exit_point=self.strategy.trailing_stoploss,
                        btexit=order.executed.price,
                        reason=self.strategy.exittype,
                    )
                )

    def customohlc(self, o, h, l, c, c26, c29):

        for trade in self.daytrades:
            trade.update(
                dict(
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    close1526=c26,
                    close1529=c29
                )
            )
            self.trades.append(trade.copy())
        self.daytrades.clear()


class PivotMTFAnalyzer(PivotAnalyzer):

    def notify_order(self, order):

        if order.status in [order.Completed]:
            if self.strategy.position:
                self.trade.update(
                    dict(
                        entry_point=self.strategy.entry,
                        stoploss_point=self.strategy.stoploss,
                        btentry=order.executed.price,
                        size=order.executed.size,
                        urisk=self.strategy.urisk,
                        # Todo mtf trends
                    )
                )
            else:
                self.trade.update(
                    dict(
                        exit_point=self.strategy.trailing_stoploss,
                        btexit=order.executed.price,
                        reason=self.strategy.exittype,
                    )
                )


class StreakProfile(Analyzer):

    def create_analysis(self):
        self.rets = AutoOrderedDict()
        self.rets.won = AutoOrderedDict()
        self.rets.lost = AutoOrderedDict()

    def stop(self):
        super(StreakProfile, self).stop()
        self.rets._close()

    def notify_trade(self, trade):

        if trade.status == trade.Closed:
            trades = self.rets

            res = AutoDict()
            # Trade just closed

            won = res.won = int(trade.pnlcomm >= 0.0)
            lost = res.lost = int(not won)

            # Streak
            for wlname in ['won', 'lost']:
                wl = res[wlname]
                prev = trades.streak[wlname].current

                trades.streak[wlname].current *= wl
                trades.streak[wlname].current += wl

                if type(prev) == int:
                    if prev > 0 and trades.streak[wlname].current == 0:
                        self.rets[wlname][prev] += 1


class ExitProfile(Analyzer):

    def create_analysis(self):
        self.rets = AutoOrderedDict()

    def stop(self):
        super(ExitProfile, self).stop()
        self.rets._close()

    def notify_trade(self, trade):
        if trade.status == trade.Closed:
            self.rets[self.strategy.exittype] += 1
