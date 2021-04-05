PENDING, ENTRY, STOPLOSS, TARGET, CANCELLED, REJECTED, MARGIN, MISSED, FAILED = range(9)


class Xone:
    attrs = ['symbol', 'entry', 'stoploss', 'target', 'size', 'status', 'entryhit']

    def __init__(self, symbol, entry, stoploss, target=None, status=None, entryhit=False, size=0):
        if entry == stoploss:
            raise ValueError("Entry Cannot be equal to Stoploss")

        self.symbol = symbol
        self.entry = entry
        self.stoploss = stoploss
        self.rpu = abs(entry - stoploss)
        self.islong = entry > stoploss
        self.target = target or (entry + (2 * self.rpu) if self.islong else entry - (2 * self.rpu))
        self.status = status or PENDING
        self.entryhit = entryhit or False
        self.nextstatus = None
        self.size = size or 0

    def setstatus(self, status):
        self.status = status

    def setsize(self, size):
        self.size = size

    def getvalues(self):
        return {k: v for k, v in self.__dict__.items() if k in Xone.attrs}
