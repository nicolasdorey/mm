# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##
#   SCRIPT :            exeLayKeyer
#   AUTHOR :            Theodoric "KrNNN" JUILLET
#
#   DATE :              25/03/2020 - 18:28
#
#   DESCRIPTION :       Prevent pos modification during layout outside a specific range.
#
#   PRECAUTION :        Define the range of a plan before executing.
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##

try:
    import maya.cmds as cmds
    import maya.mel as mel
except ImportError:
    pass


def query_range():
    cmds.keyTangent(g=True, itt="linear", ott="linear")
    min_time = float(cmds.playbackOptions(q=True, min=True))
    max_time = float(cmds.playbackOptions(q=True, max=True))
    current_time = cmds.currentTime(q=True)
    selection = cmds.ls(sl=True, long=True, r=True)
    return min_time, max_time, selection, current_time


def copy_keys(actual_time, target_time):
    cmds.ogs(p=True)
    mel.eval("timeSliderCopyKey;")
    cmds.currentTime(target_time)
    mel.eval("timeSliderPasteKey false;")
    mel.eval("selectKey;")
    mel.eval("keyTangent -itt linear -ott linear;")
    cmds.selectKey(cl=True)
    cmds.ogs(p=True)


def func_lay_keyer_1():
    min_time, max_time, selection, current_time = query_range()
    print(selection)
    if selection:
        cmds.ogs(p=True)
        cmds.currentTime(min_time - 1)
        cmds.setKeyframe()
        cmds.currentTime(max_time + 1)
        cmds.setKeyframe()
        cmds.currentTime(min_time)
        cmds.setKeyframe()
        cmds.currentTime(max_time)
        cmds.setKeyframe()
        cmds.warning("--- Keying Done ! ---")
        cmds.ogs(p=True)
    else:
        cmds.warning("--- No selection, please try again ! ---")


def func_lay_keyer_2():
    min_time, max_time, selection, current_time = query_range()
    if selection:
        if current_time == min_time:
            copy_keys(actual_time=current_time, target_time=max_time)
        elif current_time == max_time:
            copy_keys(actual_time=current_time, target_time=min_time)
        else:
            cmds.warning("--- Please move to the first or the last frame of your timeline ---")
    else:
        cmds.warning("--- No selection, please try again ! ---")


def func_lay_keyer():
    func_lay_keyer_1()
    mel.eval("timeSliderPasteKey false;")
    func_lay_keyer_2()


# ! https://stackoverflow.com/questions/28620271/python-maya-how-to-change-a-float-into-a-time-value
