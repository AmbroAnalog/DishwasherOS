
import time

import logger
from dishwasher import Dishwasher
from program import WashingProgram
import logging

logger.setup_logger()
module_logger = logging.getLogger('DishwasherOS.main')

module_logger.info('load main module')


dishwasher = Dishwasher()
dishwasher.init_gpios()
program = WashingProgram(dishwasher)
data_provider = logger.ProcessDataProvider(program)


# get selected program
dishwasher.set_buzzer(1)
program.find_selected_program()


while program.selected_program == 2:
    module_logger.info('no program selected by user... waiting and try again after 30 sec.')
    time.sleep(30)
    program.find_selected_program()

module_logger.info("start with washing program '{}' (nr {})".format(program.get_program_name(), program.selected_program))
module_logger.info("estimated program duration: {} min".format(int(program.get_time_left_program()/60)))

# start the dishwasher intern program
program.start_program()

# define variables for in_program loop
step_transition = 0
running_loop_counter = 0
current_temperature = 0.0

while dishwasher.in_wash_program:

    step_transition_is_triggered = dishwasher.step_transition_triggered
    dishwasher.step_transition_triggered = False

    old_step_operational = program.step_operational
    time_left_step = program.get_time_left_operationalstep()
    runtime_step_operational = time.time() - program.time_step_operational_start
    current_temperature = dishwasher.read_temperature()

    # process step transition in program module
    if step_transition_is_triggered:
        if step_transition == 0:
            if old_step_operational in [7, 19, 38, 40]:
                # TODO log heating step here
                pass
            module_logger.debug('step {} took {}s'.format(old_step_operational, time_left_step))
            program.get_next_step_operational()
        step_transition += 1
    elif program.step_operational >= 56 and time_left_step < 0:
        step_transition = 0
        program.get_next_step_operational()
    else:
        step_transition = 0

    # check for hardware-software step desynchronization
    program.check_program_sync()

    # write cvs log column to file
    data_provider.write_csv_data_record()

    if program.step_operational != old_step_operational:
        # the program has gone one step forward
        module_logger.debug('begin new step {}'.format(program.step_operational))

    # TODO do a post request to web provider in the ProcessDataProvider class

    running_loop_counter += 1
    time.sleep(1)

# TODO all post program steps
pass
