# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#                       Romain Leclerc
#                       Nicolas Dorey
#
#   DESCRIPTION :       Updates json lib
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging
import json

from . import reads as read_json
from ..dicts import reads as read_dicts


def write_data_json(file_path, data):
    """
    Save dictionnary to json file
    :param: file_path
    :param: data
    :return: json new content
    :rtype: string
    """
    with open(file_path, 'w') as f:
        logging.info("file {} was created".format(file_path))
        return json.dump(data, f, indent=4)


# TODO: lowercase snakecase JSON_FILE
def update_dict(JSON_FILE, mesh_name, value_attr, new_value):
    """
    Read json data, find value for given mesh and update json file with new value.
    For ex:
    mesh_name = U_EnginePropeller01_001_Msh
    value_attr = POTENTIAL SYM
    new_value = False
    It will write into the dict given the new value of POTENTIAL SYM for
    the mesh U_EnginePropeller01_001_Msh, False in that case.
    :param JSON_FILE : path to the json.
    :type : str
    :param mesh_name : Name of mesh to find.
    :type : str
    :param value_attr : Name of the attr to find.
    :type : str
    :param new_value : New value for the entry of value_attr to update.
    :type: str
    """
    # json datas
    json_data = read_json.read_data_json(JSON_FILE)
    # read nested dictionnary until the value attr is found and then update it
    read_dicts.read_children(json_data, mesh_name, value_attr, new_value)
    # write the new datas into the json file.
    write_data_json(JSON_FILE, json_data)
