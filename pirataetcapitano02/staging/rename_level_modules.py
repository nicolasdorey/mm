# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Maximillien Rolland
#
#   DESCRIPTION :       ?
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging
import json
import os

try:
    import maya.cmds as cmds
    import maya.mel as mel
except ImportError as e:
    logging.warning(str(e))

try:
    import sgtk
except ImportError as e:
    logging.warning(str(e))

from ....studio.libs.reads import nodes as read_nodes

# TODO: find a better way to be sure dirname wont fail
# TODO: clean script: snakecase and libs functions!
try:
    dirname = os.path.dirname(__file__)
except Exception as e:
    dirname = r"C:\Shotgun\tk-framework-millimages\python\millimages\maya\tools\PirataEtCapitano\rigging"
    print(e)


class RenameLevelModules(object):
    def __init__(self):
        JSON_NAME = "module_rename.json"
        JSON = os.path.join(dirname, JSON_NAME)

        with open(JSON) as f:
            self.NOM_DICT = json.load(f)

        # We need to reverse order of dict keys to replace for example "Cog_Anm_CtrlGrp" before replace "Cog_Sta_Ctrl"
        # to avoid replacing only a part of a node name.
        self.DICT_ORDER_FORCED = self.NOM_DICT.keys()
        self.DICT_ORDER_FORCED.sort()
        self.DICT_ORDER_FORCED.reverse()
        logging.info('DICT_ORDER_FORCED: {}'.format(self.DICT_ORDER_FORCED))

        self.mdl_namespace = "BridgeModelingPreRig_"

        all_top = read_nodes.get_top_node()
        self.rig_top = [i for i in all_top if "_RIG_Top" in i and cmds.objExists(i)]
        self.mdl_top = [i for i in all_top if self.mdl_namespace in i and cmds.objExists(i)]

        # Hide modeling top node
        if self.mdl_top and len(self.mdl_top) == 1:
            self.mdl_top = self.mdl_top[0]
            cmds.setAttr("{}.visibility".format(self.mdl_top), 0)

    def update_breakdown_references(self):
        """
        Call the tk-multi-breakdown method to update asset reference and sub references if exist
        # TODO: extract this function into a lib
        """
        results = []
        new_version = {}
        current_engine = sgtk.platform.current_engine()
        self.breakdown_app = current_engine.apps.get('tk-multi-breakdown')
        app = self.breakdown_app
        if not app:
            logging.error("App {} wasn't found. ".format(app))
            return

        # Looking for references to update
        try:
            items = app.analyze_scene()
        except Exception, e:
            app.log_exception("Could not execute execute hook action: %s" % e)
        if not items:
            logging.error('No reference found!')
            return results

        # If reference found
        for item_found in items:
            node_type = item_found.get('node_type')
            node_name = item_found.get('node_name')
            template = item_found.get('template')
            fields = item_found.get('fields')
            old_version = fields.get('version')

            # Find latest version
            try:
                version = app.compute_highest_version(template, fields)
                new_version = {'version': version}
            except Exception, e:
                app.log_exception("Could not execute execute hook action: %s" % e)

            # Update dict version from scan fields
            if new_version.get('version') != None and new_version.get('version') != old_version:
                fields.update(new_version)

                # Update reference with new version
                try:
                    app.update_item(node_type, node_name, template, fields)
                    logging.info('Reference path of "{}" has been updated'.format(node_name))
                    logging.info('Old version: "{}" / New version: "{}"'.format(old_version, new_version.get('version')))
                    results.append(item_found)
                except Exception, e:
                    app.log_exception("Could not execute execute hook action: %s" % e)
        return results

    def check_process_and_fix(self):
        logging.info('\tcheck_process_and_fix()...')
        try:
            cmds.delete(cmds.ls(type="nodeGraphEditorInfo"))
        except Exception as e:
            logging.error('Could not delete node graph editor ')
            logging.error(e)
        try:
            cmds.delete(cmds.ls("MayaNodeEditorSavedTabsInfo*"))
        except Exception as e:
            logging.error('Could not delete maya node editor saved tabs')
            logging.error(e)

    def repair_edits(self, edits):
        """
        Try to find in each edit some part to replace with new nomenclature.
        :param edits: edits to repair
        :type edits: list
        :return: all edits repaired and not repaired
        :rtype: list
        """
        result_edits = []
        repaired_edits = []
        not_repaired_edits = []

        # Try to repair edits
        for edit in edits:
            repaired_edit = edit
            # Loop over node name from dict
            for old_name in self.DICT_ORDER_FORCED:
                # Repair edit if old node name is found by replacing with the new one
                if old_name in repaired_edit:
                    new_name = self.NOM_DICT[old_name]
                    repaired_edit = repaired_edit.replace(old_name, new_name)

            # Store result edit
            if repaired_edit not in result_edits:
                result_edits.append(repaired_edit)
            # Store repaired or not repaired edit
            if repaired_edit != edit and repaired_edit not in repaired_edits:
                repaired_edits.append(repaired_edit)
            elif repaired_edit == edit and edit not in not_repaired_edits:
                not_repaired_edits.append(edit)

        # Return result
        return result_edits

    def get_and_rename_ref_edits(self):
        """
        Loop over valid references of the scene, get their failed edits and repair them.
        :return: repaired edits
        :rtype: list
        """
        logging.info('\n\tget_and_rename_ref_edits()...')
        references = self.get_all_references()
        new_edits = []

        # Loop over ref and get failed edits
        for ref in references:
            # Get failed edits of the reference
            fails = cmds.referenceQuery(ref, editStrings=True, failedEdits=True,
                                        successfulEdits=False, liveEdits=False)
            if not fails:
                continue
            # Get repaired failed edits
            repaired_edits = self.repair_edits(fails)
            for edit in repaired_edits:
                if edit not in new_edits:
                    new_edits.append(edit)

        # Return result
        return new_edits

    def remove_mdl_all_ref_edit(self, first_part_namespace):
        """
        Remove ref edits on modeling except visibility
        """
        logging.info('\tremove_mdl_all_ref_edit()...')
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
                    logging.warning(e)
                    return False

        if attr_to_keep:
            for attr in attr_to_keep:
                mel.eval(attr)

        return True

    def fix_rename_imported_hierachy(self):
        logging.info('\tfix_rename_imported_hierarchy()...')
        # Cog out prx
        cog_out_prx = cmds.ls("Cog_Out_Prx")
        logging.info('\tcog_out_prx: {}'.format(cog_out_prx))
        if cog_out_prx and len(cog_out_prx) == 1:
            cog_out_prx = cog_out_prx[0]
            try:
                cmds.rename(cog_out_prx, "C_Root01_CogOut_Prx")
            except Exception as e:
                print('Could not rename {}: {}'.format(cog_out_prx, e))

        # Child top nodes
        childs_top_node = cmds.listRelatives(self.rig_top, c=True)
        if not childs_top_node:
            return
        for i in childs_top_node:
            logging.info('\tchild top node "{}" ({}/{})'.format(i, childs_top_node.index(i), len(childs_top_node)))
            if i == "RigModuleIO_Prx":
                try:
                    cmds.rename(i, "RigModuleIOPrx_Grp")
                except Exception as e:
                    print('Could not rename node "{}": {}'.format(i, e))

            elif i == "Cog_Out_Prx":
                try:
                    cmds.rename(i, "C_Root01_CogOut_Prx")
                except Exception as e:
                    print('Could not rename node "{}": {}'.format(i, e))

            elif i in ["FaceRig_Grp", "FaceRig"]:
                try:
                    cmds.delete(i)
                except Exception as e:
                    print('Could not delete node "{}": {}'.format(i, e))

            if i != "RigModuleIOPrx_Grp" and not i.endswith("_Grp"):
                try:
                    newName = cmds.rename(i, "{}_Grp".format(i))
                except Exception as e:
                    print('Could not rename node "{}": {}'.format(i, e))
                if newName == "RigSystem_Grp":
                    for e in cmds.listRelatives(newName, c=True):
                        if not e.endswith('_Grp'):
                            try:
                                cmds.rename(e, "{}_Grp".format(e))
                            except Exception as e:
                                print('Could not rename node "{}": {}'.format(i, e))

    def redo_edits(self, edits):
        """
        Apply list of edits
        :param edits: edits to apply
        :type edits: list
        """
        logging.info('\n\tredo_edits()...')
        len_edits = len(edits)
        for count, edit in enumerate(edits, start=1):
            log_count = '({}/{}) '.format(count, len_edits)

            # To avoid errors with placeHolderList on reference, we force connection on connectAttr
            if edit.startswith('connectAttr'):
                edit += ' -force'

            # Apply edit
            try:
                mel.eval(edit)
                logging.info('\t\t{}edit applied: {}'.format(log_count, edit))
            except Exception as e:
                logging.info('\t\t{}edit failed: {} - {}'.format(log_count, e, edit))

    def get_all_references(self):
        """
        Return all reference nodes excepted when content is in "RefTrash" group
        :return: filtered reference nodes
        :rtype: list
        """
        references = cmds.ls(rf=True)
        out_refs = []
        for reference in references:
            if not cmds.referenceQuery(reference, isNodeReferenced=True):
                continue
            referenced_nodes = cmds.referenceQuery(reference, nodes=True)
            if referenced_nodes and "RefTrash:" in referenced_nodes:
                continue
            out_refs.append(reference)
        return out_refs

    def get_children_references(self):
        """
        Return all references which have a parent reference.
        :return: children reference nodes
        :rtype: list
        """
        logging.info('\tget_children_references()...')
        references = self.get_all_references()
        children_references = []
        for reference in references:
            if cmds.referenceQuery(reference, parent=True, rfn=True):
                children_references.append(reference)
        logging.info('\t\tFound {} child(ren) reference(s).'.format(len(children_references)))
        return children_references

    def get_children_ref_edits(self):
        """
        Save in dict edits of children reference nodes.
        Return a dict like this one: {"children01RN": ['edit01', 'edit02', ...], ...}
        :return: each reference node associated with its edits.
        :rtype: dict
        """
        logging.info('\n\tget_children_ref_edits()...')
        children_refs_edits_data = {}
        children_references = self.get_children_references()
        for reference in children_references:
            edits = cmds.referenceQuery(reference, editStrings=True, failedEdits=False, successfulEdits=True, liveEdits=False)
            if edits:
                children_refs_edits_data[reference] = edits
        return children_refs_edits_data

    def filter_children_references(self, children_references):
        logging.info('\n\tfilter_children_references()...')
        filtered_references = []

        # Loop over children reference node
        for reference in children_references:
            # Change the name to find the new reference node
            new_reference = reference.replace('RN', 'OutBuildCacheRN')
            # Try to find this new reference
            if not cmds.objExists(new_reference):
                continue
            # If found, we can save its edits
            filtered_references.append(reference)

        # Return result
        return filtered_references

    def get_filtered_children_edits(self, ref_names, children_refs_edits_data):
        """
        Return all edits of filtered children references
        :param ref_names: reference node name to get edits
        :type ref_names: list
        :param children_refs_edits_data: reference node names associated with their edits
        :type children_refs_edits_data: dict
        :return: filtered edits
        :rtype: list
        """
        logging.info('\n\tget_filtered_children_edits()...')
        filtered_children_refs_edits = []
        for ref_name, data in children_refs_edits_data.iteritems():
            if ref_name in ref_names:
                filtered_children_refs_edits.extend(data)
        return filtered_children_refs_edits

    def remove_all_edits(self):
        """Remove edits of all valid references."""
        references = self.get_all_references()
        for reference in references:
            cmds.referenceEdit(reference, removeEdits=True)

    def execute(self):
        # Get edits of children references to avoid to lose them after update (we save reference node name too)
        children_refs_edits_data = self.get_children_ref_edits()
        # Update scene references
        self.update_breakdown_references()
        # Filter children references to keep only ones found by replacing "RN" with "OutBuildCacheRN"
        filtered_children_names = self.filter_children_references(children_refs_edits_data)
        # Get list of edits of these filtered children references
        filtered_children_edits = self.get_filtered_children_edits(filtered_children_names, children_refs_edits_data)
        # Repair filtered children edits if necessary
        repaired_filtered_children_edits = self.repair_edits(filtered_children_edits)
        # Get and rename reference edits (for parent reference nodes not renamed)
        new_edits = self.get_and_rename_ref_edits()
        # Remove edits of all reference before redo edits
        self.remove_all_edits()
        # Redo edits
        logging.info('redo parent edits...')
        self.redo_edits(new_edits)
        logging.info('redo children edits...')
        self.redo_edits(repaired_filtered_children_edits)
        # Other fixes
        self.fix_rename_imported_hierachy()
        self.remove_mdl_all_ref_edit(first_part_namespace=self.mdl_namespace)
        self.check_process_and_fix()
        logging.info('Done')
