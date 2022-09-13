# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Utils for shading deletion
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


# TODO: need to return what have been deleted / or not
def clean_shading_network(shader, node, logger=logging):
    """
    Deletes nodes from between node and shader to clean shading network
    Ex: for a given file node, it will delete the nodes in the shading network between the file and the shader
    :param: shader
    :param: node
    """
    down = cmds.listHistory(node, f=True)
    up = cmds.listHistory(node, f=False)

    for connected_node in down:
        if connected_node == shader:
            break
        if connected_node != node:
            try:
                cmds.delete(connected_node)
                logger.info('Node "{}" has been deleted'.format(connected_node))
            except Exception as e:
                logger.warning('Could not delete node "{}"!'.format(connected_node))
                logger.error(e)

    for connected_node in up:
        if connected_node == shader:
            break
        try:
            cmds.delete(connected_node)
            logger.info('Node "{}" has been deleted'.format(connected_node))
        except Exception as e:
            logger.error('Could not delete node "{}"!'.format(connected_node))
            logger.error(e)
