# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Utils for scene elements deletion
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


# Used in baking_redshift
def clean_aovs():
    """
    Delete existing aovs
    :return: not_deleted, the list of aov that cannot be deleted
    :rtype: list
    """
    not_deleted = []
    existing_aovs = cmds.ls(type="RedshiftAOV")
    for aov in existing_aovs:
        try:
            cmds.delete(aov)
        except Exception as e:
            logging.error('Cannot delete aov named "{}"'.format(aov))
            logging.error(e)
            not_deleted.append(aov)
    mel.eval('unifiedRenderGlobalsWindow')
    mel.eval('redshiftUpdateActiveAovList')
    return not_deleted
