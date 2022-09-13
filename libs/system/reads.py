# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#                       Nicolas Dorey
#
#   DESCRIPTION :       Reads system lib
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import glob
import re


def found_scenes(path, file_extension, include, exclude):
    """
    Get scenes which have file_extension
    Can include or exclude a string
    :param: path, file_extension, include, exclude
    :return: files_list
    :rtype: list
    """
    file_pattern = '{}{}*{}'.format(path, os.sep, file_extension)
    exclude_list = []
    if include is not None:
        files_list = [fn for fn in glob.glob(file_pattern) if include in os.path.basename(fn)]
        if exclude:
            for file_found in files_list:
                if exclude not in file_found:
                    exclude_list.append(file_found)
                    return exclude_list
    elif exclude is not None and include is None:
        files_list = [fn for fn in glob.glob(file_pattern) if exclude not in os.path.basename(fn)]
    elif exclude is None and include is None:
        files_list = glob.glob(file_pattern)
    return files_list


def get_latest_version_timestamp(files):
    """
    Get latest version from timestamp
    :param: files
    :rtype: string
    """
    latest_file = None
    if files:
        latest_file = max(files, key=os.path.getctime)
    return latest_file


# TODO: snakecase customRegex
def get_lastest_version_digit(path, extention, customRegex=None):
    """
    Get latest version of files based on folder content.
    :param: path => path to search files
    :param: extention => extention to filter files
    :param: customRegex => customize the search of version digits
    :return: final_name
    :rtype: string
    """
    files = glob.glob(path + '/*.%s' % extention)
    files.sort()
    last_file = files[-1]
    final_name = str(last_file)
    if customRegex:
        digits = re.compile(customRegex)
    else:
        digits = re.compile(r'v\d\d\d')
    fill_lenght = 3
    match = digits.search(final_name)
    if match is not None:
        match = str(match.group().replace('v', ''))
        int_match = int(match)
        final_name = final_name.replace(match, str(int_match).zfill(fill_lenght))
        new_name = final_name.replace(match, '{}')
        while os.path.exists(new_name.format(str(int_match).zfill(fill_lenght))):
            final_name = new_name.format(str(int_match).zfill(fill_lenght))
            int_match += 1
        int_match += 1
    return final_name
