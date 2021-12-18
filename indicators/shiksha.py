import pandas as pd
from backtrader import Indicator
from math import isnan

plotskip = dict(_plotskip=True)

director_pattern_map = {
    1: '2+2',
    2: '3+1',
    3: '2+1'
}
con = 0.382  # Fibonacci constant value 38.2/100 = 0.382

# Trending Leg
trending_leg_names = {
    0: 'NOTREND',
    1: 'ITRB',
    2: 'VTRB',
    3: 'UTC',
    4: 'ITRS',
    7: 'ICS',
    8: 'VCS',
    9: 'IPBB',
    10: 'VPBB',
    11: 'ICSCOUB',
    12: 'VCSCOUB',
    13: 'CSCOUB-C',
    14: 'IPBCODB',
    15: 'VPBCODB',
    16: 'PBCODB-C'
}
trending_leg_colors = {
    0: '#ffffff',
    1: '#3bc63b',
    2: '#3bc63b',
    3: '#055905',
    4: '#d54c4c',
    5: '#d54c4c',
    6: '#ff0000',
    7: '#1b06dc',
    8: '#1b06dc',
    9: '#654321', 5: 'VTRS',
    6: 'DTC',

    10: '#654321',
    11: '#3bc63b',
    12: '#3bc63b',
    13: '#055905',
    14: '#d54c4c',
    15: '#d54c4c',
    16: '#ff0000'
}

# Move
up, down = "up", "down"
moves = {
    0: "no move",
    1: "up move",
    2: "down move",
    3: "up move begins",
    4: "down move begins",
}

# Rar
VB, VS = "Valid Buy", "Valid Sell"
GAS, WBS = "Good Above Series", "Weak Below Series"
series = {
    1: "Good Above Series - Occur",
    2: "Good Above Series - Justified",
    3: "Good Above Series - Inactive",
    4: "Good Above Series - Reactive",
    5: "Weak Below Series - Occur",
    6: "Weak Below Series - Justified",
    7: "Weak Below Series - Inactive",
    8: "Weak Below Series - Reactive",
}

# GAP
PCHG, PCLG, PCNOHG, PCNOLG = "PCHG", "PCLG", "PCNOHG", "PCNOLG"


def do_nothing(): pass


def name_moves(key):
    try:
        return moves[key]
    except KeyError:
        return moves[0]


class Fibo(Indicator):
    lines = ('_bdp', '_wdp', '_trending_leg')
    params = dict(daily=True, replay=False)
    plotinfo = dict(subplot=False)
    plotlines = dict(
        _bdp=dict(marker='_', markersize=8.0, color='red', fillstyle='full', ),
        _wdp=dict(marker='_', markersize=8.0, color='blue', fillstyle='full', ),
    )

    def __init__(self):
        minperiod = 2 if self.p.replay else 3
        self.addminperiod(minperiod)
        self.prevlen = None

    def next(self):

        ltt = self.data0.datetime.datetime(0)

        _len = len(self)
        if self.prevlen and _len == self.prevlen:
            return

        self.prevlen = _len

        if self.p.replay:
            self.close_1 = self.data0.close[0]
            self.high_1 = self.data0.high[0]
            self.low_1 = self.data0.low[0]
            self.high_2 = self.data0.high[-1]
            self.low_2 = self.data0.low[-1]
        else:
            self.close_1 = self.data0.close[-1]
            self.high_1 = self.data0.high[-1]
            self.low_1 = self.data0.low[-1]
            self.high_2 = self.data0.high[-2]
            self.low_2 = self.data0.low[-2]
            self.high = self.data0.high[0]
            self.low = self.data0.low[0]

        self.hhigh = max(self.high_1, self.high_2)
        self.llow = min(self.low_1, self.low_2)

        self.range = self.high_1 - self.low_1  # Range of current candle
        self.previous_range = self.high_2 - self.low_2  # Range of previous candle
        self.cjgd = self.high_1 - (self.range * con)  # JGD of current candle
        self.cjwd = self.low_1 + (self.range * con)  # JWD of current candle
        self.pjgd = self.high_2 - (self.previous_range * con)  # JGD of previous candle
        self.pjwd = self.low_2 + (self.previous_range * con)  # JWD of previous candle

        self.bdp = max(self.cjgd, self.pjgd)  # BDP of pair
        self.wdp = min(self.cjwd, self.pjwd)  # WDP of pair

        self._bdp[0] = self.bdp
        self._wdp[0] = self.wdp

        self.jgd = min(self.cjgd, self.pjgd)  # JGD of pair
        self.jwd = max(self.cjwd, self.pjwd)  # JWD of pair

        self.nbdp = float(self.bdp + (self.range * 0.146))
        self.nwdp = float(self.wdp - (self.range * 0.146))

        if self.cjgd > self.pjwd and self.cjwd > self.pjwd:
            self.director_pattern = 1
        elif self.cjgd < self.pjwd and self.cjwd < self.pjwd:
            self.director_pattern = 2
        elif self.cjgd >= self.pjwd >= self.cjwd:
            self.director_pattern = 3

        self.active = 0.118 if self.p.daily else 0.146
        self.f = 0 if self.p.daily else self.close_1 * 0.00073
        self.buffer = (self.range * 0.073) + (self.close_1 * 0.00073)

        # Absolute values of Rising channel
        self.rc_active = round(self.close_1 + (self.range * self.active), 2)
        self.rc23 = round(self.close_1 + (self.range * 0.236), 2)
        self.rc38 = round(self.close_1 + (self.range * 0.382), 2)
        self.rc61 = round(self.close_1 + (self.range * 0.618), 2)
        self.rc100 = round(self.close_1 + self.range, 2)
        self.rc127 = round(self.close_1 + (self.range * 1.272), 2)
        self.rc161 = round(self.close_1 + (self.range * 1.618), 2)
        self.rc261 = round(self.close_1 + (self.range * 2.618), 2)
        self.rc423 = round(self.close_1 + (self.range * 4.236), 2)
        self.rc_kiss = round(self.rc_active - self.buffer, 2)

        # Absolute values of Falling channel
        self.fc_active = round(self.close_1 - (self.range * self.active), 2)
        self.fc23 = round(self.close_1 - (self.range * 0.236), 2)
        self.fc38 = round(self.close_1 - (self.range * 0.382), 2)
        self.fc61 = round(self.close_1 - (self.range * 0.618), 2)
        self.fc100 = round(self.close_1 - self.range, 2)
        self.fc127 = round(self.close_1 - (self.range * 1.272), 2)
        self.fc161 = round(self.close_1 - (self.range * 1.618), 2)
        self.fc261 = round(self.close_1 - (self.range * 2.618), 2)
        self.fc423 = round(self.close_1 - (self.range * 4.236), 2)
        self.fc_kiss = round(self.fc_active + self.buffer, 2)

        # TVHS of Rising channel
        self.hsrc_active = round(self.rc_active + (((self.rc23 - self.rc_active) * con) + self.f), 2)
        self.hsrc23 = round(self.rc23 + (((self.rc38 - self.rc23) * con) + self.f), 2)
        self.hsrc38 = round(self.rc38 + (((self.rc61 - self.rc38) * con) + self.f), 2)
        self.hsrc61 = round(self.rc61 + (((self.rc100 - self.rc61) * con) + self.f), 2)
        self.hsrc100 = round(self.rc100 + (((self.rc127 - self.rc100) * con) + self.f), 2)
        self.hsrc127 = round(self.rc127 + (((self.rc161 - self.rc127) * con) + self.f), 2)
        self.hsrc161 = round(self.rc161 + (((self.rc261 - self.rc161) * con) + self.f), 2)
        self.hsrc261 = round(self.rc261 + (((self.rc423 - self.rc261) * con) + self.f), 2)
        self.hsrc423 = round(self.close_1 + ((self.range * 6.854) + self.f), 2)

        # TVLS of Rising channel
        self.lsrc_active = round(self.rc_active - (((self.rc_active - self.fc_active) * con) + self.f), 2)
        self.lsrc23 = round(self.rc23 - (((self.rc23 - self.rc_active) * con) + self.f), 2)
        self.lsrc38 = round(self.rc38 - (((self.rc38 - self.rc23) * con) + self.f), 2)
        self.lsrc61 = round(self.rc61 - (((self.rc61 - self.rc38) * con) + self.f), 2)
        self.lsrc100 = round(self.rc100 - (((self.rc100 - self.rc61) * con) + self.f), 2)
        self.lsrc127 = round(self.rc127 - (((self.rc127 - self.rc100) * con) + self.f), 2)
        self.lsrc161 = round(self.rc161 - (((self.rc161 - self.rc127) * con) + self.f), 2)
        self.lsrc261 = round(self.rc261 - (((self.rc261 - self.rc161) * con) + self.f), 2)
        self.lsrc423 = round(self.rc423 - (((self.rc423 - self.rc261) * con) + self.f), 2)

        # TVHS of Falling Channel
        self.hsfc_active = round(self.fc_active + (((self.rc_active - self.fc_active) * con) + self.f), 2)
        self.hsfc23 = round(self.fc23 + (((self.fc_active - self.fc23) * con) + self.f), 2)
        self.hsfc38 = round(self.fc38 + (((self.fc23 - self.fc38) * con) + self.f), 2)
        self.hsfc61 = round(self.fc61 + (((self.fc38 - self.fc61) * con) + self.f), 2)
        self.hsfc100 = round(self.fc100 + (((self.fc61 - self.fc100) * con) + self.f), 2)
        self.hsfc127 = round(self.fc127 + (((self.fc100 - self.fc127) * con) + self.f), 2)
        self.hsfc161 = round(self.fc161 + (((self.fc127 - self.fc161) * con) + self.f), 2)
        self.hsfc261 = round(self.fc261 + (((self.fc161 - self.fc261) * con) + self.f), 2)
        self.hsfc423 = round(self.fc423 + (((self.fc261 - self.fc423) * con) + self.f), 2)

        # TVLS of Falling Channel
        self.lsfc_active = round(self.fc_active - (((self.fc_active - self.fc23) * con) + self.f), 2)
        self.lsfc23 = round(self.fc23 - (((self.fc23 - self.fc38) * con) + self.f), 2)
        self.lsfc38 = round(self.fc38 - (((self.fc38 - self.fc61) * con) + self.f), 2)
        self.lsfc61 = round(self.fc61 - (((self.fc61 - self.fc100) * con) + self.f), 2)
        self.lsfc100 = round(self.fc100 - (((self.fc100 - self.fc127) * con) + self.f), 2)
        self.lsfc127 = round(self.fc127 - (((self.fc127 - self.fc161) * con) + self.f), 2)
        self.lsfc161 = round(self.fc161 - (((self.fc161 - self.fc261) * con) + self.f), 2)
        self.lsfc261 = round(self.fc261 - (((self.fc261 - self.fc423) * con) + self.f), 2)
        self.lsfc423 = round(self.close_1 - ((self.range * 6.854) + self.f), 2)

        # Collection of channels in a Dictionary
        self.rc_kv = {"rc_active": self.rc_active, "rc38": self.rc38, "rc61": self.rc61,
                      "rc100": self.rc100, "rc127": self.rc127, "rc161": self.rc161, "rc261": self.rc261,
                      "rc423": self.rc423}
        self.hsrc_kv = {"hsrc_active": self.hsrc_active, "hsrc38": self.hsrc38, "hsrc61": self.hsrc61,
                        "hsrc100": self.hsrc100, "hsrc127": self.hsrc127, "hsrc161": self.hsrc161,
                        "hsrc261": self.hsrc261, "hsrc423": self.hsrc423}
        self.lsrc_kv = {"lsrc_active": self.lsrc_active, "lsrc38": self.lsrc38, "lsrc61": self.lsrc61,
                        "lsrc100": self.lsrc100, "lsrc127": self.lsrc127, "lsrc161": self.lsrc161,
                        "lsrc261": self.lsrc261, "lsrc423": self.lsrc423}
        self.fc_kv = {"fc_active": self.fc_active, "fc38": self.fc38, "fc61": self.fc61,
                      "fc100": self.fc100, "fc127": self.fc127, "fc161": self.fc161, "fc261": self.fc261,
                      "fc423": self.fc423}
        self.hsfc_kv = {"hsfc_active": self.hsfc_active, "hsfc38": self.hsfc38, "hsfc61": self.hsfc61,
                        "hsfc100": self.hsfc100, "hsfc127": self.hsfc127, "hsfc161": self.hsfc161,
                        "hsfc261": self.hsfc261, "hsfc423": self.hsfc423}
        self.lsfc_kv = {"lsfc_active": self.lsfc_active, "lsfc38": self.lsfc38, "lsfc61": self.lsfc61,
                        "lsfc100": self.lsfc100, "lsfc127": self.lsfc127, "lsfc161": self.lsfc161,
                        "lsfc261": self.lsfc261, "lsfc423": self.lsfc423}
        self.fork_kv = self.rc_kv.copy()
        self.fork_kv.update(self.fc_kv)
        self.hs_fork_kv = self.hsrc_kv.copy()
        self.hs_fork_kv.update(self.hsfc_kv)
        self.ls_fork_kv = self.lsrc_kv.copy()
        self.ls_fork_kv.update(self.lsfc_kv)

        # Collection of channels in a List
        self.rc = list(self.rc_kv.values())
        self.hsrc = list(self.hsrc_kv.values())
        self.lsrc = list(self.lsrc_kv.values())
        self.fc = list(self.fc_kv.values())
        self.hsfc = list(self.hsfc_kv.values())
        self.lsfc = list(self.lsfc_kv.values())
        self.fork = sorted(list(self.fork_kv.values()))
        self.hs_fork = sorted(list(self.hs_fork_kv.values()))
        self.ls_fork = sorted(list(self.ls_fork_kv.values()))

        self.support_name = None
        self.support_value = None
        self.climbing_buy_name = None
        self.climbing_buy_value = None

        self.resistance_name = None
        self.resistance_value = None
        self.drifting_sell_name = None
        self.drifting_sell_value = None

        self.upperband = self.upper_band()
        self.lowerband = self.lower_band()
        self.abs_upperband = self.rc38 if self.upperband == self.hsrc38 else self.rc61
        self.abs_lowerband = self.fc38 if self.lowerband == self.lsfc38 else self.fc61
        self.theory = self.find_theory()
        self.trend = self.find_trend()

        if not self.p.replay:
            self.prev_trending_leg = self._trending_leg[-1]
            self.current_trending_leg = self.get_trending_leg()
            self._trending_leg[0] = self.current_trending_leg

    def get_level(self, price, levels=1):
        if levels == 0:
            return None, price
        else:
            price_appended = False
            if price not in self.fork:
                self.fork.append(price)
                price_appended = True
            self.fork.sort()
            prefix = "hs" if levels > 0 else "ls"
            idx = self.fork.index(price) + levels
            level_name, level_value = None, None
            try:
                idx_val = self.fork[idx]
                level_name = prefix + self.get_name(idx_val, [self.fork_kv])
                level_value = self.__getattribute__(level_name)

            except Exception:
                if levels > 0:  # and price > self.rc423:
                    level_name, level_value = 'hsrc423', self.hsrc423
                elif levels < 0:  # and price < self.fc423:
                    level_name, level_value = 'lsfc423', self.lsfc423

            self.fork.remove(price) if price_appended else do_nothing()
            return level_name, level_value

    def get_level_traded_higher_side(self, high):
        if high not in self.hs_fork:
            self.hs_fork.append(high)
        self.hs_fork.sort()
        level_value = self.hs_fork[self.hs_fork.index(high) - 1]
        level_name = list(self.hs_fork_kv.keys())[
            list(self.hs_fork_kv.values()).index(level_value)]
        self.hs_fork.remove(high)
        return level_name, level_value

    def get_level_traded_lower_side(self, low):
        if low not in self.ls_fork:
            self.ls_fork.append(low)
        self.ls_fork.sort()
        level_value = self.ls_fork[self.ls_fork.index(low) + 1]
        level_name = list(self.ls_fork_kv.keys())[
            list(self.ls_fork_kv.values()).index(level_value)]
        self.ls_fork.remove(low)
        return level_name, level_value

    def support(self, price, level=-2):
        self.support_name, self.support_value = self.get_level(price, levels=level)
        return self.support_name, self.support_value

    def climbing_buy(self, price, level=1):
        self.climbing_buy_name, self.climbing_buy_value = self.get_level(price, levels=level)
        return self.climbing_buy_name, self.climbing_buy_value

    def resistance(self, price, level=2):
        self.resistance_name, self.resistance_value = self.get_level(price, levels=level)
        return self.resistance_name, self.resistance_value

    def drifting_sell(self, price, level=-1):
        self.drifting_sell_name, self.drifting_sell_value = self.get_level(price, levels=level)
        return self.drifting_sell_name, self.drifting_sell_value

    def get_name(self, price, fork_kv_list=None):
        name = None
        fork_list = [self.hs_fork_kv, self.ls_fork_kv, self.fork_kv] if fork_kv_list is None else fork_kv_list
        for dictionary in fork_list:
            if price in dictionary.values():
                idx = list(dictionary.values()).index(price)
                name = list(dictionary.keys())[idx]
                break
        return name

    def nomenclate(self):
        self.support_name = self.get_name(self.support_value)
        self.climbing_buy_name = self.get_name(self.climbing_buy_value)
        self.resistance_name = self.get_name(self.resistance_value)
        self.drifting_sell_name = self.get_name(self.drifting_sell_value)

    def log(self, message):
        self.snr_log.append(message)

    def update_event_dictionary(self):
        self.event_dictionary = {self.support_value: 'S&R to Sell at {}'.format(self.support_name),
                                 self.climbing_buy_value: 'CB Traded at {}'.format(self.climbing_buy_name),
                                 self.resistance_value: 'S&R to Buy at {}'.format(self.resistance_name),
                                 self.drifting_sell_value: 'DS Traded at {}'.format(self.drifting_sell_name)}
        return self.event_dictionary

    def find_trend(self):
        if self.fc38 <= self.bdp < self.rc38 and self.wdp < self.fc38:
            trend = 'up trend'
        elif self.fc38 < self.wdp <= self.rc38 and self.bdp > self.rc38:
            trend = 'down trend'
        else:
            trend = 'both trend'
        return trend

    def upper_band(self):
        ub = self.hsrc38
        for a in [self.bdp, self.jgd]:
            if self.rc61 > a > self.rc38:
                ub = self.hsrc61
                break
        return ub

    def lower_band(self):
        lb = self.lsfc38
        for a in [self.wdp, self.jwd]:
            if self.fc61 < a < self.fc38:
                lb = self.lsfc61
                break
        return lb

    def icrc(self, or_high, or_low):
        return True if self.hsrc_active < or_high <= self.upperband and or_low >= self.lsfc_active else False

    def icfc(self, or_high, or_low):
        return True if self.lsfc_active > or_low >= self.lowerband and or_high <= self.hsrc_active else False

    def rmsl_high(self, or_high, or_low):
        return True if or_high > self.upperband and or_low >= self.lowerband else False

    def rmsl_low(self, or_high, or_low):
        return True if or_low < self.lowerband and or_high <= self.upperband else False

    def icrr(self, or_high, or_low):
        return True if or_low >= self.lsfc_active and or_high <= self.hsrc_active else False

    def higher_gap(self, or_low):
        return True if or_low > self.nbdp else False

    def lower_gap(self, or_high):
        return True if or_high < self.nwdp else False

    def rmsl_higher_gap(self, or_high, or_low):
        return True if self.rmsl_high(or_high, or_low) and self.higher_gap(or_low) else False

    def rmsl_lower_gap(self, or_high, or_low):
        return True if self.rmsl_low(or_high, or_low) and self.lower_gap(or_high) else False

    def how(self, or_high, or_low, or_close):

        self.open_type = ""

        def guess_direction():
            close2high, close2low = or_high - or_close, or_close - or_low
            return up if close2high > close2low else down

        if or_high > self.upperband and or_low < self.lowerband:
            self.open_type += "RMSL-HIGH " if guess_direction() == up else "RMSL-LOW "
        elif self.rmsl_high(or_high, or_low):
            self.open_type += "RMSL-HIGH "
            if or_close < self.lsrc38:
                self.open_type += "Close < LSRC38 "
        elif self.rmsl_low(or_high, or_low):
            self.open_type += "RMSL-LOW "
            if or_close > self.hsfc38:
                self.open_type += "Close > HSFC38 "
        elif or_high > self.hsrc_active and or_low < self.lsfc_active:
            self.open_type += "ICRC " if guess_direction() == up else "ICFC "
        elif self.icrc(or_high, or_low):
            self.open_type += "ICRC "
        elif self.icfc(or_high, or_low):
            self.open_type += "ICFC "
        elif self.icrr(or_high, or_low):
            self.open_type += "ICRR "

        if self.higher_gap(or_low):
            self.open_type += "HIGHER-GAP "
        elif self.lower_gap(or_high):
            self.open_type += "LOWER-GAP "

        return self.open_type

    def sleeping_beauty(self):
        return True if self.fc_active >= self.bdp >= self.fc38 else False

    def reverse_sleeping_beauty(self):
        return True if self.rc38 >= self.wdp >= self.rc_active else False

    def bdp_in_icrr(self):
        return True if self.rc_active > self.bdp > self.fc_active else False

    def wdp_in_icrr(self):
        return True if self.rc_active > self.wdp > self.fc_active else False

    def knock_knock_in_rc(self):
        return True if self.rc38 >= self.bdp >= self.rc_active else False

    def knock_knock_in_fc(self):
        return True if self.fc_active >= self.wdp >= self.fc38 else False

    def cut_cut_pack_up_in_rc(self):
        return True if self.rc61 >= self.bdp > self.rc38 else False

    def cut_cut_pack_up_in_fc(self):
        return True if self.fc38 > self.wdp >= self.fc61 else False

    def cutting_the_flying_kite(self):
        return True if self.rc100 >= self.bdp > self.rc61 else False  # self.director_pattern == "3+1" and

    def catching_the_falling_knife(self):
        return True if self.fc61 > self.wdp >= self.fc100 else False  # self.director_pattern == "2+2" and

    def bdp_above_rc100(self):
        return True if self.bdp > self.rc100 else False

    def wdp_below_fc100(self):
        return True if self.wdp < self.fc100 else False

    def find_theory(self):
        theory_type = ''

        if self.sleeping_beauty():
            theory_type += 'Sleeping Beauty in FC'
        elif self.bdp_in_icrr():
            theory_type += 'BDP in ICRR'
        elif self.knock_knock_in_rc():
            theory_type += 'Knock Knock in RC'
        elif self.cut_cut_pack_up_in_rc():
            theory_type += 'Cut Cut Pack Up in RC'
        elif self.cutting_the_flying_kite():
            theory_type += 'Cutting The Flying Kite'
        elif self.bdp_above_rc100():
            theory_type += 'BDP Above RC100'

        theory_type += ' & '

        if self.reverse_sleeping_beauty():
            theory_type += 'Reverse Sleeping Beauty in RC'
        elif self.wdp_in_icrr():
            theory_type += 'WDP in ICRR'
        elif self.knock_knock_in_fc():
            theory_type += 'Knock Knock in FC'
        elif self.cut_cut_pack_up_in_fc():
            theory_type += 'Cut Cut Pack Up in FC'
        elif self.catching_the_falling_knife():
            theory_type += 'Catching The Falling Knife'
        elif self.wdp_below_fc100():
            theory_type += 'WDP Below FC100'

        return theory_type

    def bdp_level(self, level=1):
        return self.get_level(self.bdp, levels=level)

    def bdp_level_traded(self, price, level=1):
        if price > self.bdp:
            return True if price > self.bdp_level(level)[1] else False
        else:
            return False

    def wdp_level(self, level=-1):
        return self.get_level(self.wdp, levels=level)

    def wdp_level_traded(self, price, level=-1):
        if price < self.wdp:
            return True if price < self.wdp_level(level)[1] else False
        else:
            return False

    def high_level(self, level=1):
        return self.get_level(self.high_1, levels=level)

    def high_level_traded(self, price, level=1):
        return True if price > self.high_level(level)[1] else False

    def low_level(self, level=-1):
        return self.get_level(self.low_1, levels=level)

    def low_level_traded(self, price, level=-1):
        return True if price < self.low_level(level)[1] else False

    def highest_high(self, level=1):
        return self.get_level(self.hhigh, levels=level)

    def highest_high_traded(self, price, level=1):
        return True if price > self.highest_high(level)[1] else False

    def lowest_low(self, level=-1):
        return self.get_level(self.llow, levels=level)

    def lowest_low_traded(self, price, level=-1):
        return True if price < self.lowest_low(level)[1] else False

    def traded_above(self, price, what, level):
        if price > what:
            return True if price > self.get_level(what, levels=level)[1] else False
        else:
            return False

    def traded_below(self, price, what, level):
        if price < what:
            return True if price < self.get_level(what, levels=level)[1] else False
        else:
            return False

    def up_move(self):
        return self.high_1 if self.traded_above(self.close_1, self.high_2, 0) else False

    def down_move(self):
        return self.low_1 if self.traded_below(self.close_1, self.low_2, 0) else False

    def up_move_traded(self, price):
        up_move = self.up_move()
        return price > up_move if up_move else False

    def down_move_traded(self, price):
        down_move = self.down_move()
        return price < down_move if down_move else False

    def snr_to_buy(self, price):
        try:
            return True if price > self.resistance_value else False
        except TypeError as te:
            print(te)

    def snr_to_sell(self, price):
        try:
            return True if price < self.support_value else False
        except TypeError as te:
            print(te)

    def valid_buy(self, price):  # Valid Buy
        valid_buy_level = max(self.bdp_level(2)[1], self.hsrc61)
        return valid_buy_level if price > valid_buy_level else False

    def valid_sell(self, price):  # Valid Sell
        valid_sell_level = min(self.wdp_level(-2)[1], self.lsfc61)
        return valid_sell_level if price < valid_sell_level else False

    def up_move_exhausts(self, price):
        if self.director_pattern == "2+2":
            return True if self.traded_below(price, self.jwd, -1) else False
        else:
            return True if self.traded_below(price, self.wdp, -1) else False

    def down_move_exhausts(self, price):
        if self.director_pattern == "3+1":
            return True if self.traded_above(price, self.jgd, 1) else False
        else:
            return True if self.traded_above(price, self.bdp, 1) else False

    def trend_reversal_buy(self, price):  # Trend Reversal Buy
        if price > self.upperband:
            if self.bdp > self.abs_upperband:
                if self.bdp_level_traded(price, 2):
                    return 2
                elif self.bdp_level_traded(price, 1):
                    return 1
                else:
                    return False
            else:
                if self.traded_above(price, self.abs_upperband, 1):
                    return 2
                elif self.traded_above(price, self.abs_upperband, 0):
                    return 1
                else:
                    return False

    def up_trend_continues(self, price):  # Up Trend Continues
        if price > self.upperband:
            if self.highest_high_traded(price):
                return 3
            else:
                return False

    def correction_sell(self, price):  # Correction Sell
        if price < self.lowerband and self.director_pattern != "2+1":
            if self.jwd < self.abs_lowerband:
                if self.traded_below(price, self.jwd, -2):
                    return 8
                elif self.traded_below(price, self.jwd, -1):
                    return 7
                else:
                    return False
            else:
                if self.traded_below(price, self.abs_lowerband, -1):
                    return 8
                elif self.traded_below(price, self.abs_lowerband, 0):
                    return 7
                else:
                    return False

    def cscoub(self, price):  # Correction Sell Completes Original Up Trend Begins
        if price > self.upperband:
            if self.bdp > self.abs_upperband:
                if self.bdp_level_traded(price, 2):
                    return 12
                elif self.bdp_level_traded(price, 1):
                    return 11
                else:
                    return False
            else:
                if self.traded_above(price, self.abs_upperband, 1):
                    return 12
                elif self.traded_above(price, self.abs_upperband, 0):
                    return 11
                else:
                    return False

    def cscoub_c(self, price):  # Correction Sell Completes Original Up Trend Begins - Continues
        if price > self.upperband:
            if self.highest_high_traded(price):
                return 13
            else:
                return False

    def trend_reversal_sell(self, price):  # Trend Reversal Sell
        if price < self.lowerband:
            if self.wdp < self.abs_lowerband:
                if self.wdp_level_traded(price, -2):
                    return 5
                elif self.wdp_level_traded(price, -1):
                    return 4
                else:
                    return False
            else:
                if self.traded_below(price, self.abs_lowerband, -1):
                    return 5
                elif self.traded_below(price, self.abs_lowerband, 0):
                    return 4
                else:
                    return False

    def down_trend_continues(self, price):  # Down Trend Continues
        if price < self.lowerband:
            if self.lowest_low_traded(price):
                return 6
            else:
                return False

    def pull_back_buy(self, price):  # Pull Back Buy
        if price > self.upperband and self.director_pattern != "2+1":
            if self.jgd > self.abs_upperband:
                if self.traded_above(price, self.jgd, 2):
                    return 10
                elif self.traded_above(price, self.jgd, 1):
                    return 9
                else:
                    return False
            else:
                if self.traded_above(price, self.abs_upperband, 1):
                    return 10
                elif self.traded_above(price, self.abs_upperband, 0):
                    return 9
                else:
                    return False

    def pbcodb(self, price):  # Pull Back Buy Completes Original Down Trend Begins
        if price < self.lowerband:
            if self.wdp < self.abs_lowerband:
                if self.wdp_level_traded(price, -2):
                    return 15
                elif self.wdp_level_traded(price, -1):
                    return 14
                else:
                    return False
            else:
                if self.traded_below(price, self.abs_lowerband, -1):
                    return 15
                elif self.traded_below(price, self.abs_lowerband, 0):
                    return 14
                else:
                    return False

    def pbcodb_c(self, price):  # Pull Back Buy Completes Original Down Trend Begins - Continues
        if price < self.lowerband:
            if self.lowest_low_traded(price):
                return 16
            else:
                return False

    def get_trending_leg(self):
        trending_legs = []

        if isnan(self.prev_trending_leg):
            self.prev_trending_leg = 0

        if self.prev_trending_leg == 0:

            trb = self.trend_reversal_buy(self.high)
            trs = self.trend_reversal_sell(self.low)

            if trb:
                trending_legs.append(trb)
            if trs:
                trending_legs.append(trs)

        elif self.prev_trending_leg in [2, 1, 3]:

            utc = self.up_trend_continues(self.high)
            trs = self.trend_reversal_sell(self.low)
            cs = self.correction_sell(self.low)

            if utc:
                trending_legs.append(utc)

            if trs:
                trending_legs.append(trs)
            elif cs:
                trending_legs.append(cs)

        elif self.prev_trending_leg in [8, 7]:

            cscoub = self.cscoub(self.high)
            trs = self.trend_reversal_sell(self.low)

            if cscoub:
                trending_legs.append(cscoub)
            if trs:
                trending_legs.append(trs)

        elif self.prev_trending_leg in [12, 11, 13]:

            cscoub_c = self.cscoub_c(self.high)
            trs = self.trend_reversal_sell(self.low)
            cs = self.correction_sell(self.low)

            if cscoub_c:
                trending_legs.append(cscoub_c)

            if trs:
                trending_legs.append(trs)
            elif cs:
                trending_legs.append(cs)

        elif self.prev_trending_leg in [5, 4, 6]:

            trb = self.trend_reversal_buy(self.high)
            pbb = self.pull_back_buy(self.high)
            dtc = self.down_trend_continues(self.low)

            if trb:
                trending_legs.append(trb)
            elif pbb:
                trending_legs.append(pbb)

            if dtc:
                trending_legs.append(dtc)

        elif self.prev_trending_leg in [10, 9]:

            trb = self.trend_reversal_buy(self.high)
            pbcodb = self.pbcodb(self.low)

            if trb:
                trending_legs.append(self.trend_reversal_buy(self.high))
            if pbcodb:
                trending_legs.append(pbcodb)

        elif self.prev_trending_leg in [15, 14, 16]:

            trb = self.trend_reversal_buy(self.high)
            pbb = self.pull_back_buy(self.high)
            pbcodb_c = self.pbcodb_c(self.low)

            if trb:
                trending_legs.append(trb)
            elif pbb:
                trending_legs.append(pbb)

            if pbcodb_c:
                trending_legs.append(pbcodb_c)

        if len(trending_legs) > 1:
            return self.prev_trending_leg
        elif len(trending_legs) < 1:
            return self.prev_trending_leg
        else:
            return trending_legs[0]


class Move(Indicator):
    lines = ('up_move', 'down_move', 'dominating_up_move', 'dominating_down_move', 'aborted_top', 'aborted_bottom')
    params = dict(daily=True)
    plotlines = dict(
        aborted_bottom=dict(marker='^', markersize=8.0, color='black', fillstyle='full'),
        aborted_top=dict(marker='v', markersize=8.0, color='black', fillstyle='full'),
    )

    def __init__(self):

        ilen = len(self)
        self.fibo = Fibo(replay=True)

        # Move
        self.move_direction = None
        self.up_move_begins_level, self.down_move_begins_level = None, None
        self.up_move_begins_index, self.down_move_begins_index = ilen, ilen

    def next(self):
        self.get_move()

    def subtract_indexes(self):
        self.up_move_begins_index -= 1
        self.down_move_begins_index -= 1

    def get_move(self):
        um = self.fibo.up_move()
        dm = self.fibo.down_move()

        if um:
            self.up_move[0] = self.fibo.high_1
            if self.move_direction == down:
                self.up_move_begins_level = self.fibo.high_1
                self.up_move_begins_index = 0

                if self.down_move_begins_level:
                    if self.fibo.traded_above(self.fibo.high_1, self.down_move_begins_level, 1):

                        aborted_bottom = self.down_move_begins_level
                        aborted_bottom_index = self.down_move_begins_index

                        slice_of_low = self.data0.low.get(size=abs(self.down_move_begins_index) - 1)
                        dex = self.down_move_begins_index
                        ll = self.data0.low[dex]
                        for sliced_low in slice_of_low:
                            dex += 1
                            if sliced_low < ll:
                                aborted_bottom = sliced_low
                                aborted_bottom_index = dex

                        self.aborted_bottom[aborted_bottom_index] = aborted_bottom
                        self.dominating_up_move[0] = self.fibo.high_1

            self.move_direction = up

        elif dm:
            self.down_move[0] = self.fibo.low_1
            if self.move_direction == up:
                self.down_move_begins_level = self.fibo.low_1
                self.down_move_begins_index = 0

                if self.up_move_begins_level:
                    if self.fibo.traded_below(self.fibo.low_1, self.up_move_begins_level, -1):
                        aborted_top = self.up_move_begins_level
                        aborted_top_index = self.up_move_begins_index

                        slice_of_high = self.data0.high.get(size=abs(self.up_move_begins_index) - 1)
                        dex = self.down_move_begins_index
                        hh = self.data0.high[dex]
                        for sliced_high in slice_of_high:
                            dex += 1
                            if sliced_high > hh:
                                aborted_top = sliced_high
                                aborted_top_index = dex

                        self.aborted_top[aborted_top_index] = aborted_top
                        self.dominating_down_move[0] = self.fibo.low_1

            self.move_direction = down


class Rar(Indicator):
    lines = (
        'valid_buy', 'valid_sell', 'gaso', 'wbso', 'master_high', 'key_low', 'master_low', 'key_high', 'gasj', 'wbsj')
    params = dict(daily=True)
    plotinfo = dict(subplot=False)
    plotlines = dict(
        gaso=dict(marker='^', markersize=8.0, color='blue', fillstyle='full'),
        wbso=dict(marker='v', markersize=8.0, color='blue', fillstyle='full'),
        gasj=dict(marker='^', markersize=8.0, color='red', fillstyle='full'),
        wbsj=dict(marker='v', markersize=8.0, color='red', fillstyle='full'),
        key_low=dict(marker='^', markersize=8.0, color='black', fillstyle='full'),
        key_high=dict(marker='v', markersize=8.0, color='black', fillstyle='full'),
    )

    def __init__(self):
        ilen = len(self)
        self.fibo = Fibo()
        self.valid = None
        self.state = None
        self.vhigh, self.vlow = None, None
        self.vhighx, self.vlowx = ilen, ilen
        self.mhigh, self.mlow = None, None
        self.mhighx, self.mlowx = ilen, ilen
        self.gaso_level, self.wbso_level = None, None
        self.masterhigh, self.keylow = None, None
        self.masterlow, self.keyhigh = None, None
        self.gas_block, self.wbs_block = False, False

    def next(self):
        self.subtract_indexes()
        self.get_rar()

    def subtract_indexes(self):
        self.vhighx -= 1
        self.vlowx -= 1
        self.mhighx -= 1
        self.mlowx -= 1

    def get_rar(self):

        valid_buy = self.fibo.valid_buy(self.fibo.high)
        valid_sell = self.fibo.valid_sell(self.fibo.low)

        # High Tracker
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.vhigh and self.fibo.high > self.vhigh:
            self.vhigh = self.fibo.high
            self.vhighx = 0

        # Low Tracker
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.vlow and self.fibo.low < self.vlow:
            self.vlow = self.fibo.low
            self.vlowx = 0

        # Valid Buy
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if valid_buy and not valid_sell and self.valid in [VS, None]:
            self.valid = VB
            self.mhigh, self.mhighx = self.vhigh, self.vhighx
            self.vhigh, self.vhighx = self.fibo.high, 0
            self.valid_buy[0] = self.vhigh
            self.wbs_block = False if self.wbs_block else do_nothing()

        # Valid Sell
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif valid_sell and not valid_buy and self.valid in [VB, None]:
            self.valid = VS
            self.mlow, self.mlowx = self.vlow, self.vlowx
            self.vlow, self.vlowx = self.fibo.low, 0
            self.valid_sell[0] = self.vlow
            self.gas_block = False if self.gas_block else do_nothing()

        # Good Above Series - Occur
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.valid == VB and not self.gas_block and self.mhigh:
            if self.fibo.high > self.mhigh:
                if self.fibo.traded_above(self.fibo.high, self.mhigh, 1):
                    self.gaso[0] = self.gaso_level = self.fibo.high
                    self.master_high[self.mhighx] = self.masterhigh = self.mhigh
                    self.key_low[self.vlowx] = self.keylow = self.vlow
                    self.gas_block = True
                    self.state = 1
                    return

        # Weak Below Series - Occur
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.valid == VS and not self.wbs_block and self.mlow:
            if self.fibo.low < self.mlow:
                if self.fibo.traded_below(self.fibo.low, self.mlow, -1):
                    self.wbso[0] = self.wbso_level = self.fibo.low
                    self.master_low[self.mlowx] = self.masterlow = self.mlow
                    self.key_high[self.vhighx] = self.keyhigh = self.vhigh
                    self.wbs_block = True
                    self.state = 5
                    return

        # Good Above Series - Justified
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.state == 1:
            if self.fibo.high > self.gaso_level and self.fibo.high > self.fibo.hsrc38:
                if self.fibo.traded_above(self.fibo.high, self.gaso_level, 1):
                    self.gasj[0] = self.fibo.high
                    self.state = 2
                    return

        # Weak Below Series - Justified
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.state == 5:
            if self.fibo.low < self.wbso_level and self.fibo.low < self.fibo.lsfc38:
                if self.fibo.traded_below(self.fibo.low, self.wbso_level, -1):
                    self.wbsj[0] = self.fibo.low
                    self.state = 6
                    return


class Snr(Indicator):
    lines = ('price', 'support', 'climbing_buy', 'resistance', 'drifting_sell')
    params = dict(daily=True, period=50)
    plotinfo = dict(subplot=False)
    plotlines = dict()

    def __init__(self):
        self.fibo = Fibo(self.data1, replay=True)
        self.fibo.snr_log = []
        self.addminperiod(self.p.period)  # TODO change period based on required min candles
        self.opening_candle = False
        self.open = ""
        self.post_closing = False

    def next(self):
        self.dt0 = self.data0.datetime.datetime(0)
        self.dt1 = self.data1.datetime.datetime(0)

        if self.opening_candle:
            self.or_high = self.data0.high[0]
            self.or_low = self.data0.low[0]
            self.or_close = self.data0.close[0]
            self.open = self.fibo.how(self.or_high, self.or_low, self.or_close).lower()
            self.trend = self.fibo.trend
            self.hs_fork = [vx for vx in self.fibo.hs_fork if not self.fibo.hsrc_active < vx < self.fibo.upperband]
            self.ls_fork = [vx for vx in self.fibo.ls_fork if not self.fibo.lsfc_active > vx > self.fibo.lowerband]
            self.snr_high, self.snr_low = self.or_high, self.or_low
            self.snr2buy_spawned, self.snr2buy_diffused = [], []
            self.snr2sell_spawned, self.snr2sell_diffused = [], []
            self.post_closing = False
            self.post_closing_values = {}

            if 'rmsl' in self.open:
                self.band_traded = True
                if 'high' in self.open:  # 'RMSL-HIGH'
                    if 'close < lsrc38' in self.open:
                        self.fibo.support_value = self.fibo.lowerband
                    else:
                        self.fibo.support_value = max(self.fibo.support(self.or_close)[1], self.fibo.lsrc_active)
                        if self.trend == 'up trend' and self.or_high < self.fibo.hsrc100:  # In RC if Up trend, Support = LSRC_Active till HSRC61 traded
                            self.fibo.support_name, self.fibo.support_value = 'lsrc_active', self.fibo.lsrc_active
                    self.fibo.climbing_buy_value = self.fibo.climbing_buy(self.or_high)[1]
                    self.post(self.dt0, self.fibo.upperband, self.open, s=self.fibo.support_value,
                              cb=self.fibo.climbing_buy_value)
                    self.halt_dictionary = {self.fibo.support_value: self.support_traded,
                                            self.fibo.climbing_buy_value: self.climbing_buy_traded}
                else:  # 'RMSL-LOW'
                    if 'close > hsfc38' in self.open:
                        self.fibo.resistance_value = self.fibo.upperband
                    else:
                        self.fibo.resistance_value = min(self.fibo.resistance(self.or_close)[1], self.fibo.hsfc_active)
                        if self.trend == 'down trend' and self.or_low > self.fibo.lsfc100:  # In FC if Down trend, Resistance = HSFC_Active till LSFC61 traded
                            self.fibo.resistance_name, self.fibo.resistance_value = 'hsfc_active', self.fibo.hsfc_active
                    self.fibo.drifting_sell_value = self.fibo.drifting_sell(self.or_low)[1]
                    self.post(self.dt0, self.fibo.lowerband, self.open, r=self.fibo.resistance_value,
                              ds=self.fibo.drifting_sell_value)
                    self.halt_dictionary = {self.fibo.resistance_value: self.resistance_traded,
                                            self.fibo.drifting_sell_value: self.drifting_sell_traded}
                self.fibo.nomenclate()
            else:
                self.kissed = False
                self.hs_fork.append(self.fibo.rc_kiss)
                self.ls_fork.append(self.fibo.fc_kiss)
                if 'icrc' in self.open:
                    self.post(self.dt0, self.fibo.hsrc_active, self.open)
                    self.visited_rc = True
                    self.visited_fc = False
                    self.halt_dictionary = {self.fibo.lsrc_active: self.active_resistance_in_rc,
                                            self.fibo.upperband: self.upper_band_traded}
                elif 'icfc' in self.open:
                    self.post(self.dt0, self.fibo.lsfc_active, self.open)
                    self.visited_fc = True
                    self.visited_rc = False
                    self.halt_dictionary = {self.fibo.lowerband: self.lower_band_traded,
                                            self.fibo.hsfc_active: self.active_support_in_fc}
                elif 'icrr' in self.open:
                    self.post(self.dt0, 0, self.open)
                    self.visited_rc = False
                    self.visited_fc = False
                    self.halt_dictionary = {self.fibo.hsrc_active: self.active_support_in_rc,
                                            self.fibo.lsfc_active: self.active_resistance_in_fc}
            self.opening_candle = False
            self.count = 0
            return

        if self.open:
            self.count += 1

            pc = self.data0.close[-1]
            h = self.data0.high[0]
            l = self.data0.low[0]
            c = self.data0.close[0]

            if self.count == 1:  # Adjust close
                if 'icrc' in self.open and pc < self.fibo.lsrc_active:  # In ICRC if or_close < lsrc_active => adjust
                    pc = self.fibo.rc_active
                elif 'icfc' in self.open and pc > self.fibo.hsfc_active:  # In ICFC if or_close < hsfc_active => adjust
                    pc = self.fibo.fc_active

            if self.snr_high is None or h > self.snr_high:
                self.snr_high = h
            if self.snr_low is None or l < self.snr_low:
                self.snr_low = l

            if pc >= h:
                sequence = [pc, l, h, c]
            elif pc <= l:
                sequence = [pc, h, l, c]
            else:
                if min(h - pc, pc - l) == h - pc:
                    sequence = [pc, h, l, c]
                else:
                    sequence = [pc, l, h, c]

            for i in range(3):
                begin = sequence[i]
                destination = sequence[i + 1]
                fork = sorted(self.hs_fork) if destination > begin else sorted(self.ls_fork, reverse=True)
                big = max(begin, destination)
                small = min(begin, destination)
                halts = [v for v in fork if big > v > small]
                for halt in halts:
                    if halt in self.halt_dictionary.keys():
                        self.halt_dictionary[halt](self.dt0, halt)

        if self.dt0 == self.dt1:

            if self.post_closing:
                last_event = self.fibo.snr_log[-1]
                if last_event['support']:
                    pcs = last_event['support']
                    pccb = last_event['climbing buy']
                    self.post_closing_values = {'pcs': pcs, 'pccb': pccb}
                else:
                    pcr = last_event['resistance']
                    pcds = last_event['drifting sell']
                    self.post_closing_values = {'pcr': pcr, 'pcds': pcds}

            print(pd.DataFrame(self.fibo.snr_log)) if len(self.fibo.snr_log) else do_nothing()
            self.fibo.snr_log.clear()

            self.opening_candle = True

    def post(self, event_time, price, event, s='', cb='', r='', ds=''):
        if not self.post_closing:
            if s != '' or r != '':
                self.post_closing = True
        self.fibo.snr_log.append({'event_timestamp': event_time, 'price': price, 'event': event, 'support': s,
                                  'climbing buy': cb, 'resistance': r, 'drifting sell': ds})

    def support_traded(self, event_time, price):
        event = 'S&R to Sell at {}'.format(self.fibo.support_name)
        self.calculate_resistance(self.snr_high, level=1)
        self.snr_high = None
        self.snr_low = price
        self.calculate_drifting_sell(price)
        self.snr2sell_spawned.append(
            {'price': price, 'resistance': self.fibo.resistance_value, 'drifting sell': self.fibo.drifting_sell_value,
             'power': []})
        if self.snr2buy_spawned:
            for each in self.snr2buy_spawned:
                if price <= each['support']:
                    self.snr2buy_spawned.remove(each)
        self.halt_dictionary = {self.fibo.resistance_value: self.resistance_traded,
                                self.fibo.drifting_sell_value: self.drifting_sell_traded}
        self.post(event_time, price, event, r=self.fibo.resistance_value, ds=self.fibo.drifting_sell_value)

    def resistance_traded(self, event_time, price):
        event = 'S&R to Buy at {}'.format(self.fibo.resistance_name)
        self.calculate_support(self.snr_low, level=-1)
        self.snr_low = None
        self.snr_high = price
        self.calculate_climbing_buy(price)
        self.snr2buy_spawned.append(
            {'price': price, 'support': self.fibo.support_value, 'climbing buy': self.fibo.climbing_buy_value,
             'power': []})
        if self.snr2sell_spawned:
            for each in self.snr2sell_spawned:
                if price > each['resistance']:
                    self.snr2sell_spawned.remove(each)
        self.halt_dictionary = {self.fibo.support_value: self.support_traded,
                                self.fibo.climbing_buy_value: self.climbing_buy_traded}
        self.post(event_time, price, event, s=self.fibo.support_value, cb=self.fibo.climbing_buy_value)

    def climbing_buy_traded(self, event_time, price):
        event = 'CB Traded at {}'.format(self.fibo.climbing_buy_name)
        self.calculate_support(price)
        self.calculate_climbing_buy(price)
        if self.snr2buy_spawned:
            for each in self.snr2buy_spawned:
                if each["power"]:
                    if self.fibo.support_value > each["power"][-1]:
                        each["power"].append(self.fibo.support_value)
                else:
                    each["power"].append(self.fibo.support_value)
        if self.snr2sell_spawned:
            for each in self.snr2sell_spawned:
                if price > each['resistance']:
                    self.snr2sell_spawned.remove(each)
        self.halt_dictionary = {self.fibo.support_value: self.support_traded,
                                self.fibo.climbing_buy_value: self.climbing_buy_traded}
        self.post(event_time, price, event, s=self.fibo.support_value, cb=self.fibo.climbing_buy_value)

    def drifting_sell_traded(self, event_time, price):
        event = 'DS Traded at {}'.format(self.fibo.drifting_sell_name)
        self.calculate_resistance(price)
        self.calculate_drifting_sell(price)
        if self.snr2sell_spawned:
            for each in self.snr2sell_spawned:
                if each["power"]:
                    if self.fibo.resistance_value < each["power"][-1]:
                        each["power"].append(self.fibo.resistance_value)
                else:
                    each["power"].append(self.fibo.resistance_value)
        if self.snr2buy_spawned:
            for each in self.snr2buy_spawned:
                if price <= each['support']:
                    self.snr2buy_spawned.remove(each)
        self.halt_dictionary = {self.fibo.resistance_value: self.resistance_traded,
                                self.fibo.drifting_sell_value: self.drifting_sell_traded}
        self.post(event_time, price, event, r=self.fibo.resistance_value, ds=self.fibo.drifting_sell_value)

    def active_support_in_fc(self, event_time, price):
        event = 'Active Support in FC'
        if self.visited_rc:
            event = 'Rebegin to Buy'
        self.post(event_time, price, event)
        if not self.kissed:
            self.halt_dictionary = {self.fibo.support(price)[1]: self.support_traded,
                                    self.fibo.rc_kiss: self.active_support_rc_kiss}
        else:
            self.halt_dictionary = {self.fibo.support(price)[1]: self.support_traded,
                                    self.fibo.hsrc_active: self.active_support_in_rc}

    def active_support_rc_kiss(self, event_time, price):
        event = 'Active Support RC Kiss'
        self.post(event_time, price, event)
        self.kissed = True
        self.halt_dictionary = {self.fibo.lsfc_active: self.active_resistance_in_fc,
                                self.fibo.hsrc_active: self.active_support_in_rc}

    def active_support_in_rc(self, event_time, price):
        event = 'Active Support in RC'
        if self.visited_rc:
            event = 'ReEntry into RC'
        self.visited_rc = True
        self.post(event_time, price, event)
        if not self.kissed:
            self.halt_dictionary = {self.fibo.fc_kiss: self.active_resistance_fc_kiss,
                                    self.fibo.upperband: self.upper_band_traded}
        else:
            self.halt_dictionary = {self.fibo.lsfc_active: self.active_resistance_in_fc,
                                    self.fibo.upperband: self.upper_band_traded}

    def active_resistance_in_rc(self, event_time, price):
        event = 'Active Resistance in RC'
        if self.visited_fc:
            event = 'Rebegin to Sell'
        self.post(event_time, price, event)
        if not self.kissed:
            self.halt_dictionary = {self.fibo.fc_kiss: self.active_resistance_fc_kiss,
                                    self.fibo.resistance(price)[1]: self.resistance_traded}
        else:
            self.halt_dictionary = {self.fibo.lsfc_active: self.active_resistance_in_fc,
                                    self.fibo.resistance(price)[1]: self.resistance_traded}

    def active_resistance_fc_kiss(self, event_time, price):
        event = 'Active Resistance FC Kiss'
        self.post(event_time, price, event)
        self.kissed = True
        self.halt_dictionary = {self.fibo.lsfc_active: self.active_resistance_in_fc,
                                self.fibo.hsrc_active: self.active_support_in_rc}

    def active_resistance_in_fc(self, event_time, price):
        event = 'Active Resistance in FC'
        if self.visited_fc:
            event = 'ReEntry into FC'
        self.visited_fc = True
        self.post(event_time, price, event)
        if not self.kissed:
            self.halt_dictionary = {self.fibo.lowerband: self.lower_band_traded,
                                    self.fibo.rc_kiss: self.active_support_rc_kiss}
        else:
            self.halt_dictionary = {self.fibo.lowerband: self.lower_band_traded,
                                    self.fibo.hsrc_active: self.active_support_in_rc}

    def lower_band_traded(self, event_time, price):
        event = 'Lower Band Traded'
        self.calculate_resistance(price)
        self.calculate_drifting_sell(price)
        self.halt_dictionary = {self.fibo.resistance_value: self.resistance_traded,
                                self.fibo.drifting_sell_value: self.drifting_sell_traded}
        self.post(event_time, price, event, r=self.fibo.resistance_value, ds=self.fibo.drifting_sell_value)

    def upper_band_traded(self, event_time, price):
        event = 'Upper Band Traded'
        self.calculate_support(price)
        self.calculate_climbing_buy(price)
        self.halt_dictionary = {self.fibo.support_value: self.support_traded,
                                self.fibo.climbing_buy_value: self.climbing_buy_traded}
        self.post(event_time, price, event, s=self.fibo.support_value, cb=self.fibo.climbing_buy_value)

    def calculate_support(self, price, level=-2):
        self.fibo.support_value = self.fibo.support(price, level=level)[1]
        if self.trend == 'up trend' and price == self.fibo.hsrc61:  # In RC if Up trend or Both Trend, Support = LSRC_Active till HSRC61 traded
            self.fibo.support_name, self.fibo.support_value = 'lsrc_active', self.fibo.lsrc_active
        if self.fibo.close_1 > self.fibo.support_value > self.fibo.lowerband:  # Support can not be LSFC_Active
            self.fibo.support_name, self.fibo.support_value = self.fibo.get_name(
                self.fibo.lowerband), self.fibo.lowerband

    def calculate_resistance(self, price, level=2):
        self.fibo.resistance_value = self.fibo.resistance(price, level=level)[1]
        if self.trend == 'down trend' and price == self.fibo.lsfc61:  # In FC if Down trend or Both trend, Resistance = HSFC_Active till LSFC61 traded
            self.fibo.resistance_name, self.fibo.resistance_value = 'hsfc_active', self.fibo.hsfc_active
        if self.fibo.upperband > self.fibo.resistance_value > self.fibo.close_1:  # Resistance can not be HSRC_Active
            self.fibo.resistance_name, self.fibo.resistance_value = self.fibo.get_name(
                self.fibo.upperband), self.fibo.upperband

    def calculate_climbing_buy(self, price):
        self.fibo.climbing_buy_value = self.fibo.climbing_buy(price)[1]
        if self.fibo.upperband > self.fibo.climbing_buy_value > self.fibo.close_1:  # Climbing Buy can not be HSRC_Active
            self.fibo.climbing_buy_name, self.fibo.climbing_buy_value = self.fibo.get_name(
                self.fibo.upperband), self.fibo.upperband
        if self.trend == 'down trend' and price == self.fibo.hsfc61:  # In FC if Down trend or Both trend, Climbing Buy = HSFC_Active till HSFC61 traded
            self.fibo.climbing_buy_name, self.fibo.climbing_buy_value = 'hsfc_active', self.fibo.hsfc_active

    def calculate_drifting_sell(self, price):
        self.fibo.drifting_sell_value = self.fibo.drifting_sell(price)[1]
        if self.fibo.close_1 > self.fibo.drifting_sell_value > self.fibo.lowerband:  # Drifting Sell can not be LSFC_Active
            self.fibo.drifting_sell_name, self.fibo.drifting_sell_value = self.fibo.get_name(
                self.fibo.lowerband), self.fibo.lowerband
        if self.trend == 'up trend' and price == self.fibo.lsrc61:  # In RC if Up trend or Both trend, Drifting Sell = LSRC_Active till LSRC61 traded
            self.fibo.drifting_sell_name, self.fibo.drifting_sell_value = 'lsrc_active', self.fibo.lsrc_active


class Gap(Indicator):
    lines = ('hg', 'hng', 'hj', 'hrj', 'lg', 'lng', 'lj', 'lrj')
    params = dict(daily=True, period=75)
    plotinfo = dict(subplot=False)
    plotlines = dict()

    def __init__(self):
        self.fibo = Fibo(self.data1, replay=True)
        self.addminperiod(self.p.period)
        self.opening_candle = False
        self.gap_state = ""
        self.pchg = []
        self.pclg = []

    def next(self):
        self.dt0 = self.data0.datetime.datetime(0)
        self.dt1 = self.data1.datetime.datetime(0)
        l = self.data0.low[0]
        h = self.data0.high[0]

        if self.opening_candle:
            if self.fibo.higher_gap(l):
                self.gap_state = PCHG
            elif self.fibo.lower_gap(h):
                self.gap_state = PCLG

            self.opening_candle = False
            return

        if self.gap_state == PCHG and l <= self.fibo.nbdp:
            self.gap_state = PCNOHG

        if self.gap_state == PCLG and h >= self.fibo.nwdp:
            self.gap_state = PCNOLG

        if self.dt0 == self.dt1:
            #  TODO if self.gap_state in PCHG|PCLG find Day HIGH|LOW to set justification LEVEL
            self.opening_candle = True
