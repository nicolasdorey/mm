# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       ?
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

try:
    import maya.cmds as cmds
    import pymel.core as pm
    from functools import partial
except ImportError:
    pass


# FIXME: remove and fix import from inside: cmt.rig.spaceswitch as spaceswitch
# TODO: snakecase
class SpaceswitchTools():

    def drivenBT_action(self, *args):
        sel = cmds.ls(sl=True)
        cmds.textField("drivenTF", e=True, tx=sel[0])

    def driverBT_action(self, *args):
        sel = cmds.ls(sl=True)
        cmds.textScrollList("driverTSL", e=True, ra=True)
        cmds.textScrollList("driverTSL", e=True, a=sel)
        childs_space_nameGrpCL = cmds.columnLayout('space_nameGrpCL', q=True, ca=True)
        if childs_space_nameGrpCL is not None:
            cmds.deleteUI(childs_space_nameGrpCL)
        pm_sel = pm.selected()
        for obj in pm_sel:
            cmds.textField(parent='space_nameGrpCL', text=obj.name().replace(obj.namespace(), '').split('_')[0], h=14)


    def spaceswitchBT_action(self, switch_attribute="space", use_rotate=False, *args):
        driven_ctrls = cmds.textField("drivenTF", q=True, tx=True)
        drivers_ctrls = cmds.textScrollList("driverTSL", q=True, ai=True)
        childs_space_nameGrpCL = cmds.columnLayout('space_nameGrpCL', q=True, ca=True)
        space_names = []
        if childs_space_nameGrpCL is not None:
            for child in childs_space_nameGrpCL:
                space_names.append(cmds.textField(child, q=True, tx=True))
        drivers = []
        for i in range(0, len(drivers_ctrls)):
            drivers.append((drivers_ctrls[i], space_names[i]))
        print(drivers)
        # Create the space switch
        # FIXME: remove import from there!
        import cmt.rig.spaceswitch as spaceswitch
        spaceswitch.create_space_switch(
            driven_ctrls,
            drivers,
            switch_attribute=switch_attribute,
            use_rotate=use_rotate,
        )

    def spaceswitchUI(self):
        if cmds.window("spaceSwitchWD", exists=True):
            cmds.deleteUI("spaceSwitchWD")
        cmds.window("spaceSwitchWD")
        cmds.columnLayout("mainCL", w=600, adj=True)
        cmds.separator()
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 400), (2, 200)], adj=True)
        cmds.textField("drivenTF")
        cmds.button(l="driven_ctrls", c=partial(self.drivenBT_action))
        cmds.setParent("..")
        cmds.separator()
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 400), (2, 200)], adj=True)
        cmds.textScrollList("driverTSL", h=500)
        cmds.columnLayout('space_nameGrpCL', adj=1)
        cmds.textScrollList(h=500)
        cmds.setParent('..')
        cmds.button(label="driver_ctrls", c=partial(self.driverBT_action))
        cmds.button(l="balance la sauce", c=partial(self.spaceswitchBT_action))
        cmds.showWindow("spaceSwitchWD")
