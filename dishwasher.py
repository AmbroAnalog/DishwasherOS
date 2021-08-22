from config import HardwareConfig
import RPi.GPIO as GPIO


class Dishwasher():

    def __init__(self):
        self.pump_drain = False
        self.pump_circulation = False
        self.valve_inlet = False
        self.valve_outlet = False
        self.heating = False
        self.in_thermostop = False  # TODO need to implement
        self.temperature = 0.0

        self.hwconfig = HardwareConfig()

    def init_gpios(self):
        GPIO.setmode(GPIO.BCM)
        # initialize hardware outputs
        for pin in self.hwconfig.output_pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)

        # initialize hardware inputs
        for pin in self.hwconfig.input_pins.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def read_values(self):
        self.pump_drain = GPIO.input(self.hwconfig.get_input_pin('sensorPinMotor'))
        self.pump_circulation = GPIO.input(self.hwconfig.get_input_pin('sensorPinUmwelz'))
        self.valve_inlet = GPIO.input(self.hwconfig.get_input_pin('sensorPinEinlauf'))
        self.valve_outlet = GPIO.input(self.hwconfig.get_input_pin('sensorPinAblauf'))
        self.heating = GPIO.input(self.hwconfig.get_input_pin('sensorPinHeizen'))

        self.temperature = self.__read_temperature()

    def __read_temperature(self):
        file = open('/sys/bus/w1/devices/{}/w1_slave'.format(self.hwconfig.get_address('sesorTemp')))
        file_content = file.read()
        file.close()
        # read and convert temperature value
        string_value = file_content.split("\n")[1].split(" ")[9]
        return round(float(string_value[2:]) / 1000, 1)
