# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#                       Nicolas Dorey
#
#   DESCRIPTION :       References checks lib
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging

try:
    import maya.cmds as cmds
except ImportError:
    pass

from ..reads import references as read_references


def check_if_scene_has_ref(logger=logging):
    """
    Check if scene has references
    :return: ref
    :rtype: list
    """
    ref = read_references.list_references()
    if len(ref) > 0:
        logger.error("References found: {}".format(ref))
    return ref


def check_unknown_ref_node(logger=logging):
    """
    Check if scene containts _UNKNOWN_REF_NODE_
    :return: unknows
    :rtype: list
    """
    unknown_ref = cmds.ls('_UNKNOWN_REF_NODE_', type='reference')
    if unknown_ref:
        logger.error('{} // {}'.format('_UNKNOWN_REF_NODE_ found !!', unknown_ref))
    return unknown_ref


def check_namespaces(logger=logging):
    """
    Check if scene has namespaces
    :return: namespaces
    :rtype: list
    """
    namespaces = read_references.list_namespaces()
    if len(namespaces) > 0:
        logger.error("NameSpaces found: {}".format(namespaces))
    return namespaces


# TODO: snakecase
def check_reference_edits(reference, whiteList=['visibility'], logger=logging):
    """
    Check if reference has edits, besides whiteList
    :param: reference
    :param: whiteList => ['visibility'] by default
    :return: check_edit
    :rtype: boolean
    """
    check_edit = True
    edits = cmds.referenceQuery(reference, editAttrs=True)
    for edit in edits:
        if edit not in whiteList:
            logger.error('Unauthorized Edits of references! Only {}authorized!'.format(whiteList))
            check_edit = False
    return check_edit


# TODO: snakecase
def check_failed_references_edits(refList=[], logger=logging):
    """
    Check if references have failed edits
    :param: refList => empty list by default
    :return: no_ref_fails
    :rtype: boolean
    """
    no_ref_fails = True
    all_ref = refList if refList else read_references.list_references()
    for ref in all_ref:
        edits = cmds.referenceQuery(ref, editStrings=True)
        fails = [i for i in cmds.referenceQuery(ref, editStrings=True, failedEdits=True) if i not in edits]
        if fails:
            logger.warning('Failed edits found on ref : {}'.format(ref))
            no_ref_fails = False
    return no_ref_fails
