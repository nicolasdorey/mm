# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Shading creates libs
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

try:
    import maya.cmds as cmds
except ImportError:
    pass


# Used in hook build_bridge_shading
def create_lambert(name='lambert', shading_group_name=None):
    """
    Create a lambert material connected to shading_group_name
    :param: name => string, 'lambert' by default
    :param: shading_group_name => None by default
    :return: a dict with shader as key and shading group as value
    :rtype: dict
    """
    # Shading group name
    if not shading_group_name:
        shading_group_name = name + 'SG'
    # Node creation
    lambert = cmds.shadingNode('lambert', name=name, asShader=True)
    shading_group = cmds.sets(name=shading_group_name, empty=True, renderable=True, noSurfaceShader=True)
    cmds.connectAttr(lambert + '.outColor', shading_group + '.surfaceShader')

    return {'lambert': lambert, 'shading_group': shading_group}
