import time

from config import SoftwareConfig
from dishwasher import Dishwasher


class WashingProgram:
    """
    SOFTWARE ABSTRACTION LAYER for the dishwasher process control.

    This class contains hardcoded individual program sequences for the Miele G 470.
    Other machines require adaptation!
    """

    def __init__(self, machine: Dishwasher):
        self.machine = machine

        # process associated variables
        self.selected_program = 1
        self.step_operational = 1
        self.step_sequence = 1
        self.time_step_operational_start = time.time()
        self.thermostop_starttemp = 0

        # configuration
        self.swconfig = SoftwareConfig()

    def get_program_name(self):
        program_map = {
            1: "VDE - 0",
            2: "Stop - Start",
            3: "Intensiv 65°C",
            4: "Universal Plus 65°C",
            5: "Universal Plus 55°C",
            6: "Universal 65°C",
            7: "Universal 55°C",
            8: "Spar 65°C",
            9: "Spar 55°C",
            10: "Kurz 45°C",
            11: "Fein 45°C",
            12: "Kalt"
        }
        return program_map.get(self.selected_program, "Invalid")

    def __scan_selected_program(self):
        """private function to get selected program by reading sensor states"""
        sensor_values = self.machine.read_program_sensor_values()
        if sensor_values.get('pinP4'):
            if sensor_values.get('pinP9'):
                return 10
            if sensor_values.get('pinP12'):
                return 9
            else:
                return 11
        if sensor_values.get('pinP11'):
            if sensor_values.get('pinP12'):
                return 2
            else:
                return 12
        if sensor_values.get('pinP6'):
            if sensor_values.get('pinP7'):
                return 5
            else:
                return 7
        if sensor_values.get('pinP7'):
            return 4
        if sensor_values.get('pinP10'):
            if sensor_values.get('pinP12'):
                return 8
            else:
                return 6
        return 3

    def get_sequence_steplength(self):
        sequence_map = {
            0: 0,
            1: 8,
            2: 6,
            3: 10,
            4: 10,
            5: 11,
            6: 11,
            7: 4
        }
        return sequence_map.get(self.step_sequence, 0)

    def get_last_sequence_step(self):
        sequence_map = {
            1: 8,
            2: 14,
            3: 24,
            4: 34,
            5: 45,
            6: 56,
            7: 60
        }
        return sequence_map.get(self.step_sequence, 0)

    def get_sequence_name(self):
        sequence_map = {
            0: "Stop - Start",
            1: "1. Vorspülen",
            2: "2. Vorspülen",
            3: "Reinigen",
            4: "Zwichenspülen",
            5: "Klarspülen",
            6: "Trocknen",
            7: "Auslaufen"
        }
        return sequence_map.get(self.step_sequence, "Invalid")

    def get_target_temp(self, step_id=0):
        if step_id == 0:
            var = self.step_operational
        else:
            var = step_id
        if 1 <= var <= 8:
            if self.selected_program == 3:
                return 66
        if 15 <= var <= 24:
            if self.selected_program in [3, 4, 6, 8]:
                return 66
            elif self.selected_program in [5, 7, 9]:
                return 56
            elif self.selected_program in [10, 11]:
                return 45
        if 35 <= var < 39:
            if 3 <= self.selected_program <= 11:
                return 45
        if 39 <= var <= 45:
            if self.selected_program in [3, 4, 5, 6, 7, 8]:
                return 66
            elif self.selected_program in [9, 10, 11]:
                return 56
        return 0

    def is_thermo_stop(self, step_id=0):
        if step_id == 0:
            var = self.step_operational
        else:
            var = step_id
        if var in [7, 19, 38, 40]:
            return True
        else:
            return False

    def get_operational_time(self, step_id=0):
        operational_map = {
            1: 0.5,
            2: 0.5,
            3: 0.5,
            4: 1,
            5: 0.5,
            6: 4,
            7: 0.5,
            8: 0.5,
            9: 0.5,
            10: 1,
            11: 1,
            12: 4,
            13: 4,
            14: 0.5,
            15: 0.5,
            16: 1,
            17: 1,
            18: 0.5,
            19: 0.5,
            20: 4,
            21: 4,
            22: 1,
            23: 1,
            24: 0.5,
            25: 0.5,
            26: 0.5,
            27: 0.5,
            28: 1,
            29: 0.5,
            30: 0.5,
            31: 0.5,
            32: 0.5,
            33: 1,
            34: 0.5,
            35: 0.5,
            36: 1,
            37: 1,
            38: 0.5,
            39: 0.5,
            40: 0.5,
            41: 0.5,
            42: 0.5,
            43: 0.5,
            44: 0.5,
            45: 0.5,
            46: 0.5,
            47: 0.5,
            48: 0.5,
            49: 0.5,
            50: 1,
            51: 4,
            52: 0.5,
            53: 4,
            54: 0.5,
            55: 0.5,
            56: 1,
            57: 1,
            58: 4,
            59: 4,
        }
        if step_id == 0:
            return operational_map.get(self.step_operational, 0)
        else:
            return operational_map.get(step_id, 0)

    def check_program_sync(self):
        newstep_operational = 0
        valve_outlet = self.machine.read_input('sensorPinAblauf')
        if valve_outlet:
            if 16 <= self.step_operational <= 19:
                newstep_operational = 15
            if 20 <= self.step_operational <= 23:
                newstep_operational = 24
            if 26 <= self.step_operational <= 29:
                newstep_operational = 25
            if 30 <= self.step_operational <= 33:
                newstep_operational = 34
            if 36 <= self.step_operational <= 40:
                newstep_operational = 35
            if 41 <= self.step_operational <= 43:
                newstep_operational = 44
            if 52 <= self.step_operational <= 55:
                newstep_operational = 56
        if newstep_operational != 0:
            # TODO rework print statement
            print("DESYNC!!! oldStep: " + str(self.step_operational) + "  newStep: " + str(newstep_operational) + ".")
            print("status: " + str(valve_outlet))
            self.set_new_operational_step(newstep_operational)

    def get_next_step_operational(self, get_next_step=False, step_id=0):
        if step_id == 0:
            step = self.step_operational
        else:
            step = step_id
        newstep_operational = 0
        if self.selected_program in [4, 5]:
            if step == 6:
                newstep_operational = 8
        if self.selected_program in [6, 7, 11, 12]:
            if 2 <= step <= 8:
                if not get_next_step:
                    self.step_sequence = 2
                newstep_operational = 9
        if self.selected_program in [8, 9, 10]:
            if 2 <= step <= 14:
                if not get_next_step:
                    self.step_sequence = 3
                newstep_operational = 15
        if self.selected_program == 10:
            if step == 19:
                newstep_operational = 24
            if step == 28:
                newstep_operational = 34
            if step == 40:
                newstep_operational = 44
            if step == 47:
                newstep_operational = 56
        if self.selected_program == 12:
            if 14 <= step <= 55:
                newstep_operational = 56
                if not get_next_step:
                    self.step_sequence = 6
            if 56 <= step <= 59:
                newstep_operational = 60
                if not get_next_step:
                    self.step_sequence = 7
        if get_next_step:
            if newstep_operational == 0:
                return step + 1
            else:
                return newstep_operational
        if newstep_operational == 0:
            self.set_new_operational_step(step + 1)
        else:
            self.set_new_operational_step(newstep_operational)

    def get_time_left_operationalstep(self):
        time_now = time.time()
        time_run = time_now - self.time_step_operational_start
        if self.is_thermo_stop():
            temp_now = self.machine.read_temperature()
            temp_target_sensor = self.swconfig.get_program_target_temps(self.get_target_temp())

            gradient = self.swconfig.temp_growth_speed
            time_total = (temp_target_sensor - self.thermostop_starttemp) / gradient
            time_curr = (temp_now - self.thermostop_starttemp) / gradient
            time_left = round(time_total - time_curr)
        else:
            time_left = round((self.get_operational_time() * 60) - time_run)
        return int(time_left)

    def get_time_left_sequence_step(self):
        step_last = self.get_last_sequence_step()
        time_left = self.get_time_left_operationalstep()
        if self.step_operational != step_last:
            i = self.get_next_step_operational(True, self.step_operational)
            time_left += self.get_runtime_for_steps(i, step_last + 1)
        return time_left

    def get_time_left_program(self):
        time_left = self.get_time_left_operationalstep()
        if self.step_operational < 57:
            i = self.get_next_step_operational(True, self.step_operational)
            time_left += self.get_runtime_for_steps(i, 57)
        return time_left

    def get_runtime_for_steps(self, step_start, step_end):
        i = step_start
        time_left = 0
        while i < step_end:
            if self.is_thermo_stop(i):
                if i == 38:
                    temp_start = 25
                elif i == 40:
                    temp_start = 35
                else:
                    temp_start = 17
                temp_target_sensor = self.swconfig.get_program_target_temps(self.get_target_temp())

                gradient = self.swconfig.temp_growth_speed
                time_head = (temp_target_sensor - temp_start) / gradient
                time_left += round(time_head)
            else:
                time_left += self.get_operational_time(i) * 60
            i = self.get_next_step_operational(True, i)
        return time_left

    def set_new_operational_step(self, step_new):
        self.step_operational = step_new
        self.time_step_operational_start = time.time()
        # check if sequence is finished
        if self.step_operational > self.get_last_sequence_step():
            # start next sequence
            self.step_sequence += 1
        if self.is_thermo_stop():
            self.thermostop_starttemp = self.machine.read_temperature()

    def find_selected_program(self):
        """find the selected program by toggle relays and read sensor response"""
        self.machine.set_all_relays(True)
        time.sleep(0.5)
        self.selected_program = self.__scan_selected_program()
        self.machine.set_all_relays(False)
