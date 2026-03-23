try:
    from dateutil import parser
    print("ok")
except ImportError:
    print("missing")
