import requests

from state import State


class ProgramSelectionState(State):
    """
    The state which indicates that the operator sill need to select a program.
    formerly state 1
    """

    def program_selected(self):
        return WaitForBackendState(self.machine)


class WaitForBackendState(State):
    """
    The state in which the machine is waiting for a backend answer and delays the start of the program as required
    formerly state 2
    """

    def __init__(self, dishwasher):
        super().__init__(dishwasher)


    def doBackendCall(self):
        # start a backend request
        post_reg = requests.post('')

