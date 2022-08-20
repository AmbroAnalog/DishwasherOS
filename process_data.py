"""
Modules that take care of the collection and transfer of process-relevant data.
"""

import time
import os

import serial
import logging
import traceback
import requests
import json
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
        self.module_logger.info('initialize ProcessDataProvider with [session_id:{}]'.format(self.session_id))

        self.data_report_state = 0
        """ data_report_state list:
            0   =>  only report is_alive, before program selection
            1   =>  report process_data, active process
            2   =>  report limited process_data, in afterrunning cycle
            3   =>  only report is_alive, program ended
        """
        self.last_process_data_report = False
        self.backend_is_working = True
        self.electricity_meter_connected = False
        self.electricity_aenergy_init = 0.0
        self.read_initial_aenergy()

        self.timer = SendProcessDataRepeatedTimer(self.swconfig.data_repeated_timer_interval, self.collect_process_data)

    def read_initial_aenergy(self):
        """try to read and store the inital value of total aenergy from rpc electricity meter"""
        electricity_aenergy_init = self.get_electricity_meter_metrics(True)['aenergy']

        if electricity_aenergy_init is not None:
            self.electricity_meter_connected = True
            self.electricity_aenergy_init = float(electricity_aenergy_init)
            self.module_logger.info('electricity meter connected with %s Wh' % self.electricity_aenergy_init)
        else:
            self.module_logger.warning('electricity meter not found!')

    def get_program_aenergy(self, aenergy_current=-1) -> int:
        """return the used energy consumption for running program in Watt-hours"""
        aenergy_relative = 0.0
        if aenergy_current == -1:
            aenergy_current = self.get_electricity_meter_metrics()['aenergy']
        if not self.electricity_meter_connected or aenergy_current is None:
            return 0
        return int(float(aenergy_current) - self.electricity_aenergy_init)

    def get_electricity_meter_metrics(self, inital=False) -> dict:
        metrics = {'aenergy': None, 'apower': None}
        if not inital and not self.electricity_meter_connected:
            return metrics
        base_url = self.swconfig.electricity_meter_ip
        base_url = base_url.rstrip('/').lstrip('http://')
        target_api_url = 'http://' + base_url + '/rpc/Switch.GetStatus?id=0'
        try:
            response = requests.get(target_api_url, verify=False)
            if response.ok:
                data = json.loads(response.content)
                metrics['aenergy'] = data.get('aenergy').get('total')
                metrics['apower'] = int(data.get('apower')) if data.get('apower') is not None else None
        except requests.exceptions.RequestException as e:
            pass
        # self.module_logger.debug('electricity_meter_metrics request ' + json.dumps(metrics))
        return metrics

    def collect_process_data(self):
        """thread function to collect & transfer process data"""
        if self.program.time_start is None or self.data_report_state == 3:
            self.send_is_alive_backend()
            return
        if self.program.time_start is not None and self.data_report_state == 0:
            # start report for process_data
            self.data_report_state = 1
            self.module_logger.info('start data_report_state 1')
        if self.program.time_end is not None and self.data_report_state == 1:
            if not self.last_process_data_report:
                self.last_process_data_report = True
                self.module_logger.debug('prepare data_report_state 2')
            else:
                # start afterrunning cycle
                self.data_report_state = 2
                self.module_logger.info('start data_report_state 2 (afterrunning cycle)')
        if self.data_report_state == 2:
            current_time = int(time.time())
            afterrunning_time_left = self.swconfig.program_afterrunning_cycle - (current_time - self.program.time_end)
            if afterrunning_time_left < 0:
                self.data_report_state = 3
                self.module_logger.info('start data_report_state 3')
                return
        runtime = self.program.get_current_runtime()
        time_left = self.program.get_time_left_program() if self.data_report_state == 1 else 0
        if time_left + runtime == 0:
            progress_percent = 0
        elif self.program.time_end is None:
            progress_percent = int((runtime / (time_left + runtime)) * 100)
        else:
            progress_percent = 100
        electricity_metrics = self.get_electricity_meter_metrics()
        process_data = {
            'session_id': self.session_id,
            'device_identifier': self.program.machine.device_identifier,
            'program_runtime': runtime,
            'program_progress_percent': progress_percent,
            'program_step_operational': self.program.step_operational,
            'program_step_sequence': self.program.step_sequence,
            'program_selected_id': self.program.selected_program,
            'program_estimated_runtime': self.program.estimated_runtime,
            'program_time_start': self.program.time_start,
            'program_time_end': self.program.time_end,
            'program_time_left_step': self.program.get_time_left_operationalstep() if self.data_report_state != 2 else afterrunning_time_left,
            'program_time_left_sequence': self.program.get_time_left_sequence_step() if self.data_report_state != 2 else afterrunning_time_left,
            'program_time_left_program': time_left,
            'machine_temperature': self.program.machine.read_temperature(),
            'machine_sensor_values': self.program.machine.read_actuator_sensor_values(),
            'machine_aenergy': self.get_program_aenergy(electricity_metrics['aenergy']),
            'machine_apower': electricity_metrics['apower']
        }
        # use process_data dict to distribute it to all endpoints
        self.send_process_data_serial_projector(process_data)
        self.send_process_data_backend(process_data)

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
            # self.module_logger.debug('send data to ttySO: ' + serial_data)
        except Exception as e:
            # or maybe serial.SerialException
            self.module_logger.error(traceback.format_exc())
        serial_communicator.close()

    def send_process_data_backend(self, process_data):
        base_url = self.swconfig.backend_base_url
        base_url = base_url.rstrip('/')
        target_api_url = base_url + '/insert/run_state/'
        try:
            requests.post(target_api_url, verify=False, json=process_data)
        except requests.exceptions.RequestException as e:
            # backend call raised an exception
            if self.backend_is_working:
                self.module_logger.exception('backend call raised an exception')
                self.backend_is_working = False
        else:
            self.backend_is_working = True

    def send_is_alive_backend(self):
        base_url = self.swconfig.backend_base_url
        base_url = base_url.rstrip('/')
        target_api_url = base_url + '/insert/is_alive/'
        process_data = {
            'session_id': self.session_id,
            'device_identifier': self.program.machine.device_identifier}
        try:
            requests.post(target_api_url, verify=False, json=process_data)
        except requests.exceptions.RequestException as e:
            # backend call raised an exception
            if self.backend_is_working:
                self.module_logger.exception('backend call raised an exception')
                self.backend_is_working = False
        else:
            self.backend_is_working = True

    def write_csv_data_record(self):
        time_start = self.program.time_start
        logger_file_name = '{}_DataRecord.csv'.format(int(time_start))
        logger_file_path = os.path.join(self.swconfig.logging_directory, logger_file_name)
        with open(logger_file_path, 'a') as fd:
            timestamp = time.strftime('%H:%M:%S')
            runtime = self.program.get_current_runtime()
            fd.write('{time};{runtime};{termostop};{step};{temp}\n'.format(
                time=timestamp, runtime=runtime, termostop=self.program.is_thermo_stop(),
                step=self.program.step_operational, temp=self.program.machine.read_temperature()))

    def write_csv_program_completion_record(self):
        record_file_path = os.path.join(self.swconfig.logging_directory, 'RunningLog.csv')
        self.module_logger.debug('write {}'.format(record_file_path))
        with open(record_file_path, 'a') as fd:
            fd.write('{start_time};{program};{duration_est};{duration_real};{aenergy}\n'.format(
                start_time=self.program.time_start,
                program=self.program.selected_program,
                duration_est=int(self.program.estimated_runtime),
                duration_real=self.program.get_current_runtime(),
                aenergy=self.get_program_aenergy()
            ))


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
