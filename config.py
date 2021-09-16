import yaml


class Config:

    def __init__(self):
        self._config = self.load_configuration()['dishwasher']

    def load_configuration(self):
        with open('settings.yaml', 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exe:
                print(exe)
                return None

    def get_property(self, property_name):
        if property_name not in self._config.keys():
            return None
        return self._config[property_name]


class HardwareConfig(Config):

    def __init__(self):
        super().__init__()
        self._hwconfig = self.get_property('hardware')

    @property
    def output_pins(self):
        return self._hwconfig.get('outputs')

    @property
    def input_pins(self):
        return self._hwconfig.get('inputs')

    def get_output_pin(self, pin_name):
        return self._hwconfig.get('outputs').get(pin_name)

    def get_input_pin(self, pin_name):
        return self._hwconfig.get('inputs').get(pin_name)

    def get_address(self, name):
        return self._hwconfig.get('addresses').get(name)


class SoftwareConfig(Config):

    def __init__(self):
        super().__init__()
        self._swconfig = self.get_property('software')

    @property
    def loop_sleep_time(self):
        return self._swconfig.get('loopSleepTime')

    @property
    def backend_base_url(self):
        return self._swconfig.get('backendBaseUrl')

    @property
    def logging_directory(self):
        return self._swconfig.get('loggingDirectory')

    @property
    def temp_growth_speed(self):
        return self._swconfig.get('programTargetTemps').get('tempGrowthSpeed')

    def get_program_target_temps(self, program_target):
        return self._swconfig.get('programTargetTemps').get('targetTemp{}'.format(program_target))
