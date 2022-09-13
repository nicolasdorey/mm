# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#                       Nicolas Dorey
#
#   DESCRIPTION :       Layers checks lib
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging

from ..reads import layers as read_layers


def check_display_layer(logger=logging):
    """
    Check if scene has display layer besides default
    :return: all_disp
    :rtype : list
    """
    all_disp = read_layers.list_display_layers()
    if len(all_disp) > 0:
        logger.error("DisplayLayers found: {}".format(all_disp))

    return all_disp
