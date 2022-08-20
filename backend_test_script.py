import requests
import json
import time
import random
from config import SoftwareConfig

swconfig = SoftwareConfig()
session_id = int(time.time())
runtime = 0  # in seconds
complete_runtime = 3300


def send_example_push_alive():
    base_url = swconfig.backend_base_url
    base_url = base_url.rstrip('/')
    target_api_url = base_url + '/insert/is_alive/'
    process_data = {
        'session_id': session_id,
        'device_identifier': '00:00:5e:00:53:af'}
    try:
        resp = requests.post(target_api_url, verify=False, json=process_data)
        print(' [{}] send example_push_alive post'.format(resp.status_code), json.dumps(process_data))
    except requests.exceptions.RequestException as e:
        # backend call raised an exception
        print('backend call raised an exception')


def get_simulated_program_runtimes():
    # time_start = sessionid
    time_left = complete_runtime - runtime
    return {
        'runtime': runtime,
        'progress': int((runtime / (time_left + runtime)) * 100),
        'step_operational': round((runtime / (time_left + runtime)) * 59),
        'step_sequence': round((runtime / (time_left + runtime)) * 7),
        'time_left': time_left,
    }


def send_example_push_data():
    runtimes = get_simulated_program_runtimes()
    process_data = {
        'session_id': session_id,
        'device_identifier': '00:00:5e:00:53:af',
        'program_runtime': runtime,
        'program_progress_percent': runtimes['progress'],
        'program_step_operational': runtimes['step_operational'],
        'program_step_sequence': runtimes['step_sequence'],
        'program_selected_id': 6,
        'program_estimated_runtime': complete_runtime,
        'program_time_start': session_id,
        'program_time_end': None,
        'program_time_left_step': 10,
        'program_time_left_sequence': 20,
        'program_time_left_program': runtimes['time_left'],
        'machine_temperature': round(random.uniform(20.0, 50.0), 1),
        'machine_sensor_values': {
            'pump_drain': 0,
            'pump_circulation': 1,
            'valve_inlet': 0,
            'valve_outlet': 0,
            'heating': 1},
        'machine_aenergy': 33,
        'machine_apower': random.randint(199, 3000)
    }
    base_url = swconfig.backend_base_url
    base_url = base_url.rstrip('/')
    target_api_url = base_url + '/insert/run_state/'
    try:
        resp = requests.post(target_api_url, verify=False, json=process_data)
        print(' [{}] send example_push_data post'.format(resp.status_code), json.dumps(process_data))
    except requests.exceptions.RequestException as e:
        # backend call raised an exception
        print('backend call raised an exception')


if __name__ == "__main__":
    print('START dishwasher program simulation...')
    while runtime < complete_runtime:
        runtime += 1

        send_example_push_alive()
        # send_example_push_data()

        time.sleep(1)
    print('END dishwasher program simulation')
