import os
import re
import logging
import logging.config
from datetime import datetime
import json
import yaml

class UpdateAsciiString():
    """
    This class can be used to search and replace strings in ascii files like .ma, .nk
    It can be used to get informations by reading ascii and saving logs
    """

    #-----------------------------------------


    def get_files_from_folder(self, top_folders, extensions):
        # Get list of maya file in path_to_walk_on directory
        exclude = set(self.exclude_dirs)
        extensions = set(extensions)
        files_path_list = []
        for top_folder in top_folders:
            for root, dirs, files in os.walk(top_folder, topdown=True):
                dirs[:] = [d for d in dirs if d not in exclude]
                files = [file for file in files if os.path.splitext(file)[1] in extensions]
                for fname in files:
                    current_path_file = os.path.join(root, fname)
                    files_path_list.append(current_path_file)
                    self.logger.info('file found : {}'.format(current_path_file))

        return files_path_list


    def search_and_replace_in_file_with_regex(self, files_path_list, write=False):
        list_files_regex_detected=[]
        logger.info("START OF PROCESS.")

        for file_found in files_path_list:

            logger.info('Working on "{}"'.format(file_found))

            with open(file_found, 'r') as input_file:
                content = input_file.read()
                for regex in self.regex_list:
                    content_new = re.sub(regex, self.new_string, content)
                    regex_full_line = r".*{}.*".format(regex)
                    matches = re.finditer(regex, content, re.MULTILINE)
                    for matchNum, match in enumerate(matches, start=1):
                        list_files_regex_detected.append(file_found)
                        self.logger.warning('regex "{}" found in {} --> string :{}'.format(regex, file_found, match.group()))

                if write and content_new != content:
                    with open(file_found, 'w') as output_file:
                        output_file.write(content_new)
                        self.logger.info('file {} updated '.format(file_found))
        self.logger.info("END OF PROCESS.")
        return list_files_regex_detected


    def execute(self, logs_folder, top_folders, new_string, regex_list, exclude_dirs, extensions):
        self.logs_folder = logs_folder
        self.new_string = new_string
        self.regex_list = regex_list
        self.exclude_dirs = exclude_dirs
        # Where should the logs be save
        json_list_files_regex_detected = os.path.join(self.logs_folder, 'logs', 'list_files_regex_detected.json')
        if not os.path.exists(json_list_files_regex_detected):
            os.makedirs(json_list_files_regex_detected)
        log_filename = os.path.join(self.logs_folder, 'logs', 'analyse_ascii.log')
        if not os.path.exists(log_filename):
            os.makedirs(log_filename)
        # Configure logger
        with open(os.path.join(r'C:\Shotgun\tk-framework-millimages\python\millimages\maya\tools\PirataEtCapitano\tds', 'logging_config.yaml'), 'r') as stream:
            config = yaml.load(stream, Loader=yaml.FullLoader)
            config['handlers']['file']['filename'] = log_filename
            logging.config.dictConfig(config)
            # print(config)
        self.logger = logging.getLogger()
        # Save a list of all file to edit in a json
        list_files_regex_detected =[]
        with open(json_list_files_regex_detected, 'r') as files_list_json:
            list_files_regex_detected = json.load(files_list_json)
        list_files_regex_detected = self.search_and_replace_in_file_with_regex(self, sorted(list(dict.fromkeys(list_files_regex_detected))), write=False)
        with open(json_list_files_regex_detected, 'w') as outfile:
            json.dump(sorted(list(dict.fromkeys(list_files_regex_detected))), outfile)




# Path to walk on
# top_folders = [r"L:\Millimages\PirataEtCapitano\PirataEtCapitano02\ProjectFiles\assets"]
top_folders = [r"\\srv-data1\Roaming_profile$\n.dorey\Desktop\tests\masterscene"]
# Where should the logs be save
logs_folder = r'\\srv-data1\Roaming_profile$\n.dorey\Desktop\tests\masterscene'
# The strings you want to replace...
regex_list = [r"(.*\.rs.*)"]
#  ... by:
new_string = ""
# Folder you don't want to edit / In case of crash, put already treated asset folders name in exclude_dirs
exclude_dirs = ["reference", "DSN", 'jobs', 'review', 'tmp', 'photoshop', 'substancepainter', 'aftereffects', 'image', 'cache', 'fbx', 'alembic']
# Type of ascii file you want to edit (.ma, .nk, ...)
extensions = [".ma"]

# Launch process
UpdateAsciiString().execute(logs_folder, top_folders, new_string, regex_list, exclude_dirs, extensions)





'''
dir_path = os.path.dirname(os.path.realpath(__file__))
log_filename = os.path.join(dir_path, 'logs', 'analyse_ascii.log')

with open(os.path.join(dir_path, 'logging_config.yaml'), 'r') as stream:
    config = yaml.load(stream, Loader=yaml.FullLoader)
    config['handlers']['file']['filename'] = log_filename
    logging.config.dictConfig(config)
    # print(config)

logger = logging.getLogger()


def get_files_from_folder(top_folders, excludes_dirs, extensions, logger=logging):

    # Get list of maya file in path_to_walk_on directory

    exclude = set(excludes_dirs)
    extensions = set(extensions)
    files_path_list = []
    for top_folder in top_folders:
        for root, dirs, files in os.walk(top_folder, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude]
            files = [file for file in files if os.path.splitext(file)[1] in extensions]
            for fname in files:
                current_path_file = os.path.join(root, fname)
                files_path_list.append(current_path_file)
                logger.info('file found : {}'.format(current_path_file))

    return files_path_list


def search_and_replace_in_file_with_regex(files_path_list, new_string, regex_list, write=False, logger=logging):
    """
    :param: path_to_walk
    """
    list_files_regex_detected=[]
    logger.info("START OF PROCESS.")

    for file_found in files_path_list:

        logger.info('Working on "{}"'.format(file_found))

        with open(file_found, 'r') as input_file:
            content = input_file.read()
            for regex in regex_list:
                content_new = re.sub(regex, new_string, content)
                regex_full_line = r".*{}.*".format(regex)
                matches = re.finditer(regex, content, re.MULTILINE)
                for matchNum, match in enumerate(matches, start=1):
                    list_files_regex_detected.append(file_found)
                    logger.warning('regex "{}" found in {} --> string :{}'.format(regex, file_found, match.group()))

            if write and content_new != content:
                with open(file_found, 'w') as output_file:
                    output_file.write(content_new)
                    logger.info('file {} updated '.format(file_found))

    logger.info("END OF PROCESS.")

    return list_files_regex_detected


# Path to walk on
top_folders = [r"L:\Millimages\PirataEtCapitano\PirataEtCapitano02\ProjectFiles\assets"]
# The string you want to replace...

new_assets_path = ""
# Logs obsolete/wrong strings in your ascii

regex_list = [r"(.*\.rs.*)"]
# Folder you don't want to edit
# In case of crash, put already treated asset folders name in exception_directory
excludes_dirs = ["reference", "DSN", 'jobs', 'review', 'tmp', 'photoshop', 'substancepainter', 'aftereffects', 'image', 'cache', 'fbx', 'alembic']
extensions = [".ma"]
# Launch process

# files_list = get_files_from_folder(top_folders, excludes_dirs, extensions, logger=logger)

# json_filename = os.path.join(dir_path, 'logs', 'list_files_to_process.json')

# with open(json_filename, 'w') as outfile:
#     json.dump(sorted(files_list), outfile)


# with open(json_filename, 'r') as files_list_json:
#     files_list = json.load(files_list_json)

# list_files_regex_detected = search_and_replace_in_file_with_regex(files_list, new_assets_path, regex_list, write=False, logger=logger)

json_list_files_regex_detected = os.path.join(dir_path, 'logs', 'list_files_regex_detected.json')

# with open(json_list_files_regex_detected, 'w') as outfile:
#     json.dump(sorted(list(dict.fromkeys(list_files_regex_detected))), outfile)

list_files_regex_detected =[]
with open(json_list_files_regex_detected, 'r') as files_list_json:
    list_files_regex_detected = json.load(files_list_json)

list_files_regex_detected = search_and_replace_in_file_with_regex(sorted(list(dict.fromkeys(list_files_regex_detected))), new_assets_path, regex_list, write=False, logger=logger)
'''