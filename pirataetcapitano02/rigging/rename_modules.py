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

import json
import os

try:
    import maya.cmds as cmds
    import maya.mel as mel
except ImportError:
    pass


from ....studio.libs.reads import nodes as read_nodes
from ....studio.libs.reads import references as read_references

# TODO: need a library for these kinds of actions to avoid import from update_asset_step
from ...pirataetcapitano02.common.update_asset_step import UpdateAssetScene

# TODO: find a better way to be sure dirname wont fail
try:
    dirname = os.path.dirname(__file__)
except Exception as e:
    dirname = r"C:\Shotgun\tk-framework-millimages\python\millimages\maya\tools\PirataEtCapitano\rigging"
    print(e)


class RenameModules(object):
    def __init__(self):
        JSON_NAME = "module_rename.json"
        JSON = os.path.join(dirname, JSON_NAME)

        with open(JSON) as f:
            self.NOM_DICT = json.load(f)

        # We need to reverse order of dict keys to replace for example "Cog_Anm_CtrlGrp" before replace "Cog_Sta_Ctrl"
        #   to avoid replacing only a part of a node name.
        self.DICT_ORDER_FORCED = self.NOM_DICT.keys()
        self.DICT_ORDER_FORCED.sort()
        self.DICT_ORDER_FORCED.reverse()

        self.mdl_namespace = "BridgeModelingPreRig_"

        all_top = read_nodes.get_top_node()
        self.rig_top = [i for i in all_top if "_RIG_Top" in i and cmds.objExists(i)]
        self.mdl_top = [i for i in all_top if self.mdl_namespace in i and cmds.objExists(i)]

        # hide modeling top node
        if self.mdl_top and len(self.mdl_top) == 1:
            self.mdl_top = self.mdl_top[0]
            cmds.setAttr("{}.visibility".format(self.mdl_top), 0)

    # def rename_non_ref_nodes(self):
    #     all_top = read_nodes.get_top_node()
    #     self.rig_top = [i for i in all_top if "_RIG_Top" in i and cmds.objExists(i)]
    #     if not rig_top:
    #         print('No top rig found!!')
    #         return
    #     else:
    #         rig_top = rig_top[0]
    #     cmds.select(rig_top, hi=True)
    #     rig_hiearchy = cmds.ls(sl=True)
    #     for rig_node in rig_hiearchy:
    #         for old in self.DICT_ORDER_FORCED:
    #             if old in rig_node:
    #                 new = self.NOM_DICT[old]
    #                 new_name = rig_node.replace(old, new)
    #                 try:
    #                     cmds.rename(rig_node, new_name)
    #                     print('Node has been renamed', rig_node, new_name)
    #                 except Exception as e:
    #                     print(e, 'Couldnt rename : ', rig_node)

    def rename_namespaces(self):
        allNs = read_references.list_namespaces()
        for ns in allNs:
            if "BridgeModeling" not in ns:
                try:
                    cmds.namespace(rename=[ns, "C_Root01"])
                except Exception as e:
                    print(e)
                    pass
                print('name space:', ns, " has been renamed to :", "C_Root01")
                return ns

    def check_process_and_fix(self):
        parent_ctrl_grp = cmds.listRelatives("C_Root01:_Ctrls_Grp", p=True)
        if parent_ctrl_grp != "Ctrls_Grp":
            try:
                cmds.parent("C_Root01:_Ctrls_Grp", "Ctrls_Grp")
            except Exception as e:
                print(e)
                pass
            try:
                cmds.parent("C_Root01:_Trash_Grp", "Trash_Grp")
            except Exception as e:
                print(e)
                pass
        cmds.setAttr("C_Root01:_Ctrls_Grp.DoubleVis", 0)
        try:
            cmds.delete(cmds.ls(type="nodeGraphEditorInfo"))
        except Exception as e:
            print('Could not delete node graph editor ')
            print(e)

        try:
            cmds.delete(cmds.ls("MayaNodeEditorSavedTabsInfo*"))
        except Exception as e:
            print('Could not delete maya node editor saved tabs')
            print(e)


    def get_and_rename_ref_edits(self, curr_namespace):
        allRef = read_references.list_references()
        print('all ref', allRef)
        new_edits = []
        print(self.DICT_ORDER_FORCED)
        self.DICT_ORDER_FORCED.remove('C_Master')
        self.DICT_ORDER_FORCED.append(curr_namespace)
        self.NOM_DICT[curr_namespace] = self.NOM_DICT.pop("C_Master")

        for ref in allRef:
            # Get failed edits of the reference
            edits = cmds.referenceQuery(ref, editStrings=True)
            fails = [i for i in cmds.referenceQuery(ref, editStrings=True, failedEdits=True) if i not in edits]

            # Try to repair failed edits with dict
            for failed_edit in fails:
                repaired_edit = failed_edit

                # Loop over names
                for old in self.DICT_ORDER_FORCED:
                    new = self.NOM_DICT[old]

                    # Repair edit if name is found by replacing by the new one
                    if old in repaired_edit:
                        repaired_edit = repaired_edit.replace(old, new)

                # If edit is repaired, we store it
                if repaired_edit != failed_edit and repaired_edit not in new_edits:
                    new_edits.append(repaired_edit)

            cmds.referenceEdit(ref, removeEdits=True)
        print(new_edits)
        return new_edits

    def remove_mdl_all_ref_edit(self, first_part_namespace):
        """
        Remove ref edits on modeling except visibility
        """
        EditsTypes = ["parent", "setAttr", "addAttr", "deleteAttr", "disconnectAttr", "connectAttr", "lock", "unlock"]
        BridgeModeling_ref_nodes = cmds.ls("{}*:*".format(first_part_namespace))

        current_edits = []
        for ref in BridgeModeling_ref_nodes:
            edits = cmds.referenceQuery(ref, editStrings=True)
            current_edits += edits

        attr_to_keep = [edit for edit in current_edits if ".visibility" in edit]

        for BridgeModeling_ref_node in BridgeModeling_ref_nodes:
            for EditsType in EditsTypes:
                try:
                    cmds.referenceEdit(BridgeModeling_ref_node, failedEdits=True, successfulEdits=True, editCommand=EditsType, removeEdits=True)
                except Exception as e:
                    print(e)
                    return False

        if attr_to_keep:
            for attr in attr_to_keep:
                mel.eval(attr)

        return True

    def fix_rename_imported_hierachy(self):

        childs_top_node = cmds.listRelatives(self.rig_top, c=True)
        childs_SkinJoints_Grp = cmds.listRelatives("SkinJoints*", c=True)
        cog_out_prx = cmds.ls("Cog_Out_Prx")

        if cog_out_prx and len(cog_out_prx) == 1:
            cog_out_prx = cog_out_prx[0]
            try:
                cmds.rename(cog_out_prx, "C_Root01_CogOut_Prx")
            except Exception as e:
                print('Could not rename {}'.format(cog_out_prx))
                print e

        for i in childs_SkinJoints_Grp:
            if "SkJnt" in i:
                if i != "C_Root01_01_SkJnt":
                    try:
                        cmds.rename(i, "C_Root01_01_SkJnt")
                    except Exception as e:
                        print("Could not rename node : {}".format(i))
                        print(e)

        for i in childs_top_node:
            if i == "RigModuleIO_Prx":
                try:
                    cmds.rename('RigModuleIO_Prx', "RigModuleIOPrx_Grp")
                except Exception as e:
                    print(e)
                    pass

            elif i == "Cog_Out_Prx":
                try:
                    cmds.rename(i, "C_Root01_CogOut_Prx")
                except Exception as e:
                    print("Could not rename node : {}".format(i))
                    print(e)

            elif i == "FaceRig_Grp" or i == "FaceRig":
                try:
                    cmds.delete(i)
                except Exception as e:
                    print("Could not delete node : {}".format(i))
                    print(e)

            if i != "RigModuleIOPrx_Grp":
                if not i.endswith("_Grp"):
                    try:
                        newName = cmds.rename(i, "{}_Grp".format(i))
                    except Exception as e:
                        print("Could not rename node {}".format(i))
                        print(e)
                    if newName == "RigSystem_Grp":
                        for e in cmds.listRelatives(newName, c=True):
                            if not e.endswith('_Grp'):
                                try:
                                    cmds.rename(e, "{}_Grp".format(e))
                                except Exception as e:
                                    print("Could not rename node {}".format(i))
                                    print(e)


    def redo_edits(self, new_edits):
        for edit in new_edits:
            # To avoid errors with placeHolderList on reference, we force connection on connectAttr
            if edit.startswith('connectAttr'):
                edit += ' -force'

            # Apply edit
            try:
                mel.eval(edit)
            except Exception as e:
                print(e)


    def execute(self):
        print('updating reference')
        update_scene = UpdateAssetScene()
        update_scene.update_breakdown_references()
        print('Start of renaming namespace')
        curr_namespace = self.rename_namespaces()
        print('Get Ref edit and rename')
        new_edits = self.get_and_rename_ref_edits(curr_namespace)
        print('New_Edit', new_edits)
        self.redo_edits(new_edits)
        self.fix_rename_imported_hierachy()
        self.remove_mdl_all_ref_edit(first_part_namespace=self.mdl_namespace)
        self.check_process_and_fix()

        print('deleting unknown nodes')
        # try:
        #     mel.eval('delete `ls -type unknown -type unknownDag -type unknownTransform`')
        # except Exception as e:
        #     print(e, "Could not remove unknown dag nodes!")

        print('Done')
