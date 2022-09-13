# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Romain Leclerc
#
#   DESCRIPTION :       Custom logger, usefull for debug (used in a lot of our tools)
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import logging
import logging.config
import json


class ExtraLogger(object):
    """
    Custom logger for TDs
    logging_config.json should always be in the same folder as extra_logger.py
    You can use another logging_config if needed.
    """
    def execute_logger(self, logs_path, logs_config=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logging_config.json')):
        # Where the logs should be saved. Logs should always be in a "logs" folder!
        log_folder = os.path.dirname(logs_path)
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        # Configure logger
        with open(logs_config, 'r') as stream:
            config = json.load(stream)
            config['handlers']['file']['filename'] = logs_path
            logging.config.dictConfig(config)
        self.logger = logging.getLogger()

# if __name__ == "__main__":
#     log_path = r'\\srv-data1\Roaming_profile$\n.dorey\Desktop\tests\masterscene\logs\remove_redshift_stuff.log'
#     ExtraLogger().execute_logger(log_path)
