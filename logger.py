import logging
import time
import os

from program import WashingProgram

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


class ProcessDataProvider:

    def __init__(self, program: WashingProgram):
        self.program = program
        self.swconfig = program.swconfig

    def write_csv_data_record(self):
        time_start = self.program.time_start
        logger_file_name = '{}_DataRecord.csv'.format(int(time_start))
        logger_file_path = os.path.join(self.swconfig.logging_directory, logger_file_name)
        with open(logger_file_path, 'a') as fd:
            timestamp = time.strftime('%H:%M:%S')
            runtime = self.program.get_current_runtime()
            fd.write('{time};{runtime};{termostop};{step};{temp}'.format(
                time=timestamp, runtime=runtime, termostop=self.program.is_thermo_stop(),
                step=self.program.step_operational, temp=self.program.machine.read_temperature()))
