from typing import List, Optional

lengthOfStatuses = 10
PENDING, ENTRY, STOPLOSS, TARGET, MISSED, FAILED, HARDEXIT, CANCELLED, REJECTED, MARGIN = range(lengthOfStatuses)

statuses: List[str] = ["PENDING", "ENTRY", "STOPLOSS", "TARGET", "MISSED", "FAILED", "HARDEXIT", "CANCELLED",
                       "REJECTED", "MARGIN"]


class Xone:
    attrs = ['symbol', 'entry', 'stoploss', 'target', 'size', 'status', 'entryhit']

    def __init__(self, symbol, entry, stoploss, target=None, state=None, entryhit=0, size=0):
        if entry == stoploss:
            raise ValueError("Entry Cannot be equal to Stoploss")

        self.symbol: str = symbol
        self.entry: float = entry
        self.stoploss: float = stoploss
        self.rpu: float = abs(entry - stoploss)
        self.islong: bool = entry > stoploss
        self.target: float = target or (entry + (2 * self.rpu) if self.islong else entry - (2 * self.rpu))
        self.state: int = state or PENDING
        self.status: str = statuses[self.state]
        self.entryhit: int = entryhit or 0
        self.nextstate: Optional[int] = None
        self.size: int = size or 0

    def setstate(self, state):
        self.state = state
        self.status = statuses[self.state]

    def setsize(self, size):
        self.size = size

    def getvalues(self):
        return {k: v for k, v in self.__dict__.items() if k in Xone.attrs}

    def __hash__(self):
        return hash(tuple(self.getvalues().values()))


def spawn(kwargs: dict):
    kwargs = {key: val for key, val in kwargs.items() if val != ''}
    try:
        for attr in ["symbol", "entry", "stoploss"]:
            assert attr in kwargs, f"Missing Xone Attribute: {attr}"

        symbol = kwargs['symbol']
        assert isinstance(symbol, str), "symbol must be a string"

        entry = kwargs['entry']
        assert isinstance(entry, (float, int)), "entry not of type (float, int)"

        stoploss = kwargs['stoploss']
        assert isinstance(stoploss, (float, int)), "stoploss not of type (float, int)"

        assert entry != stoploss, "Entry Cannot be equal to Stoploss"

        target = kwargs.get('target', None)
        if target:
            assert isinstance(target, (float, int)), "target not of type (float, int)"

        size = kwargs.get('size', None)
        if size:
            assert isinstance(size, int), "size not of type int"

        state = kwargs.get('state', None)
        if state:
            assert isinstance(state, int), "state must be an integer"
            assert state in range(lengthOfStatuses), f"state must be in range({lengthOfStatuses})"

        entryhit = kwargs.get('entryhit', False)
        if entryhit is not False:
            if entryhit.lower() == 'true':
                entryhit = True
            elif entryhit.lower() == 'false':
                entryhit = False
            else:
                raise ValueError('entryhit attr has an ambiguous value. Must be True or False')

        x = Xone(symbol=symbol,
                 entry=entry,
                 stoploss=stoploss,
                 target=target,
                 size=size,
                 state=state,
                 entryhit=entryhit)

        return x
    except (AssertionError, ValueError) as ae:
        return ae
