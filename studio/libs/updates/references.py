# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Utils for references updates
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         glob var problem in found_maya_scene. Unfound rendersetup
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging

try:
    import maya.cmds as cmds
except ImportError:
    pass

from ..reads import references as read_references


##########################
# ---MANAGE REFERENCES---#
##########################

# TODO: snakecase args
# TODO: return the list of removed ref
def remove_reference(deleteRef=True, refList=None, logger=logging):
    """
    Load and remove references
    :param: deleteRef => True by default
    :param: refList => None by default
    """
    refs = read_references.list_references() if refList is None else refList
    for ref in refs:
        try:
            if cmds.referenceQuery(ref, isLoaded=True) is False:
                cmds.file(loadReference=True)
            cmds.file(lockReference=False)
            if deleteRef:
                cmds.file(referenceNode=ref, removeReference=True, f=True)
            else:
                cmds.file(referenceNode=ref, importReference=True, f=True)
        except Exception as e:
            logger.warning('Couln t query reference!')
            logger.warning(e)
    logger.info("References {}: have been removed.".format(refs))


def remove_namespaces():
    """
    Remove Namespaces of scene
    :return: namespaces
    :rtype: list
    """
    namespaces = read_references.list_namespaces()
    # We use while loop to delete nested namespaces
    while len(namespaces) > 0:
        for ns in namespaces:
            try:
                cmds.namespace(force=True, rm=ns, mnr=True)  # , mergeNamespaceWithRoot=True)
                logging.info("NameSpace `{}` has been removed".format(ns))
                namespaces = read_references.list_namespaces()
            except Exception as e:
                logging.warning("%s // Cant remove namespace! %s" % (str(e), ns))
                if ns in namespaces:
                    namespaces.remove(ns)
                    break
    return namespaces
