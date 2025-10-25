import importlib, traceback, sys

try:
    m = importlib.import_module('app.main')
    print('import succeeded')
except Exception:
    traceback.print_exc()
    sys.exit(1)
