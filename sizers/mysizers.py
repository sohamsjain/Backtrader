import backtrader as bt

from utils import price


class MySizer(bt.Sizer):
    params = (
        ('pct_risk', 1),
        ('percents', 90),
        ('lot_size', 1),
        ('margin', None)
    )

    def _getsizing(self, comminfo, cash, data, isbuy):

        prisk = price((self.p.pct_risk / 100) * cash)
        urisk = abs(self.strategy.entry - self.strategy.stoploss)

        riskqty = abs(int((prisk / urisk) / self.p.lot_size)) * self.p.lot_size

        if self.p.margin:
            cashqty = abs(int(cash / (self.p.margin * self.p.lot_size))) * self.p.lot_size
        else:
            cashqty = int((abs(int(cash / (data.close[0] * self.p.lot_size))) * self.p.lot_size) * \
                          (self.params.percents / 100))

        return min(cashqty, riskqty)
