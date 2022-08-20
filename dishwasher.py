from config import HardwareConfig
import RPi.GPIO as GPIO
import time
import logging
import subprocess


class Dishwasher:
    """
    HARDWARE ABSTRACTION LAYER for the dishwasher hardware control.

    Write GPIO Outputs for relay board and read GPIO Inputs from sensor.
    """

    def __init__(self):
        # configuration
        self.hwconfig = HardwareConfig()
        self.module_logger = logging.getLogger('DishwasherOS.HAL')

        self.device_identifier = self.get_mac_address()
        self.in_wash_program = False
        self.step_transition_triggered = False
        self.debug_led_state = True

    def init_gpios(self):
        """initialize all GPIO inputs and outputs"""
        GPIO.setmode(GPIO.BCM)
        # initialize hardware outputs
        for pin in self.hwconfig.output_pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)

        # initialize hardware inputs
        for pin in self.hwconfig.input_pins.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # create interrupt event handler
        GPIO.add_event_detect(self.hwconfig.get_input_pin('sensorPinMotor'), GPIO.RISING,
                              bouncetime=50)
        GPIO.add_event_callback(self.hwconfig.get_input_pin('sensorPinMotor'),
                                self.step_transition_detected)

    def dispose_gpios(self):
        """cleanup GPIO pins after the program has finished."""
        if self.in_wash_program:
            self.module_logger.warning('GPIO cleanup in active program run called, aborting!')
        else:
            GPIO.cleanup()

    def get_mac_address(self):
        """the mac address of the device wlan0 is used as a clear identifier of the machine"""
        response_bytes = subprocess.run(['cat', '/sys/class/net/wlan0/address'], stdout=subprocess.PIPE)
        string = response_bytes.stdout.decode('utf-8')
        string = string.replace('\n', '')
        return string.strip()

    def step_transition_detected(self, channel):
        if self.in_wash_program and not self.step_transition_triggered:
            self.module_logger.debug('step transition detected')
            self.step_transition_triggered = True
        elif not self.in_wash_program:
            # self.module_logger.debug('step transition outside of program run detected')
            pass

    def read_program_sensor_values(self) -> dict[str, bool]:
        """return all GPIO Inputs for program selection detection"""
        return {
            'pinP4': GPIO.input(self.hwconfig.get_input_pin('sensorPinP4')),
            'pinP6': GPIO.input(self.hwconfig.get_input_pin('sensorPinP6')),
            'pinP7': GPIO.input(self.hwconfig.get_input_pin('sensorPinP7')),
            'pinP9': GPIO.input(self.hwconfig.get_input_pin('sensorPinP9')),
            'pinP10': GPIO.input(self.hwconfig.get_input_pin('sensorPinP10')),
            'pinP11': GPIO.input(self.hwconfig.get_input_pin('sensorPinP11')),
            'pinP12': GPIO.input(self.hwconfig.get_input_pin('sensorPinP12'))
        }

    def read_actuator_sensor_values(self) -> dict[str, bool]:
        """return all GPIO actuator stats"""
        return {
            'pump_drain': GPIO.input(self.hwconfig.get_input_pin('sensorPinMotor')),
            'pump_circulation': GPIO.input(self.hwconfig.get_input_pin('sensorPinUmwelz')),
            'valve_inlet': GPIO.input(self.hwconfig.get_input_pin('sensorPinEinlauf')),
            'valve_outlet': GPIO.input(self.hwconfig.get_input_pin('sensorPinAblauf')),
            'heating': GPIO.input(self.hwconfig.get_input_pin('sensorPinHeizen'))
        }

    def read_input(self, sensor_name: str) -> bool:
        """return bool GPIO value of one input sensor"""
        return GPIO.input(self.hwconfig.get_input_pin(sensor_name))

    def read_temperature(self) -> float:
        """read & convert the temperature sensor from bus"""
        file = open('/sys/bus/w1/devices/{}/w1_slave'.format(self.hwconfig.get_address('sesorTemp')))
        file_content = file.read()
        file.close()
        # read and convert temperature value
        string_value = file_content.split("\n")[1].split(" ")[9]
        return round(float(string_value[2:]) / 1000, 1)

    def set_all_relays(self, set_state: bool):
        """set all GPIO program relay outputs to set_state"""
        mode = GPIO.LOW if set_state is True else GPIO.HIGH
        GPIO.output(self.hwconfig.get_output_pin('relayPinP9'), mode)
        GPIO.output(self.hwconfig.get_output_pin('relayPinP7'), mode)
        GPIO.output(self.hwconfig.get_output_pin('relayPinP6'), mode)
        GPIO.output(self.hwconfig.get_output_pin('relayPinP4'), mode)

    def set_buzzer(self, passes: int):
        pin_name = self.hwconfig.get_output_pin('relayPinSummer')
        for i in range(0, passes):
            GPIO.output(pin_name, GPIO.LOW)
            time.sleep(0.5)
            GPIO.output(pin_name, GPIO.HIGH)
            time.sleep(1)

    def set_lamp(self, enable: bool):
        mode = GPIO.HIGH if enable is True else GPIO.LOW
        GPIO.output(self.hwconfig.get_output_pin('relayPinLamp'), mode)

    def flip_debug_led(self):
        """flip the state of the internal debug LED"""
        mode = GPIO.HIGH if self.debug_led_state is False else GPIO.LOW
        self.debug_led_state = not self.debug_led_state
        GPIO.output(self.hwconfig.get_output_pin('pinDebugLED'), mode)

    def reset_projector(self):
        """workaround for freezing projector microcontroller"""
        self.module_logger.info('reset projector microcontroller')
        GPIO.output(self.hwconfig.get_output_pin('pinResetProjector'), GPIO.LOW)
        time.sleep(0.15)
        GPIO.output(self.hwconfig.get_output_pin('pinResetProjector'), GPIO.HIGH)

    def set_main_relay(self, enable: bool):
        mode = GPIO.LOW if enable is True else GPIO.HIGH
        GPIO.output(self.hwconfig.get_output_pin('relayPinMain'), mode)