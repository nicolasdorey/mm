# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Romain Leclerc
#
#   DESCRIPTION :       Replace strings in ascii files and logs what has been update
#                       Two modes! first one logs what will be change, the other will edit ascii
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import re
import logging
import logging.config
import json
import sys
import time

from ..logger import extra_logger


class UpdateAsciiString(object):
    """
    This class can be used to search and replace strings in ascii files like .ma, .nk
    It can be used to get informations by reading ascii and saving logs
    """

    def __init__(self,
                 top_folders=None,
                 new_string=None,
                 regex_list=[""],
                 log_path='logs',
                 export_json_folder='jsons',
                 export_logs_folder='logs',
                 exclude_dirs=[""], extensions=[".*"],
                 write=False,
                 loadExistingFile=None):

        self.current_dir = os.path.dirname(os.path.realpath(__file__))
        self.is_load_existing_file = False
        self.files_jsons_exported = []
        self.timestr = time.strftime("%Y%m%d-%H%M%S")

        self.export_json_folder = export_json_folder

        if len(os.path.dirname(log_path)) == 0:
            self.log_path = os.path.join(self.current_dir, export_logs_folder, "{}_{}.log".format(log_path, self.timestr))
        else:
            if os.path.exists(log_path):
                self.log_path = log_path
            else:
                logging.error("Invalid log_path!")
                sys.exit()

        self.top_folders = top_folders
        self.new_string = new_string
        self.regex_list = regex_list
        self.exclude_dirs = exclude_dirs
        self.extensions = extensions
        self.write = write
        self.loadExistingFile = loadExistingFile
        # Prepare extra log
        self.extra_logger = extra_logger.ExtraLogger()
        self.extra_logger.execute_logger(self.log_path)
        self.extra_logging = logging.getLogger()


    def init_logs(self):
        if self.write is False:
            self.extra_logging.info("START OF PROCESS - SCAN")
        else:
            self.extra_logging.info("START OF PROCESS - UPDATE")


    def get_files_from_folder(self):
        """
        :return: list_files_found
        :rtype: list
        """
        list_files_found = []
        if self.loadExistingFile is not None:
            try:
                with open(self.loadExistingFile, 'r') as files_list_json:
                    list_files_found = json.load(files_list_json)
                    self.is_load_existing_file = False
            except Exception as e:
                self.extra_logging.error('File "{}" doesnt exist \n details:\n{}'.format(files_list_json, e))
        else:
            self.is_load_existing_file = True
            # Get list of file in path_to_walk_on directory
            exclude = set(self.exclude_dirs)
            extensions = set(self.extensions)
            files_path_list = []

            for root, dirs, files in os.walk(self.top_folders, topdown=True):
                dirs[:] = [d for d in dirs if d not in exclude]
                files = [file for file in files if os.path.splitext(file)[1] in extensions]
                for fname in files:
                    current_path_file = os.path.join(root, fname)
                    files_path_list.append(current_path_file)
                    self.extra_logging.info('File found: {}'.format(current_path_file))
            list_files_found = sorted(list(dict.fromkeys(files_path_list)))

        return list_files_found


    def search_and_replace_in_file_with_regex(self, files_path_list):
        """
        :param: files_path_list
        :return: sorted(list(dict.fromkeys(list_files_regex_detected)))
        :rtype: list
        """
        list_files_regex_detected = []
        for file_found in files_path_list:

            self.extra_logging.info('Working on "{}"'.format(file_found))

            with open(file_found, 'r') as input_file:
                content = input_file.read()
                for regex in self.regex_list:
                    matches = re.finditer(regex, content, re.MULTILINE)
                    for match in matches:
                        list_files_regex_detected.append(file_found)
                        self.extra_logging.warning('regex "{}" found in {} --> string :{}'.format(regex, file_found, match.group()))
                if self.write:
                    if self.new_string is None:
                        self.extra_logging.error("Cannot replace string with nothing! Put your new string: {}".format(self.new_string))
                    content_new = re.sub(regex, self.new_string, content)
                    if content_new != content:
                        with open(file_found, 'w') as output_file:
                            output_file.write(content_new)
                            self.extra_logging.info('File {} updated '.format(file_found))
        return sorted(list(dict.fromkeys(list_files_regex_detected)))


    def export_json(self, filename, data):
        '''
        Supress duplicated items and sort list before export json
        :param: filename, data
        :return: True or False
        :rtype: boolean
        '''

        file_path = os.path.join(self.current_dir, self.export_json_folder, "{}_{}.json".format(filename, self.timestr))
        self.extra_logging.info("jsonfile : {}".format(file_path))
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
            if not os.path.exists(file_path):
                jsonfile = open(file_path, 'a').close()
        try:
            with open(file_path, 'w') as outfile:
                json.dump(data, outfile, indent=4)
            self.files_jsons_exported.append(file_path)
            return True
        except Exception as e:
            self.extra_logging.error("error during write json file : {}".format(e))
            return False


    def execute(self):
        """
        Execute script
        """
        self.init_logs()
        filename = ""
        list_files_found = self.get_files_from_folder()
        if self.is_load_existing_file is True:
            self.export_json(filename="file_found", data=list_files_found)
        list_files_regex_detected = self.search_and_replace_in_file_with_regex(list_files_found)

        if self.write is True:
            filename = "files_edited"
        else:
            filename = "files_regex_found"

        self.export_json(data=list_files_regex_detected, filename=filename)

        self.extra_logging.info("END OF PROCESS.")

        return {"files_found": list_files_found,
                "files_regex_detected": list_files_regex_detected,
                "log_path": self.log_path,
                "jsons_files": self.files_jsons_exported}


# if __name__ == "__main__":
#     top_folders = "L:/Millimages/PirataEtCapitano/PirataEtCapitano02/ProjectFiles/assets/TestBalloonFish01"
#     # Folder you don't want to edit / In case of crash, put already treated asset folders name in exclude_dirs
#     exclude_dirs = ["reference", 'jobs', 'DSN', 'review', 'tmp', 'photoshop', 'substancepainter', 'aftereffects', 'image', 'cache', 'fbx', 'alembic']
#     # Type of ascii file you want to edit (, .ma, .nk, ...)
#     extensions = [".ma"]
#     regex_list = ["(BalloonFish01)"]
#     new_string = "TestBalloonFish01"
#     loadExistingFile = r"C:\Shotgun\tk-framework-millimages\python\millimages\maya\tools\Common\tds\jsons\file_found_20200610-154906.json"
#     tree_ops = UpdateAsciiString(top_folders=top_folders,
#                                  new_string=new_string,
#                                  regex_list=regex_list,
#                                  exclude_dirs=exclude_dirs,
#                                  extensions=extensions,
#                                  loadExistingFile=loadExistingFile,
#                                  write=False)

#     results = tree_ops.execute()
#     tree_ops.extra_logging.info("RESULTS :{}".format(results))
