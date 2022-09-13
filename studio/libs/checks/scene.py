# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#                       Nicolas Dorey
#
#   DESCRIPTION :       Scene checks lib
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

from ..reads import scene as read_scenes


def check_time_unit(logger=logging):
    """
    Check if the scene is setup in pal.
    :return correct_time : True if current unit is pal
    :rtype : bool
    """
    correct_time = True
    current_time = cmds.currentUnit(time=True, q=True)
    if current_time != "pal":
        correct_time = False
    return correct_time


# TODO: snakecase args
def check_frame_range(startFr=1001, endFr=1200, logger=logging):
    """
    Check frame range.
    :param: startFr
    :param: endFr
    :return: True if playback is well setted
    :rtype: boolean
    """
    correct_fr = True
    min_time = cmds.playbackOptions(minTime=True, q=True)
    min_anim_start = cmds.playbackOptions(animationStartTime=True, q=True)
    min_anim_end = cmds.playbackOptions(animationEndTime=True, q=True)
    max_time = cmds.playbackOptions(maxTime=True, q=True)

    if min_time != startFr:
        correct_fr = False
    if min_anim_start != startFr:
        correct_fr = False
    if min_anim_end != endFr:
        correct_fr = False
    if max_time != endFr:
        correct_fr = False
    return correct_fr


def check_colormanagement_mode(mode='linear'):
    """
    False if scene is not setuped in linear
    :param: mode / 'linear' by default
    :return: check_color_mode
    :rtype: boolean
    """
    check_color_mode = True
    post_effects = cmds.ls(exactType="RedshiftPostEffects")
    for post_effect in post_effects:
        mode = cmds.getAttr(post_effect + ".clrMgmtDisplayMode")
        mode = mode.split('_')[-1]
        if mode.lower() != mode:
            check_color_mode = False
    return check_color_mode


def check_redshift_load(logger=logging):
    """
    Check if redshift is loaded
    :return: check_rs_load
    :rtype: boolean
    """
    check_rs_load = True
    current_render = read_scenes.get_current_renderer()[0]
    avail_renders = read_scenes.get_current_renderer()[1]
    if cmds.pluginInfo("redshift4maya", query=True, loaded=True):
        check_rs_load = False
        logging.info("Redshift is loaded.")
    if "redshift" in current_render:
        # check_rs_load = False
        logging.warning("Redshift is current render.")
    elif "redshift" in avail_renders:
        # check_rs_load = False
        logging.warning("RedShift is still available in renderers.")
    return check_rs_load
