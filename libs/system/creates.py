# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           John Allard
#                       Nicolas Dorey
#
#   DESCRIPTION :       Creates system lib
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import logging
import shutil


def copy_files(source_path, destination_path, old_name, new_name, dry_run=False):
    for directory, folders, files in os.walk(source_path):
        for file in files:
            old_file_path = os.path.join(directory, file)
            new_file_path = old_file_path.replace(old_name, new_name)
            logging.info("old file : {}\nnew file : {}".format(old_file_path, new_file_path))
            if not dry_run:
                if os.path.exists(old_file_path) and not os.path.exists(new_file_path):
                    if not os.path.exists(os.path.dirname(new_file_path)):
                        os.makedirs(os.path.dirname(new_file_path))
                    shutil.copy(old_file_path, new_file_path)


def copy_directory(source_path, destination_path, dry_run=False):
    if not dry_run:
        try:
            shutil.copytree(source_path, destination_path)
        except Exception as e:
            logging.error(e)
