# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##
#   AUTHOR :            Theodoric "KrNNN" JUILLET
#
#   DESCRIPTION :       Open/Close Maya port for Sublime Text 3/VS Code.
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##

try:
    import maya.cmds as cmds
except ImportError:
    pass


def edit_port(open_port):
    """
    Close ports if they were already open under another configuration
    """
    try:
        cmds.commandPort(name=":7001", close=True)
    except Exception as e:
        cmds.warning('Could not close port 7001 (maybe it is not opened yet...)')
        cmds.warning(e)
    try:
        cmds.commandPort(name=":7002", close=True)
    except Exception as e:
        cmds.warning('Could not close port 7002 (maybe it is not opened yet...)')
        cmds.warning(e)
    if open_port:
        # Open new ports
        cmds.commandPort(name=":7001", sourceType="mel")
        cmds.commandPort(name=":7002", sourceType="python")
