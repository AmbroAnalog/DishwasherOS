"""
Modules that take care of the collection and transfer of process-relevant data.
"""

import time
import os
import serial
import logging
import traceback
from threading import Event, Thread
from program import WashingProgram


def _format_integer(value, digits = None):
    if digits:
        return str(int(value)).zfill(digits)
    else:
        return str(int(value))


class ProcessDataProvider:
    def __init__(self, program: WashingProgram):
        self.session_id = int(time.time())
        self.program = program
        self.swconfig = program.swconfig
        self.module_logger = logging.getLogger('DishwasherOS.ProcessData')

        # self.timer = SendProcessDataRepeatedTimer(self.swconfig.data_repeated_timer_interval, self.collect_process_data)

    def collect_process_data(self):
        """thread function to collect & transfer process data"""
        runtime = self.program.get_current_runtime()
        time_left = self.program.get_time_left_program()
        progress_percent = int((runtime / time_left + runtime) * 100)
        process_data = {
            'session_id': self.session_id,
            'program_runtime': runtime,
            'program_progress_percent:': progress_percent,
            'program_step_operational': self.program.step_operational,
            'program_step_sequence': self.program.step_sequence,
            'program_selected_id': self.program.selected_program,
            'program_time_left_step': self.program.get_time_left_operationalstep(),
            'program_time_left_sequence': self.program.get_time_left_sequence_step(),
            'program_time_left_program': time_left,
            'machine_temperature': self.program.machine.read_temperature(),
            'machine_sensor_values': self.program.machine.read_actuator_sensor_values()
        }
        # use process_data dict to distribute it to all endpoints
        self.send_process_data_serial_projector(process_data)

    def send_process_data_serial_projector(self, process_data):
        if self.program.time_start is None:
            return
        if self.program.time_start is not None and self.program.time_end is None:
            serial_data = "ETE{}PR{}T{}M0U{}E{}A{}H{}X".format(
                _format_integer(process_data['program_time_left_program'], 4),
                _format_integer(process_data['program_progress_percent'], 3),
                _format_integer(process_data['machine_temperature'], 2),
                _format_integer(process_data['machine_sensor_values']['pump_circulation']),
                _format_integer(process_data['machine_sensor_values']['valve_inlet']),
                _format_integer(process_data['machine_sensor_values']['valve_outlet']),
                _format_integer(process_data['machine_sensor_values']['heating'])
            )
        else:
            serial_data = "ETE0000PR111T00M0U0E0A0H0X"

        serial_communicator = serial.Serial('/dev/ttyS0', 9600, timeout=0.5)
        serial_communicator.flush()
        try:
            serial_communicator.write(serial_data.encode('utf-8'))
            self.module_logger.debug('send data to ttySO: ' + serial_data)
        except Exception as e:
            # or maybe serial.SerialException
            self.module_logger.error(traceback.format_exc())
        serial_communicator.close()

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


class SendProcessDataRepeatedTimer(object):
    """
    Repeat the passed `function` every `interval` seconds with given `args`.
    """
    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target)
        self.thread.start()

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self):
        self.event.set()
        self.thread.join()
