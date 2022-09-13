# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie #
#
#   DESCRIPTION :       Utils for nodes deletion
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         glob var problem in found_maya_scene. Unfound rendersetup
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging

try:
    import maya.cmds as cmds
    import maya.mel as mel
except ImportError:
    pass

from ..reads import nodes as read_nodes
from ..updates import nodes as update_nodes


TEMP_SUFFIX = "_TMP"


# _________________________________________________________________________________________________________
# #########################
# ------MANAGE MESHES-----#
# #########################

# TODO: need to return what has been changed
def remove_instance(mesh):
    """
    Remove instance of mesh
    :param: mesh
    """
    shape = read_nodes.get_shape_or_transform(mesh)
    parents = cmds.listRelatives(shape, ap=True)
    if TEMP_SUFFIX in shape:
        cmds.rename(shape, shape.replace(TEMP_SUFFIX, ''))
    for parent in parents:
        tmp_name = parent + TEMP_SUFFIX
        cmds.rename(parent, tmp_name)
        if cmds.objExists(parent):
            parent = update_nodes.increment_name(parent)
        cmds.duplicate(tmp_name, name=parent)
        cmds.delete(tmp_name)


# Unused
# TODO: call delete_nodes instead of cmds.delete, append obj_parent to nodesList
def delete_geometry(shapesList):
    """
    Delete shapesList (shapes and transforms)
    :param: shapesList => must be shapes list
    :return: deleted_list
    :rtype: list
    """
    deleted_list = []
    for obj in shapesList:
        try:
            obj_parent = cmds.listRelatives(obj, p=True)[0]
        except Exception as e:
            logging.warning(e)
            obj_parent = []
        try:
            cmds.delete(obj, s=True)
            deleted_list.append(obj)
            if obj_parent:
                cmds.delete(obj_parent)
                deleted_list.append(obj_parent)
        except Exception as e:
            logging.warning(e)
            pass
    return deleted_list


# Used in utils_scene, out_task_asset
# TODO: snakecase
# TODO: Change the name to "delete_node_list()" to avoid conflict with module name "delete_nodes" (current module shortname)
def delete_nodes(nodesList):
    """
    Delete nodes whatever type they are
    :param: nodesList
    :return: deleted_list
    :rtype: list
    """
    deleted_list = []
    for item in nodesList:
        try:
            cmds.lockNode(item, lock=False)
            cmds.delete(item)
            deleted_list.append(item)
            logging.info('"{}" has been deleted.'.format(item))
        except Exception as e:
            logging.error('Cant delete item: "{}"'.format(e))
            pass
            try:
                cmds.deleteUI(item)
            except Exception as e:
                logging.error('Cant delete deleteUI: "{}"'.format(e))
                pass
    return deleted_list


# _________________________________________________________________________________________________________
# #########################
# ------MANAGE SETS-------#
# #########################

# Used in SC, detect_sym_auto
# TODO: snakecase
def delete_sets(setsList=None):
    """
    Delete selected sets arg: cmds.ls(sl=True, set=True)
    :param: setsList => None by default
    :return: deleted_list
    :rtype: list
    """
    deleted_list = []
    all_sets = read_nodes.list_non_default_set() if not setsList else setsList
    if all_sets:
        for current_set in all_sets:
            try:
                cmds.delete(current_set)
                deleted_list.append(current_set)
                logging.info('"{}" has been deleted.'.format(current_set))
            except Exception as e:
                logging.error('Unable to delete "{}"!'.format(current_set))
                logging.error(e)
    return deleted_list


# Unused
def remove_from_sets(elements_list, set_name):
    """
    Remove elementList from a set
    :param: elements_list
    :param: set_name
    :return: removed_list
    :rtype: list
    """
    removed_list = []
    if elements_list and cmds.objExists(set_name):
        for element in elements_list:
            if cmds.objExists(element):
                try:
                    cmds.sets(element, rm=set_name)
                    removed_list.append(element)
                    logging.info('"{}" has been removed from "{}"'.format(element, set_name))
                except Exception as e:
                    logging.error('Unable to remove "{}" from "{}"'.format(element, set_name))
                    logging.error(e)
    return removed_list


# Used in out_task_assembly
def clean_sets(set_suffixe, sets_list):
    """
    Remove sets which not ends with set_suffixe
    :param: set_suffixe
    :param: sets_list
    :return: the list of deleted sets
    :rtype: list
    """
    obsolete_sets = []
    for set_found in list(sets_list):
        if not set_found.endswith('_{}'.format(set_suffixe)):
            cmds.delete(set_found)
            sets_list.remove(set_found)
            obsolete_sets.append(set_found)
    return obsolete_sets


# _________________________________________________________________________________________________________
# #########################
# --- UNUSED - UNKNOWN ---#
# #########################

# Used in clean_shading
def delete_unused_nodes():
    """
    Delete unused shading nodes
    """
    mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')
    logging.info('Unused Nodes have been deleted.')


# Used in SC, out_task_asseet
def delete_unknown_nodes(unknown_list=[]):
    """
    Check for unknown nodes, delete them
    :param: unknown_list => list of unknown nodes to delete
    :return: None if unknown nodes have been successfully deleted.
    :return: the list of undeletable unkown nodes
    :rtype: None or a list
    """
    if unknown_list:
        unknown_list = read_nodes.list_unknown_nodes()
    for unknown in unknown_list:
        if cmds.objExists(unknown):
            try:
                cmds.lockNode(unknown, lock=False)
                cmds.delete(unknown)
            except Exception as e:
                logging.error('Unable to delete this Unknown Node: {}'.format(unknown))
                logging.error(e)
    still_unknown = read_nodes.list_unknown_nodes()
    if still_unknown:
        logging.error('Unable to delete these Unknown Nodes: {}'.format(still_unknown))
        return still_unknown
    else:
        logging.info('Unknown Nodes have been deleted.')
        return None
