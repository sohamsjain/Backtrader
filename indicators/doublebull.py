from backtrader import Indicator


class BarType(Indicator):
    lines = ("nature", "bullish", "bearish")
    params = ()
    plotinfo = dict(subplot=False)
    plotlines = dict(
        bullish=dict(marker='^', markersize=8.0, color='black', fillstyle='full'),
        bearish=dict(marker='v', markersize=8.0, color='black', fillstyle='full'),
        nature=dict(_plotskip=True),
    )

    def next(self):
        barbody = round(self.data0.close[0] - self.data0.open[0], 2)
        barrange = round(self.data0.high[0] - self.data0.low[0], 2)
        # closeposition = round(self.data0.close[0] - self.data0.low[0], 2) / barrange
        density = abs(barbody) / barrange
        if barbody > 0:  # green

            if density >= 0.5:
                self.lines.nature[0] = 1
                self.lines.bullish[0] = self.data0.low[0]

        elif barbody < 0:  # red

            if density >= 0.5:
                self.lines.nature[0] = -1
                self.lines.bearish[0] = self.data0.high[0]

        else:
            self.lines.nature[0] = 0
