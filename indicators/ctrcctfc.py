from shiksha import *

(BULL, BEAR) = range(2)
HOUSES = ["BULL", "BEAR"]
(BULLPORCH, BEARPORCH, BULLHOUSE, BEARHOUSE, BULLHOUSEMAXRET, BEARHOUSEMAXRET) = range(6)
STATES = ["BULLPORCH", "BEARPORCH", "BULLHOUSE", "BEARHOUSE", "BULLHOUSEMAXRET", "BEARHOUSEMAXRET"]


class House(Indicator):
    lines = ("bull", "bear")
    params = dict()
    plotinfo = dict(subplot=False)
    plotlines = dict(
        bull=dict(marker='^', markersize=8.0, color='red', fillstyle='full', ),
        bear=dict(marker='v', markersize=8.0, color='blue', fillstyle='full', ),
    )

    def __init__(self):
        self.fibo = Fibo(self.datas[1], replay=True)
        self.house = None
        self.state = None
        self.bullhigh, self.bearlow = None, None
        self.event = False
        self.waitfornextday = False
        self.lastday = None
        self.addminperiod(375 * 2)

    def setstate(self, state):
        self.state = state
        self.event = True
        self.waitfornextday = True

    def next(self):

        day = self.datas[0].datetime.date(0)
        datetime = str(self.datas[0].datetime.datetime(0))
        if datetime == "2020-02-14 13:20:00":
            pass
        if self.waitfornextday:
            if self.lastday and day == self.lastday:
                self.event = False
                if self.bullhigh and self.datas[0].high[0] > self.bullhigh:
                    self.bullhigh = self.bull[0] = self.datas[0].high[0]
                if self.bearlow and self.datas[0].low[0] < self.bearlow:
                    self.bearlow = self.bear[0] = self.datas[0].low[0]
                return

        self.waitfornextday = False
        self.lastday = day

        if self.state == BULLPORCH:
            if self.fibo.traded_above(self.datas[0].high[0], self.bullhigh, 1):
                self.setstate(BULLHOUSE)
                self.house = BULL
                self.bullhigh = None

            if "Cutting The Flying Kite" in self.fibo.theory:
                if self.datas[0].low[0] < self.fibo.lsfc100:
                    self.setstate(BEARPORCH)
                    self.bearlow = self.bear[0] = self.datas[0].low[0]

        elif self.state == BEARPORCH:
            if self.fibo.traded_below(self.datas[0].low[0], self.bearlow, -1):
                self.setstate(BEARHOUSE)
                self.house = BEAR
                self.bearlow = None

            if "Catching The Falling Knife" in self.fibo.theory:
                if self.datas[0].high[0] > self.fibo.hsrc100:
                    self.setstate(BULLPORCH)
                    self.bullhigh = self.bull[0] = self.datas[0].high[0]

        elif self.state == BULLHOUSE:
            if "Cutting The Flying Kite" in self.fibo.theory:
                if self.datas[0].low[0] < self.fibo.lsfc100:
                    self.setstate(BEARPORCH)
                    self.bearlow = self.bear[0] = self.datas[0].low[0]

        elif self.state == BEARHOUSE:
            if "Catching The Falling Knife" in self.fibo.theory:
                if self.datas[0].high[0] > self.fibo.hsrc100:
                    self.setstate(BULLPORCH)
                    self.bullhigh = self.bull[0] = self.datas[0].high[0]
        else:
            if "Catching The Falling Knife" in self.fibo.theory:
                if self.datas[0].high[0] > self.fibo.hsrc100:
                    self.setstate(BULLPORCH)
                    self.bullhigh = self.bull[0] = self.datas[0].high[0]
            if "Cutting The Flying Kite" in self.fibo.theory:
                if self.datas[0].low[0] < self.fibo.lsfc100:
                    self.setstate(BEARPORCH)
                    self.bearlow = self.bear[0] = self.datas[0].low[0]


class HouseOnDay(Indicator):
    lines = ("bull", "bear")
    params = dict()
    plotinfo = dict(subplot=False)
    plotlines = dict(
        bull=dict(marker='^', markersize=8.0, color='red', fillstyle='full', ),
        bear=dict(marker='v', markersize=8.0, color='blue', fillstyle='full', ),
    )

    def __init__(self):
        self.fibo = Fibo(self.datas[0], replay=False)
        self.house = None
        self.state = None
        self.bullhigh, self.bearlow = None, None
        self.event = False

    def setstate(self, state):
        self.state = state
        self.event = True

    def next(self):

        self.event = False
        if self.state == BULLPORCH:
            if self.fibo.traded_above(self.datas[0].high[0], self.bullhigh, 1):
                self.setstate(BULLHOUSE)
                self.house = BULL
                self.bullhigh = None

            if "Cutting The Flying Kite" in self.fibo.theory:
                if self.datas[0].low[0] < self.fibo.lsfc100:
                    self.setstate(BEARPORCH)
                    self.bearlow = self.bear[0] = self.datas[0].low[0]

            if "Catching The Falling Knife" in self.fibo.theory:
                if self.datas[0].high[0] > self.fibo.hsrc100:
                    self.setstate(BULLPORCH)
                    self.bullhigh = self.bull[0] = self.datas[0].high[0]

        elif self.state == BEARPORCH:
            if self.fibo.traded_below(self.datas[0].low[0], self.bearlow, -1):
                self.setstate(BEARHOUSE)
                self.house = BEAR
                self.bearlow = None

            if "Catching The Falling Knife" in self.fibo.theory:
                if self.datas[0].high[0] > self.fibo.hsrc100:
                    self.setstate(BULLPORCH)
                    self.bullhigh = self.bull[0] = self.datas[0].high[0]

            if "Cutting The Flying Kite" in self.fibo.theory:
                if self.datas[0].low[0] < self.fibo.lsfc100:
                    self.setstate(BEARPORCH)
                    self.bearlow = self.bear[0] = self.datas[0].low[0]

        elif self.state == BULLHOUSE:
            if "Cutting The Flying Kite" in self.fibo.theory:
                if self.datas[0].low[0] < self.fibo.lsfc100:
                    self.setstate(BEARPORCH)
                    self.bearlow = self.bear[0] = self.datas[0].low[0]

        elif self.state == BEARHOUSE:
            if "Catching The Falling Knife" in self.fibo.theory:
                if self.datas[0].high[0] > self.fibo.hsrc100:
                    self.setstate(BULLPORCH)
                    self.bullhigh = self.bull[0] = self.datas[0].high[0]
        else:
            if "Catching The Falling Knife" in self.fibo.theory:
                if self.datas[0].high[0] > self.fibo.hsrc100:
                    self.setstate(BULLPORCH)
                    self.bullhigh = self.bull[0] = self.datas[0].high[0]
            if "Cutting The Flying Kite" in self.fibo.theory:
                if self.datas[0].low[0] < self.fibo.lsfc100:
                    self.setstate(BEARPORCH)
                    self.bearlow = self.bear[0] = self.datas[0].low[0]
