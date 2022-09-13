
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Romain Leclerc
#                       Sophie Chauvet
#                       Nicolas Dorey
#
#   DESCRIPTION :       Updates dicts lib
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging


# TODO: snakecase myList
def convert_keys(d, myList):
    for key, value in d.items():
        if len(dict) > 1:
            myList.extend(convert_keys(d=value, myList=myList))
        else:
            myList.append(key)
            myList.append(value)
    return myList


# FIXME: clean this method! Rename it!
# FIXME: lvl=0 and then lvl=1!
# This is not really a READ method, recursive_read_children does update!
def read_children(json_data, mesh_name, value_attr, new_value):
    """
    Start ot dictionnary read
    :param: json_data, mesh_name, value_attr, new_value
    """
    for top_node, dico in json_data.items():
        lvl = 0
        # print "lvl", lvl, "key", top_node
        # print ''
        lvl = 1
        recursive_read_children(dico, mesh_name, value_attr, new_value, lvl)


def update_children(dico, value_attr, new_value):
    """
    Update current dictionary with new value
    """
    dico[value_attr] = new_value
    logging.info("Entry has been updated.")


# FIXME: rename function, this is not really a READ!
def recursive_read_children(dico, mesh_name, value_attr, new_value, lvl):
    """
    Recursive function to find the mesh name and update the value.
    :param dico : Dictionnary of each new level
    :type : dict
    :param lvl : increment of levels of each dictionary found.
    :type : int
    See also docstring of update_dict
    """
    for key, value in dico.items():
        # print 'lvl', lvl, "key", key
        if key == mesh_name:
            if value_attr in dico[mesh_name]:
                update_children(dico=dico[mesh_name], value_attr=value_attr, new_value=new_value)
                break
        if type(value) is dict:
            lvl += 1
            recursive_read_children(dico=value, value_attr=value_attr, mesh_name=mesh_name, new_value=new_value, lvl=lvl)


def convert_dict_to_flat_list(dictionary, flat_list=[]):
    """
    Helper function that creates a list out of all the keys and values present in the dictionary.
    :param: dictionary => the input dictionary
    :param: flat_list => Empty list by default, to be used by the recursion. For calling this function, skip this parameter
    :return: flat_list
    :rtype: list
    """
    for key, value in dictionary.iteritems():
        flat_list.append(key)
        if type(value) == dict:
            if isinstance(dictionary, dict):
                dictionary = value
                convert_dict_to_flat_list(dictionary, flat_list)

        elif type(value) == list:
            flat_list += value
    return flat_list


# FIXME: IMPORTANT! Cannot work because of obsolete import
# Method "get_infos" not found!
# from pirata2_tools.libraries.maya.libs.elts.infos import get_infos
# TODO: snakecase
def populate_dict(item, existing_dict, sourcePath, fullpath=None):
    if len(item) == 1:
        existing_dict[item[0]] = get_infos(sourcePath)
    else:
        head, tail = item[0], item[1:]
        existing_dict.setdefault(head, {})
        populate_dict(tail, existing_dict[head], sourcePath=sourcePath)


# TODO: snakecase
def build_path_to_populate(list_fullname):
    logging.info("process started")
    dict_assets = {}
    split_path = []
    for i in list_fullname:
        split_path = i.split("|")[1:]
        path_structure = []
        for part in split_path:
            path_structure.append("childrens")
            path_structure.append(part)
        populate_dict(item=path_structure,
                      existing_dict=dict_assets, sourcePath=i)
    logging.info("process completed")
    return dict_assets


def categories_build(list_category):
    dict_master = {}
    for category in list_category:
        name_category, list_fullname = category[0], category[1]
        dict_std = build_path_to_populate(list_fullname)
        dict_master[name_category] = dict_std
    return dict_master
