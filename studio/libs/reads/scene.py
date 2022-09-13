# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Utils for scene queries
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import logging
import glob
import json
import ast

try:
    import maya.cmds as cmds
except ImportError:
    pass

OUTFILE = 'C:/Shotgun/mm_profiles/PirataEtCapitano02/values.json'
INFILE = 'C:/Shotgun/mm_profiles/PirataEtCapitano02/values.json'


# TODO: snakecase filePath
# TODO: get_file_information => in english "information" doesn't have an "s" in plural
# TODO: Consider return a dictionary instead of 4 strings. Easier to use it
def get_file_informations(filePath=None):
    """
    Get the file path, file name, raw name and extension of current maya file / or the file you've specified
    :param: filePath
    :return: filePath, filename, rawname, extension
    :rtype: 4 strings
    """
    if not filePath:
        filePath = cmds.file(q=True, sn=True)
    filename = os.path.basename(filePath)
    rawname, extension = os.path.splitext(filename)
    return filePath, filename, rawname, extension


def get_latest_scene(file_path):
    """
    Get latest scene from exact path pattern
    file_path can be a string or a list string, only the first one will be used
    :param: file_path
    :return: files_in_folder[-1]
    :rtype: string
    """
    if isinstance(file_path, list) is True:
        file_path = file_path[0]
    file_folder, file_name, raw_name, extension = get_file_informations(file_path)
    files_in_folder = glob.glob('{}*'.format(file_path.split('.v')[0]))
    files_in_folder.sort()
    return files_in_folder[-1]


# TODO: snakecase pathList
def list_broken_paths(pathList):
    """
    WIP: The script should work without pathList by listing filepath, abcpath, proxypath etc. itself.  Use existing methods to get them
    :param: pathList => a list of path
    :return: broken_path_return, a list with all broken path in pathList
    :rtype: list
    """
    broken_path_return = []
    for path_to_check in pathList:
        if not os.path.exists(path_to_check):
            if not broken_path_return:
                logging.error("Broken path found:")
            logging.error(path_to_check)
            broken_path_return.append(path_to_check)
    if not broken_path_return:
        logging.info("No broken path found.")
    return broken_path_return


def get_timeline_framerange():
    """
    :return min_time and max_time
    :rtype: 2 integers
    """
    min_time = int(cmds.playbackOptions(q=True, ast=True))
    max_time = int(cmds.playbackOptions(q=True, aet=True))
    return min_time, max_time


def get_current_renderer():
    """
    Get the current renderer and those who are available.
    :return current_render, avail_renderers
    :rtype: string, list
    """
    current_renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")
    # List available renderer
    avail_renderers = cmds.renderer(query=True, namesOfAvailableRenderers=True)
    return current_renderer, avail_renderers


def get_render_framerange(shotName=None):
    """
    WIP: if shotName: get framerange from shot(shotgun?), else: get render framerange from current scene
    :param: shotName => None by default
    :return: start_frame and end_frame
    :rtype: 2 integers
    """
    if shotName:
        start_frame = "WIP: shotgun query? json?"
        end_frame = "WIP: shotgun query? json?"
    else:
        start_frame = int(cmds.getAttr('defaultRenderGlobals.startFrame'))
        end_frame = int(cmds.getAttr('defaultRenderGlobals.endFrame'))
    return start_frame, end_frame


def store_values():
    """
    Store transform values of meshes of scene inside a json
    :return: dict_transform
    :rtype: dict
    """
    # Store values
    dict_transform = {}
    if not os.path.exists(os.path.dirname(OUTFILE)):
        logging.error('Folder {} doesnt exists!'.format(OUTFILE))
        return
    meshes = cmds.ls(exactType="transform", long=True)
    transf_types = ['translate', 'rotate', 'scale']
    transf_axis = ['X', 'Y', 'Z']
    for mesh in meshes:
        transformsValues = []
        for tr_type in transf_types:
            for axis in transf_axis:
                value = cmds.getAttr("{}.{}{}".format(mesh, tr_type, axis))
                transformsValues.append(value)
        dict_transform[mesh] = transformsValues
    with open(OUTFILE, 'w') as outfile:
        json.dump(dict_transform, outfile)
    logging.info('Dictionary of values has been stored : {}'.format(OUTFILE))
    return dict_transform


def get_values_back():
    """
    Get values of transform back from json file
    :return: error_dict, dict of attrs which cannot be set with their values
    :rtype: dict
    """
    error_dict = {}
    if not os.path.isfile(INFILE):
        logging.error('File does not exist on system! Please try again!')
        return
    with open(INFILE) as json_file:
        dict_transform = json.load(json_file)
        logging.info('Values found : {}'.format(dict_transform))
    meshes = cmds.ls(exactType="transform", long=True)
    for mesh in meshes:
        if cmds.objExists(mesh):
            transf_types = ['translate', 'rotate', 'scale']
            transf_axis = ['X', 'Y', 'Z']
            key_transf = dict_transform[mesh]
            i = 0
            for tr_typ in transf_types:
                for axis in transf_axis:
                    attr = mesh + "." + tr_typ + axis
                    values = key_transf[i]
                    try:
                        cmds.setAttr(attr, values)
                        logging.info('Attribut "{}" value has been set to "{}"'.format(attr, values))
                    except Exception as e:
                        logging.error('Cannot set attribut "{}" with value "{}"'.format(attr, values))
                        error_dict[attr] = values
                    i += 1
    logging.info('Values have been restored from text file. See logs below for more details.')
    # Try to remove file from system
    try:
        os.remove(INFILE)
        logging.info('Text file has been deleted.')
    except Exception as e:
        logging.error(e)
    return error_dict


def get_shaders_stored(topnode, shader_type=None):
    """
    Get shaders to export in a given type (redshift or lambert)
    :param: topnode
    :param: shader_type => None by default
    :return: stored_shaders, list of shaders
    :rtype: list
    """
    dict_shdr = cmds.getAttr(topnode + ".notes")
    dict_shdr = ast.literal_eval(str(dict_shdr))
    stored_shaders = []
    for shading_grp, sg_dict in dict_shdr.items():
        if "shaders" in sg_dict.keys():
            shaders = sg_dict['shaders']
            for shader in shaders:
                if cmds.objExists(shader):
                    if shader_type:
                        if shader_type in cmds.objectType(shader):
                            stored_shaders.append(shader)
                    else:
                        stored_shaders.append(shader)
        else:
            raise ValueError('Shading group dictionnary has not shaders key!')
    return stored_shaders


# Unused
def list_abc_info():
    """
    WIP: should return a dict {nodeName: [filePath, os.file.exists?]}
    :rtype: dict
    """
    return cmds.ls(type="AlembicNode")
