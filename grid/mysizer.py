import backtrader as bt


class MySizer(bt.Sizer):
    params = (
        ('pct_risk', 1),
        ('percent', 95),
        ('lot_size', 1),
        ('margin', None)
    )

    def _getsizing(self, comminfo, cash, data, isbuy):

        value = self.broker.get_value()
        prisk = (self.p.pct_risk / 100) * value
        x = self.strategy.manager.alive[data._dataname]
        riskqty = abs(int((prisk / x.rpu) / self.p.lot_size)) * self.p.lot_size

        if self.p.margin:
            cashqty = abs(int(cash / (self.p.margin * self.p.lot_size))) * self.p.lot_size
            alloqty = abs(int((value / self.strategy.p.maxpos) / (self.p.margin * self.p.lot_size))) * self.p.lot_size

        else:
            cashqty = int(
                abs(int((cash * (self.p.percent / 100)) / (data.close[0] * self.p.lot_size))) * self.p.lot_size)
            alloqty = int(abs(int(((value / self.strategy.p.maxpos) * (self.p.percent / 100)) / (
                    data.close[0] * self.p.lot_size))) * self.p.lot_size)

        return min(cashqty, riskqty, alloqty)
