import pytz
from backtrader import Analyzer
from backtrader.utils.dateintern import num2dt, num2time

from mygoogle.sprint import GoogleSprint

gs = GoogleSprint()

cols = ['din', 'tin', 'dout', 'tout', 'entry_point', 'stoploss_point', 'btentry', 'exit_point', 'btexit', 'atr',
        'reason', 'position', 'size', 'urisk', 'gross_pnl', 'net_pnl', 'capital']

asiacalcutta = pytz.timezone(r"Asia/Calcutta")


class GoogleSheetReport(Analyzer):
    params = (
        ('filename', 'report.xlsx'),
    )

    def __init__(self):
        self.sprint = GoogleSprint()
        self.spread = self.sprint.gs.open("Live Trading Reports")
        self.sheet = self.spread.worksheet("Trades")
        self.pushid = len(self.sheet.get_all_values()) + 1

    def create_analysis(self):
        self.trade = dict()
        self.rets = list()

    def stop(self):
        del self.trade

    def notify_trade(self, trade):

        if trade.status == trade.Closed:
            self.trade.update(
                dict(
                    din=str(num2dt(trade.dtopen, tz=asiacalcutta)),
                    tin=str(num2time(trade.dtopen, tz=asiacalcutta)),
                    dout=str(num2dt(trade.dtclose, tz=asiacalcutta)),
                    tout=str(num2time(trade.dtclose, tz=asiacalcutta)),
                    position="Long" if trade.long else "Short",
                    gross_pnl=trade.pnl,
                    net_pnl=trade.pnlcomm,
                    capital=self.strategy.broker.getvalue(),
                )
            )
            l = [self.trade[colname] for colname in cols]
            l.insert(0, self.pushid - 1)
            self.sheet.update(f"A{self.pushid}", [l])
            self.pushid += 1
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
