import logging

"""
logger helper class for writing debug logs and save heating csv

CRITICAL    50
ERROR       40
WARNING     30
INFO        20
DEBUG       10
NOTSET      0
"""

def setup_logger():
    lg = logging.getLogger('DishwasherOS')
    lg.setLevel(logging.DEBUG)

    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create file handler
    fh = logging.FileHandler('runlog.log')
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s|%(levelname)s|%(message)s',
        '%Y-%m-%d_%H:%M:%S'
    )

    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    lg.addHandler(ch)
    lg.addHandler(fh)

    # lg.info("logger start")