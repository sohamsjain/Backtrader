from backtrader import Strategy
from backtrader.indicators import AverageTrueRange

from indicators.pivots import *
from utils import *

_3 = 0.003
pct = _3
min1 = 1
min5 = 2


class PivotStatus:
    LPH_BREAK = 'LPH_BREAK'
    LPL_BREAK = 'LPL_BREAK'
    # None


class Madan(Strategy):
    params = (
        ('trailoffset', 0),
        ('pct', pct),
        ('acton', 0),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        self.pivot = Pivots(self.datas[min5])
        self.atr = AverageTrueRange(self.datas[min5])
        self.pivot_status = None
        self.start_trailing = False

        self.last_entry_time = datetime.now().replace(hour=15, minute=10, second=0, microsecond=0).time()
        self.square_off_time = datetime.now().replace(hour=15, minute=15, second=0, microsecond=0).time()
        self.entry = None
        self.stoploss = None
        self.exittype = None
        self.trailing_stoploss = None
        self.urisk = None
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.min5 = False

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        self.mynext()
        self.postnext()

    def mynext(self):
        _open = self.datas[min1].open[0]
        high = self.datas[min1].high[0]
        low = self.datas[min1].low[0]
        close = self.datas[min1].close[0]
        ltt = self.datas[min1].datetime.time(0)
        ltts = self.datas[min1].datetime.datetime(0)

        if self.pivot_status:
            phigh, plow, pclose = self.datas[min5].high[-1], self.datas[min5].low[-1], self.datas[min5].close[-1]
            chigh, clow, cclose = self.datas[min5].high[0], self.datas[min5].low[0], self.datas[min5].close[0]

            if self.start_trailing:
                if self.pivot_status == PivotStatus.LPH_BREAK:
                    if (chigh > phigh) \
                            and (clow > plow) \
                            and (cclose > pclose) \
                            and (plow > self.trailing_stoploss):
                        self.trailing_stoploss = plow
                        self.exittype = "Trailing"

                elif self.pivot_status == PivotStatus.LPL_BREAK:
                    if (chigh < phigh) \
                            and (clow < plow) \
                            and (cclose < pclose) \
                            and (phigh < self.trailing_stoploss):
                        self.trailing_stoploss = phigh
                        self.exittype = "Trailing"

            elif not self.start_trailing:

                if self.p.trailoffset:
                    if self.pivot_status == PivotStatus.LPL_BREAK:
                        if chigh < (self.entry - self.p.trailoffset):
                            self.start_trailing = True

                    elif self.pivot_status == PivotStatus.LPH_BREAK:
                        if clow > (self.entry + self.p.trailoffset):
                            self.start_trailing = True

                else:
                    if self.pivot_status == PivotStatus.LPH_BREAK:
                        if cclose > self.entry:
                            self.start_trailing = True

                    elif self.pivot_status == PivotStatus.LPL_BREAK:
                        if cclose < self.entry:
                            self.start_trailing = True

        if self.pivot_status is None:

            if low < self.pivot.lpl_value and self.pivot.new_lpl and self.pivot.large_pivot == LPH:
                self.pivot.new_lpl = False

                if ltt >= self.last_entry_time:
                    return

                hp, hpx = self.pivot.sph_value, self.pivot.sph_index
                slice_of_high = self.datas[min5].high.get(ago=-1, size=abs(hpx + 1))
                for sliced_high in slice_of_high:
                    if sliced_high > hp:
                        hp = sliced_high

                if _open < self.pivot.lpl_value:
                    self.entry = _open
                else:
                    self.entry = self.pivot.lpl_value
                point_three_percent = self.p.pct * self.entry
                sl = round_up(self.entry + point_three_percent)
                self.exittype = "SPH" if hp < sl else ".3%"
                self.stoploss = min(hp, sl)
                self.trailing_stoploss = self.stoploss
                self.urisk = abs(self.entry - self.stoploss)
                self.pivot_status = PivotStatus.LPL_BREAK
                self.start_trailing = False
                self.log("Sell signal at : " + str(self.entry))
                self.sell(data=self.datas[self.p.acton])
                return

            elif high > self.pivot.lph_value and self.pivot.new_lph and self.pivot.large_pivot == LPL:
                self.pivot.new_lph = False

                if ltt >= self.last_entry_time:
                    return

                lp, lpx = self.pivot.spl_value, self.pivot.spl_index
                slice_of_low = self.datas[min5].low.get(ago=-1, size=abs(lpx + 1))
                for sliced_low in slice_of_low:
                    if sliced_low < lp:
                        lp = sliced_low

                if _open > self.pivot.lph_value:
                    self.entry = _open
                else:
                    self.entry = self.pivot.lph_value
                point_three_percent = self.p.pct * self.entry
                sl = round_down(self.entry - point_three_percent)
                self.exittype = "SPL" if lp > sl else ".3%"
                self.stoploss = max(lp, sl)
                self.trailing_stoploss = self.stoploss
                self.urisk = abs(self.entry - self.stoploss)
                self.pivot_status = PivotStatus.LPH_BREAK
                self.start_trailing = False
                self.log("Buy signal at : " + str(self.entry))
                self.buy(data=self.datas[self.p.acton])
                return

        elif self.pivot_status == PivotStatus.LPL_BREAK:
            # if self.new_5min_candle():
            #     if self.datas[min5].close[0] > self.entry:
            #         self.pivot_status = None
            #         self.exittype = "CAE"
            #         self.log("Exit signal at : " + str(low))
            #         self.close(data=self.datas[self.p.acton])
            #         self.start_trailing = False
            #         return

            if close > self.entry:
                self.pivot_status = None
                self.exittype = "CAE"
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            if high > self.trailing_stoploss:
                self.pivot_status = None
                self.log("Exit signal at : " + str(high))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            elif ltt >= self.square_off_time:
                self.pivot_status = None
                self.exittype = "Time"
                self.log("Exit signal at : " + str(high))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

        elif self.pivot_status == PivotStatus.LPH_BREAK:
            # if self.new_5min_candle():
            #     if self.datas[min5].close[0] < self.entry:
            #         self.pivot_status = None
            #         self.exittype = "CAE"
            #         self.log("Exit signal at : " + str(low))
            #         self.close(data=self.datas[self.p.acton])
            #         self.start_trailing = False
            #         return

            if close < self.entry:
                self.pivot_status = None
                self.exittype = "CAE"
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            if low < self.trailing_stoploss:
                self.pivot_status = None
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            elif ltt >= self.square_off_time:
                self.pivot_status = None
                self.exittype = "Time"
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

    def postnext(self):
        self.min5 = self.datas[min5].datetime.datetime(0)

        high = self.datas[min1].high[0]
        low = self.datas[min1].low[0]

        if self.pivot.new_lpl:
            if low < self.pivot.lpl_value:
                self.pivot.new_lpl = False

        if self.pivot.new_lph:
            if high > self.pivot.lph_value:
                self.pivot.new_lph = False

    def new_5min_candle(self):
        if self.min5:
            return True if self.datas[min5].datetime.datetime(0) > self.min5 else False
        else:
            return True


class MadanLive(Strategy):
    params = (
        ('trailoffset', 0),
        ('pct', pct),
        ('acton', 0),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_data(self, data, status, *args, **kwargs):

        if status == data.DELAYED:
            pass

        if status == data.LIVE:  # the data has switched to live data
            if not self.islive:
                self.islive = True

    def __init__(self):

        self.pivot = Pivots(self.datas[min5])
        self.atr = AverageTrueRange(self.datas[min5])
        self.pivot_status = None
        self.start_trailing = False
        self.islive = False
        self.last_entry_time = datetime.now().replace(hour=15, minute=10, second=0, microsecond=0).time()
        self.square_off_time = datetime.now().replace(hour=15, minute=15, second=0, microsecond=0).time()
        self.entry = None
        self.stoploss = None
        self.exittype = None
        self.trailing_stoploss = None
        self.urisk = None
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.min5 = False

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        if self.islive:
            self.mynext()
        self.postnext()

    def mynext(self):
        _open = self.datas[min1].open[0]
        high = self.datas[min1].high[0]
        low = self.datas[min1].low[0]
        close = self.datas[min1].close[0]
        ltt = self.datas[min1].datetime.time(0)
        ltts = self.datas[min1].datetime.datetime(0)

        if self.pivot_status:
            phigh, plow, pclose = self.datas[min5].high[-1], self.datas[min5].low[-1], self.datas[min5].close[-1]
            chigh, clow, cclose = self.datas[min5].high[0], self.datas[min5].low[0], self.datas[min5].close[0]

            if self.start_trailing:
                if self.pivot_status == PivotStatus.LPH_BREAK:
                    if (chigh > phigh) \
                            and (clow > plow) \
                            and (cclose > pclose) \
                            and (plow > self.trailing_stoploss):
                        self.trailing_stoploss = plow
                        self.exittype = "Trailing"

                elif self.pivot_status == PivotStatus.LPL_BREAK:
                    if (chigh < phigh) \
                            and (clow < plow) \
                            and (cclose < pclose) \
                            and (phigh < self.trailing_stoploss):
                        self.trailing_stoploss = phigh
                        self.exittype = "Trailing"

            elif not self.start_trailing:

                if self.p.trailoffset:
                    if self.pivot_status == PivotStatus.LPL_BREAK:
                        if chigh < (self.entry - self.p.trailoffset):
                            self.start_trailing = True

                    elif self.pivot_status == PivotStatus.LPH_BREAK:
                        if clow > (self.entry + self.p.trailoffset):
                            self.start_trailing = True

                else:
                    if self.pivot_status == PivotStatus.LPH_BREAK:
                        if cclose > self.entry:
                            self.start_trailing = True

                    elif self.pivot_status == PivotStatus.LPL_BREAK:
                        if cclose < self.entry:
                            self.start_trailing = True

        if self.pivot_status is None:

            if low < self.pivot.lpl_value and self.pivot.new_lpl and self.pivot.large_pivot == LPH:
                self.pivot.new_lpl = False

                if ltt >= self.last_entry_time:
                    return

                hp, hpx = self.pivot.sph_value, self.pivot.sph_index
                slice_of_high = self.datas[min5].high.get(ago=-1, size=abs(hpx + 1))
                for sliced_high in slice_of_high:
                    if sliced_high > hp:
                        hp = sliced_high

                if _open < self.pivot.lpl_value:
                    self.entry = _open
                else:
                    self.entry = self.pivot.lpl_value
                point_three_percent = self.p.pct * self.entry
                sl = round_up(self.entry + point_three_percent)
                self.exittype = "SPH" if hp < sl else ".3%"
                self.stoploss = min(hp, sl)
                self.trailing_stoploss = self.stoploss
                self.urisk = abs(self.entry - self.stoploss)
                self.pivot_status = PivotStatus.LPL_BREAK
                self.start_trailing = False
                self.log("Sell signal at : " + str(self.entry))
                self.sell(data=self.datas[self.p.acton])
                return

            elif high > self.pivot.lph_value and self.pivot.new_lph and self.pivot.large_pivot == LPL:
                self.pivot.new_lph = False

                if ltt >= self.last_entry_time:
                    return

                lp, lpx = self.pivot.spl_value, self.pivot.spl_index
                slice_of_low = self.datas[min5].low.get(ago=-1, size=abs(lpx + 1))
                for sliced_low in slice_of_low:
                    if sliced_low < lp:
                        lp = sliced_low

                if _open > self.pivot.lph_value:
                    self.entry = _open
                else:
                    self.entry = self.pivot.lph_value
                point_three_percent = self.p.pct * self.entry
                sl = round_down(self.entry - point_three_percent)
                self.exittype = "SPL" if lp > sl else ".3%"
                self.stoploss = max(lp, sl)
                self.trailing_stoploss = self.stoploss
                self.urisk = abs(self.entry - self.stoploss)
                self.pivot_status = PivotStatus.LPH_BREAK
                self.start_trailing = False
                self.log("Buy signal at : " + str(self.entry))
                self.buy(data=self.datas[self.p.acton])
                return

        elif self.pivot_status == PivotStatus.LPL_BREAK:
            # if self.new_5min_candle():
            #     if self.datas[min5].close[0] > self.entry:
            #         self.pivot_status = None
            #         self.exittype = "CAE"
            #         self.log("Exit signal at : " + str(low))
            #         self.close(data=self.datas[self.p.acton])
            #         self.start_trailing = False
            #         return

            if close > self.entry:
                self.pivot_status = None
                self.exittype = "CAE"
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            if high > self.trailing_stoploss:
                self.pivot_status = None
                self.log("Exit signal at : " + str(high))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            elif ltt >= self.square_off_time:
                self.pivot_status = None
                self.exittype = "Time"
                self.log("Exit signal at : " + str(high))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

        elif self.pivot_status == PivotStatus.LPH_BREAK:
            # if self.new_5min_candle():
            #     if self.datas[min5].close[0] < self.entry:
            #         self.pivot_status = None
            #         self.exittype = "CAE"
            #         self.log("Exit signal at : " + str(low))
            #         self.close(data=self.datas[self.p.acton])
            #         self.start_trailing = False
            #         return

            if close < self.entry:
                self.pivot_status = None
                self.exittype = "CAE"
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            if low < self.trailing_stoploss:
                self.pivot_status = None
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            elif ltt >= self.square_off_time:
                self.pivot_status = None
                self.exittype = "Time"
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

    def postnext(self):
        self.min5 = self.datas[min5].datetime.datetime(0)

        high = self.datas[min1].high[0]
        low = self.datas[min1].low[0]

        if self.pivot.new_lpl:
            if low < self.pivot.lpl_value:
                self.pivot.new_lpl = False

        if self.pivot.new_lph:
            if high > self.pivot.lph_value:
                self.pivot.new_lph = False

    def new_5min_candle(self):
        if self.min5:
            return True if self.datas[min5].datetime.datetime(0) > self.min5 else False
        else:
            return True


class MadanTest(Strategy):
    params = (
        ('trailoffset', 0),
        ('pct', pct),
        ('acton', 0),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        # self.pivot = Pivots(self.datas[min5])
        # self.atr = AverageTrueRange(self.datas[min5])
        self.pivot_status = None
        self.start_trailing = False

        self.last_entry_time = datetime.now().replace(hour=15, minute=10, second=0, microsecond=0).time()
        self.square_off_time = datetime.now().replace(hour=15, minute=15, second=0, microsecond=0).time()
        self.entry = None
        self.stoploss = None
        self.exittype = None
        self.trailing_stoploss = None
        self.urisk = None
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.min5 = False

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        print("~" * 300)
        print(self.datas[1].datetime.datetime(0), self.datas[0].open[0], self.datas[0].high[0], self.datas[0].low[0],
              self.datas[0].close[0])
        print(self.datas[2].datetime.datetime(0), self.datas[2].open[0], self.datas[2].high[0], self.datas[2].low[0],
              self.datas[2].close[0])

    def mynext(self):
        _open = self.datas[min1].open[0]
        high = self.datas[min1].high[0]
        low = self.datas[min1].low[0]
        close = self.datas[min1].close[0]
        ltt = self.datas[min1].datetime.time(0)
        ltts = self.datas[min1].datetime.datetime(0)

        if self.pivot_status:
            phigh, plow, pclose = self.datas[min5].high[-1], self.datas[min5].low[-1], self.datas[min5].close[-1]
            chigh, clow, cclose = self.datas[min5].high[0], self.datas[min5].low[0], self.datas[min5].close[0]

            if self.start_trailing:
                if self.pivot_status == PivotStatus.LPH_BREAK:
                    if (chigh > phigh) \
                            and (clow > plow) \
                            and (cclose > pclose) \
                            and (plow > self.trailing_stoploss):
                        self.trailing_stoploss = plow
                        self.exittype = "Trailing"

                elif self.pivot_status == PivotStatus.LPL_BREAK:
                    if (chigh < phigh) \
                            and (clow < plow) \
                            and (cclose < pclose) \
                            and (phigh < self.trailing_stoploss):
                        self.trailing_stoploss = phigh
                        self.exittype = "Trailing"

            elif not self.start_trailing:

                if self.p.trailoffset:
                    if self.pivot_status == PivotStatus.LPL_BREAK:
                        if chigh < (self.entry - self.p.trailoffset):
                            self.start_trailing = True

                    elif self.pivot_status == PivotStatus.LPH_BREAK:
                        if clow > (self.entry + self.p.trailoffset):
                            self.start_trailing = True

                else:
                    if self.pivot_status == PivotStatus.LPH_BREAK:
                        if cclose > self.entry:
                            self.start_trailing = True

                    elif self.pivot_status == PivotStatus.LPL_BREAK:
                        if cclose < self.entry:
                            self.start_trailing = True

        if self.pivot_status is None:

            if low < self.pivot.lpl_value and self.pivot.new_lpl and self.pivot.large_pivot == LPH:
                self.pivot.new_lpl = False

                if ltt >= self.last_entry_time:
                    return

                hp, hpx = self.pivot.sph_value, self.pivot.sph_index
                slice_of_high = self.datas[min5].high.get(ago=-1, size=abs(hpx + 1))
                for sliced_high in slice_of_high:
                    if sliced_high > hp:
                        hp = sliced_high

                if _open < self.pivot.lpl_value:
                    self.entry = _open
                else:
                    self.entry = self.pivot.lpl_value
                point_three_percent = self.p.pct * self.entry
                sl = round_up(self.entry + point_three_percent)
                self.exittype = "SPH" if hp < sl else ".3%"
                self.stoploss = min(hp, sl)
                self.trailing_stoploss = self.stoploss
                self.urisk = abs(self.entry - self.stoploss)
                self.pivot_status = PivotStatus.LPL_BREAK
                self.start_trailing = False
                self.log("Sell signal at : " + str(self.entry))
                self.sell(data=self.datas[self.p.acton])
                return

            elif high > self.pivot.lph_value and self.pivot.new_lph and self.pivot.large_pivot == LPL:
                self.pivot.new_lph = False

                if ltt >= self.last_entry_time:
                    return

                lp, lpx = self.pivot.spl_value, self.pivot.spl_index
                slice_of_low = self.datas[min5].low.get(ago=-1, size=abs(lpx + 1))
                for sliced_low in slice_of_low:
                    if sliced_low < lp:
                        lp = sliced_low

                if _open > self.pivot.lph_value:
                    self.entry = _open
                else:
                    self.entry = self.pivot.lph_value
                point_three_percent = self.p.pct * self.entry
                sl = round_down(self.entry - point_three_percent)
                self.exittype = "SPL" if lp > sl else ".3%"
                self.stoploss = max(lp, sl)
                self.trailing_stoploss = self.stoploss
                self.urisk = abs(self.entry - self.stoploss)
                self.pivot_status = PivotStatus.LPH_BREAK
                self.start_trailing = False
                self.log("Buy signal at : " + str(self.entry))
                self.buy(data=self.datas[self.p.acton])
                return

        elif self.pivot_status == PivotStatus.LPL_BREAK:
            # if self.new_5min_candle():
            #     if self.datas[min5].close[0] > self.entry:
            #         self.pivot_status = None
            #         self.exittype = "CAE"
            #         self.log("Exit signal at : " + str(low))
            #         self.close(data=self.datas[self.p.acton])
            #         self.start_trailing = False
            #         return

            if close > self.entry:
                self.pivot_status = None
                self.exittype = "CAE"
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            if high > self.trailing_stoploss:
                self.pivot_status = None
                self.log("Exit signal at : " + str(high))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            elif ltt >= self.square_off_time:
                self.pivot_status = None
                self.exittype = "Time"
                self.log("Exit signal at : " + str(high))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

        elif self.pivot_status == PivotStatus.LPH_BREAK:
            # if self.new_5min_candle():
            #     if self.datas[min5].close[0] < self.entry:
            #         self.pivot_status = None
            #         self.exittype = "CAE"
            #         self.log("Exit signal at : " + str(low))
            #         self.close(data=self.datas[self.p.acton])
            #         self.start_trailing = False
            #         return

            if close < self.entry:
                self.pivot_status = None
                self.exittype = "CAE"
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            if low < self.trailing_stoploss:
                self.pivot_status = None
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

            elif ltt >= self.square_off_time:
                self.pivot_status = None
                self.exittype = "Time"
                self.log("Exit signal at : " + str(low))
                self.close(data=self.datas[self.p.acton])
                self.start_trailing = False
                return

    def postnext(self):
        self.min5 = self.datas[min5].datetime.datetime(0)

        high = self.datas[min1].high[0]
        low = self.datas[min1].low[0]

        if self.pivot.new_lpl:
            if low < self.pivot.lpl_value:
                self.pivot.new_lpl = False

        if self.pivot.new_lph:
            if high > self.pivot.lph_value:
                self.pivot.new_lph = False

    def new_5min_candle(self):
        if self.min5:
            return True if self.datas[min5].datetime.datetime(0) > self.min5 else False
        else:
            return True
