
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#                       Nicolas Dorey
#
#   DESCRIPTION :       Updates system lib
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import re


def increment_file(path):
    """
    Increment file with 'v%03d' pattern
    :param: path
    :return: same path with version +1
    :rtype: string
    """
    file_name = os.path.basename(path)
    version = re.findall(r'v\d+', file_name)[0]
    new_version = r'v%03d' % (int(version.replace('v', '')) + 1)
    return path.replace(version, new_version)
