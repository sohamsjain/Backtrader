import sys

from batman import BaTMan
from extlogger import ExecutionReport

excrep = ExecutionReport(__file__)

try:

    b = BaTMan()
    b.run()

except Exception as e:
    exc_info = sys.exc_info()
    excrep.submit(*exc_info)
    del exc_info
