# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#
#   DESCRIPTION :       This tool is used to create/update asset library Masterscene
#   DOC :               https://hackmd.io/PznYjv9ZQNqTQznznvbwMA
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import logging
import socket
import getpass
import re

try:
    import sgtk
    import maya.cmds as cmds
except ImportError:
    pass

from ....studio.libs.updates import scene as update_scene
from ....studio.libs.reads import nodes as read_nodes


# TODO: extract constant vars (eg. ROOT_SET = "MasterSets")
class UpdateMasterScene(object):
    """
    - Update master scene selection sets, it is recommended to delete all sets before
    - Import missing assets by comparing selection sets and Master topnode content
    - If a var is also a sub and you don't have it in scene, it will be import only one time
    - Update assets by comparing source attr and Shotgun path
    - Link asset to set, does only work if a sub has transform under its topnode
    - Allow user to see whats common, unique or orphan by adding colors in the outliner
    """
    def __init__(self):
        # Get the engine instance that is currently running.
        current_engine = sgtk.platform.current_engine()
        # Grab the pre-created Sgtk instance from the current engine.
        self.tk = current_engine.sgtk
        self.sg = current_engine.shotgun
        self.loader_app = current_engine.apps.get("tk-multi-loader2")
        current_context = current_engine.context
        # Import module from tk-framework-shotgun
        fw_shotgun = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-shotgun')
        shotgun_reads = fw_shotgun.import_module('studio.libs.reads')
        self.shotgun_read_steps = shotgun_reads.steps
        self.shotgun_read_assets = shotgun_reads.assets
        self.shotgun_read_published_files = shotgun_reads.published_files
        self.shotgun_read_tasks = shotgun_reads.tasks
        self.shotgun_read_asset_libraries = shotgun_reads.asset_libraries
        self.shotgun_read_common = shotgun_reads.common
        task_template_helper = fw_shotgun.import_module("studio.tools.task_templates.task_template_helper")
        self.TaskTemplateHelper = task_template_helper.TaskTemplateHelper()
        # Import module from tk-framework-common
        fw_common = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-common')
        extra_logger = fw_common.import_module("studio.tools.common.logger.extra_logger")
        self.extra_logger = extra_logger.ExtraLogger()
        # Set master var
        self.root_set = 'MasterSets'
        self.set_suffixe = 'SplitSet'
        self.task_template_attr = 'TaskTemplate'
        self.parent_var_attr = 'ParentVariation'
        self.extension = '.ma'
        self.source_attr = 'source'
        self.derived_task_attr = 'from_task'
        self.common_group = 'Common_Grp'
        self.elt_group = 'Elt_Default_Grp'
        self.assembly_group = 'Assemblies_Grp'
        self.trash_group = 'Trash_Grp'
        self.master_groups_list = [self.elt_group, self.assembly_group, self.trash_group, self.common_group]
        self.topnode_suffixe = 'Top'
        # Set others
        self.what_to_import = []
        self.failures = []
        # Get assetLibrary info
        self.assetlib_name = current_context.entity['name']
        self.assetlib_id = current_context.entity['id']
        self.task_name = current_context.task['name']
        self.project_id = current_context.project['id']
        self.step_name = self.shotgun_read_steps.get_step_short_name(self.sg, current_context.step['name'])
        self.sg_asset_mdl_step = {'id': 14, 'name': 'Modeling', 'type': 'Step'}
        self.sg_asset_build_step = {'id': 206, 'name': 'Build', 'type': 'Step'}
        self.project_assets_path = os.path.join((self.tk.roots).get('primary'), 'assets')
        self.master_group = '{}_{}_{}_{}'.format(self.assetlib_name, self.step_name, self.task_name, self.topnode_suffixe)
        # Prepare extra log
        user_name = getpass.getuser().replace('.', '')
        host_name = socket.gethostname()
        log_folder = os.path.join(self.project_assets_path, self.assetlib_name, self.step_name, 'work', 'maya', 'logs')
        log_path = os.path.join(log_folder, 'update_master_{}_{}_{}_{}.log'.format(self.assetlib_name, self.step_name, user_name, host_name))
        # NOTE Vicky: Shortcut:
        # self.extra_logging = extra_logger.ExtraLogger().execute_logger(logger_path)
        # and inside your execute_logger() you do a `return logging.getLogger()` in the end?
        self.extra_logger.execute_logger(log_path)
        self.extra_logging = logging.getLogger()
        # Get assetlib variation from SG
        sg_variation_tmp = self.shotgun_read_asset_libraries.get_assets_from_assetslib_name(self.sg, self.assetlib_name, self.project_id)
        # Create the task template helper for each variation
        sg_variation = self.update_variations_task_template(sg_variation_tmp)
        # Remove var which are not in the right Task Template
        self.sg_variation = self.clean_sg_variation(sg_variation)
        # Get variations and subs from assetlib_name
        self.shotgun_assets = self.get_asset_from_sg()

    def execute(self):
        self.update_master_sets()
        self.update_elt_default()
        self.import_missing_references()
        self.update_existing_references()
        self.quick_sorting_set()
        self.apply_outliner_color()

    # -------------------------------------------------------------------------------------------------------------------------------
    # UTILS

    def create_master_grp_and_set(self):
        # Create master grp
        cmds.createNode('transform', n=self.common_group)
        cmds.createNode('transform', n=self.trash_group)
        cmds.createNode('transform', n=self.elt_group)
        cmds.createNode('transform', n=self.assembly_group)
        # Create master grp
        cmds.createNode('transform', n=self.master_group)
        # Create root set
        cmds.sets(n=self.root_set, em=True)

    def center_selected_object(self):
        """
        Sets the pivot of a group of meshes at its center
        Puts this group at world center
        :return: all centered object and their respective center
        :rtype: dict
        """
        obj_centers = {}
        # Get transform to center
        obj_list = cmds.ls(sl=True, l=True)
        for obj in obj_list:
            # Freeze obj
            cmds.makeIdentity(obj, apply=True, t=1, r=1, s=1, n=0)
            # Center pivot to object
            center = cmds.objectCenter(obj, gl=True)
            cmds.xform(obj, piv=center)
            # Center object to world by reverting center values
            cmds.setAttr('{}.translate'.format(obj), -float(center[0]), -float(center[1]), -float(center[2]), 'double3')
            # Freeze again
            cmds.makeIdentity(obj, apply=True, t=1, r=1, s=1, n=0)
            self.extra_logging.info('Transform "{}" has been centered to world.'.format(obj))
            obj_centers[obj] = center

        return obj_centers

    def get_asset_from_sg(self):
        """
        :return: a dict {variation : [sub1, sub2]}
        :rtype: dict
        """
        variation_dict_to_return = {}
        for variation in self.sg_variation:
            exact_imported_sub_list = []
            variation_name = variation['code']
            # Get sub from SG
            sub_from_sg_list = self.shotgun_read_assets.get_sub_assets_from_asset_recursive(self.sg, variation['id'], self.project_id)
            # Get number of subs
            for sub in sub_from_sg_list:
                exact_imported_sub_list.append(sub[-1])
            variation_dict_to_return[variation_name] = exact_imported_sub_list

        return variation_dict_to_return

    def update_variations_task_template(self, sg_variations):
        sg_variation_new = []
        for sg_var in list(sg_variations):
            task_template_helper = self.TaskTemplateHelper(sg_var["task_template"], self.sg, self.extra_logging)
            sg_var["task_template_helper"] = task_template_helper
            sg_variation_new.append(sg_var)

        return sg_variation_new

    def clean_sg_variation(self, sg_variation):
        # Remove var which are not ELT Default or ASSEMBLY
        for sg_var in list(sg_variation):
            variation_name = sg_var.get('code')
            task_template_helper = sg_var.get("task_template_helper")

            if not task_template_helper.is_assembly() and not task_template_helper.is_element():
                sg_variation.remove(sg_var)
                self.extra_logging.info('"{}" has been removed from variations list because of its Task Template: "{}" (type: {})'.format(
                                        variation_name, task_template_helper.name, task_template_helper.structure_type))
        return sg_variation

    def clean_master_set(self, current_sets):
        obsolete_sets = []
        delete_something = False
        for current_set in current_sets:
            if not current_set.endswith(self.set_suffixe) and not current_set == self.root_set:
                obsolete_sets.append(current_set)
                cmds.delete(current_set)
                delete_something = True
        if delete_something is True:
            self.extra_logging.warning('Obsolete sets have been deleted: {}.'.format(obsolete_sets))

    def add_bkl_to_set(self, parent_variation_dict):
        """
        It will add the list of parent variation from bkl to parent variation with the right task
        """
        for var_asset in parent_variation_dict:
            for sub_asset in parent_variation_dict.get(var_asset):
                sub_set_name = '{}_{}_{}'.format(sub_asset, self.step_name, self.set_suffixe)
                parent_var_name = '{}_{}'.format(self.parent_var_attr, var_asset)
                track_parent_attr = '{}.{}'.format(sub_set_name, parent_var_name)
                if cmds.objExists(sub_set_name):
                    if not cmds.objExists(track_parent_attr):
                        cmds.addAttr(sub_set_name, longName=parent_var_name, dt='string')
                    cmds.setAttr(track_parent_attr, str(parent_variation_dict.get(var_asset).get(sub_asset)), type='string')

    def is_set_unique(self):
        """
        Return common or unique set in a dict sets_to_highlight = {'unique':[], 'common':[]}
        Use to color set members in outliner
        :rtype: dict
        """
        all_sets_from_scene = cmds.ls('*_{}'.format(self.set_suffixe), set=True)
        # Get all subset from scene
        list_of_subset = []
        sets_to_highlight = {}
        sets_to_highlight['unique'] = []
        sets_to_highlight['common'] = []
        for set_found in all_sets_from_scene:
            set_content = cmds.sets(set_found, q=True)
            if set_content is not None:
                if cmds.objectType(set_content[0]) == 'objectSet':
                    list_of_subset += set_content
            set_with_no_duplicata = list(set(list_of_subset))
            # Unique or common sub ?
            for set_found in set_with_no_duplicata:
                if list_of_subset.count(set_found) == 1:
                    sets_to_highlight['unique'].append(set_found)
                elif list_of_subset.count(set_found) > 1:
                    sets_to_highlight['common'].append(set_found)
        return sets_to_highlight

    def apply_outliner_color(self):
        """
        Get unique and common set, then color them
        """
        sets_to_highlight = self.is_set_unique()
        for dict_set in sets_to_highlight:
            if sets_to_highlight[dict_set]:
                for set_name in sets_to_highlight[dict_set]:
                    all_set_content_list = []
                    set_content_query = cmds.ls(cmds.sets(set_name, q=True), l=True, type='transform')
                    all_set_content_list += set_content_query
                    for content_element in set_content_query:
                        all_set_content_list.append(content_element)
                        all_set_content_list += cmds.ls(cmds.listRelatives(content_element, ad=True, f=True), type='transform')
                    for element_from_set in all_set_content_list:
                        update_scene.set_outliner_color_attr(dict_set, element_from_set)

    def quick_sorting_set(self):
        """
        Link elt element hierarchy to their relative set
        """
        all_sets_from_scene = cmds.ls('*_{}'.format(self.set_suffixe), set=True)
        # Get all subset from scene
        list_of_subset = []
        set_with_no_duplicata = []
        for set_found in all_sets_from_scene:
            set_content = cmds.sets(set_found, q=True)
            if set_content is not None:
                if cmds.objectType(set_content[0]) == 'objectSet':
                    for sub_set in set_content:
                        if cmds.objectType(sub_set) == 'objectSet':
                            list_of_subset.append(sub_set)
            set_with_no_duplicata = list(set(list_of_subset))

        for sub_set in set_with_no_duplicata:
            # Add subs grp content to sub set
            sub_grp = sub_set.replace(self.set_suffixe, self.topnode_suffixe)
            sub_grp_longname = "|{}|{}|{}".format(self.master_group, self.elt_group, sub_grp)
            if cmds.objExists(sub_grp_longname):
                sub_grp_content = cmds.listRelatives(sub_grp_longname, f=True)
                if sub_grp_content:
                    for content_found in sub_grp_content:
                        cmds.sets(content_found, add=sub_set)
                        self.extra_logging.info('"{}" group has been added to "{}" set.'.format(content_found, sub_set))
                else:
                    self.extra_logging.warning('"{}" group is empty, found nothing to add to "{}" set.'.format(sub_grp, sub_set))

    def highlight_no_source(self):
        """
        Color orphans nodes / transforms with no source attr
        """
        all_transform = cmds.ls(type='transform', l=True)
        nodes_to_check = []
        non_trackable_list = []
        # Remove default nodes
        non_default_nodes = read_nodes.non_default_nodes_only(all_transform)
        # Remove Master scene nodes
        master_nodes = self.master_groups_list + ['_{}'.format(self.topnode_suffixe)]
        for non_default in non_default_nodes:
            if not any(non_default.endswith(orig_master) for orig_master in master_nodes):
                nodes_to_check.append(non_default)
        for node_found in nodes_to_check:
            if cmds.objExists('{}.source'.format(node_found)) is not True:
                self.extra_logging.warning('"{}" has no attribute "source" and cannot be tracked.'.format(node_found))
                non_trackable_list.append(node_found)
            elif cmds.objExists('{}.source'.format(node_found)) is True and cmds.getAttr('{}.source'.format(node_found)) == '':
                self.extra_logging.warning('"{}" has an empty attribute "source" and cannot be tracked.'.format(node_found))
                non_trackable_list.append(node_found)
        # Highlight non trackable nodes in the outliner - red color
        for non_trackable_element in non_trackable_list:
            update_scene.set_outliner_color_attr('no track', non_trackable_element)
        # Select non trackable nodes
        cmds.select(non_trackable_list)
        if len(cmds.ls(sl=True)) == 0:
            self.extra_logging.info('No orphan found.')

    def get_asset_publish_path(self, sg_asset, parent_group):
        """
        Get asset publish path from shotgun data
        Use "local_path_windows"
        """
        asset_name = sg_asset.get('name')  # TODO: should use code which is shotgun friendly
        if asset_name is None:
            asset_name = sg_asset.get('code')
        self.extra_logging.info('Looking for the latest published BridgeModelingPreRig of: "{}".'.format(asset_name))

        sg_build_task = self.shotgun_read_tasks.get_task_by_name(self.sg, 'BridgeModelingPreRig', self.sg_asset_build_step, sg_asset)
        latest_publish_scene = self.shotgun_read_published_files.get_latest_publish_for_task(self.sg, sg_asset, sg_build_task)

        if latest_publish_scene is not None:
            self.extra_logging.info('Found: "{}".'.format(latest_publish_scene.get('path').get('local_path_windows')))
        else:
            self.extra_logging.error('No publish path found on Shotgun for "{}"!'.format(asset_name))
        return latest_publish_scene

    def create_missing_group(self, asset_grp_name, parent_group):
        """
        Create missing top node and parent them to sub or master group
        """
        if not cmds.objExists(asset_grp_name):
            cmds.createNode('transform', n=asset_grp_name)
            # Parent grp if parent is not None
            if parent_group is not None:
                cmds.parent(asset_grp_name, parent_group)
                self.extra_logging.info('Group "{}" has been created and parented to "{}".'.format(asset_grp_name, parent_group))
            # Or pass
            else:
                self.extra_logging.info('Group "{}" has been created.'.format(asset_grp_name))

    def apply_source_attr(self, path, sg_derived_task, import_nodes_list):
        for i in list(import_nodes_list):
            if cmds.objectType(i) != 'transform':
                import_nodes_list.remove(i)
            else:
                # Add source path attr for tracking/update
                source_path_attr = '{}.{}'.format(i, self.source_attr)
                if not cmds.objExists(source_path_attr):
                    cmds.addAttr(i, longName=self.source_attr, dt='string')
                cmds.setAttr(source_path_attr, path, type='string')
                # Add derived task attr for tracking
                source_task_attr = '{}.{}'.format(i, self.derived_task_attr)
                if not cmds.objExists(source_task_attr):
                    cmds.addAttr(i, longName=self.derived_task_attr, dt='string')
                try:
                    cmds.setAttr(source_task_attr, sg_derived_task, type='string')
                except Exception as e:
                    self.extra_logging.error('No derived task found for {}'.format(i))
                    self.extra_logging.error(e)

    def get_asset_dict(self, asset_name, parent_group):
        """
        :return: a dict with asset name, latest publish path and id
        :rtype: dict
        """
        asset_dict = self.shotgun_read_common.get_entity_by_name(self.sg, 'Asset', asset_name)
        asset_dict['name'] = asset_name
        asset_path_dict = self.get_asset_publish_path(asset_dict, parent_group)
        if asset_path_dict is not None:
            asset_dict['path'] = asset_path_dict.get('path').get('local_path_windows')
            asset_dict['publish_id'] = asset_path_dict.get('id')
            asset_dict['sg_derived_task'] = asset_path_dict.get('sg_derived_task')
            self.extra_logging.info('Publish path, id and derived task: "{}, {}, {}"'.format(asset_dict['path'], asset_dict['publish_id'], asset_dict['sg_derived_task']))
        else:
            asset_dict['path'] = None
            asset_dict['publish_id'] = None
            asset_dict['sg_derived_task'] = None

        return asset_dict

    def parent_topnodes(self):
        """
        Parent all "topnodes" to master grp
        """
        top_nodes = cmds.ls(read_nodes.get_top_node(), l=False)
        top_nodes.remove(self.master_group)
        for top_node_found in top_nodes:
            is_parented = cmds.listRelatives(top_node_found, ap=True)
            if not is_parented or self.master_group not in is_parented:
                cmds.parent(top_node_found, self.master_group)
                self.extra_logging.info('"{}" has been parented to "{}".'.format(top_node_found, self.master_group))
            else:
                self.extra_logging.error('Something wrong happened when parenting "{}" to "{}"! One of the imported scene seems to already be a Master scene.'.format(top_node_found, self.master_group))

    def execute_load_file(self, load_as, sg_data, params=None):
        """
        Call the loader method to import elt default and reference assemblies
        TODO: If the inheritance of the class changes to crudfiles plugin, remove this and directly use the load function from crudfiles
        """
        app = self.loader_app
        if not app:
            self.extra_logging.error("App {} wasn't found. ".format(app))
            return
        if not load_as or not sg_data:
            self.extra_logging.error("Loading file failed because of missing info")
        action = {
            "sg_publish_data": sg_data,
            "name": load_as,
            "params": params
        }
        try:
            result = app.execute_hook_method("actions_hook", "execute_action", **action)
            returned_nodes = result.get('rnn', None)
        except Exception, e:
            app.log_exception("Could not execute execute_action hook: %s" % e)
            returned_nodes = None

        return returned_nodes

    # -------------------------------------------------------------------------------------------------------------------------------
    # UPDATE SETS

    def update_master_sets(self):
        """
        Update selection sets in Master scene from Shotgun data
        Usefull if the breakdown as been updated
        """
        # Get selection sets in scene
        current_sets = read_nodes.list_non_default_set()
        # Be sure we have a root set
        if self.root_set not in current_sets:
            cmds.sets(n=self.root_set, em=True)
            self.extra_logging.info('Root set "{}" has been created.'.format(self.root_set))
        if self.task_name == 'Master':
            # Check if set exists, if not create set
            for variation_found_in_dict in self.shotgun_assets:
                # Prepare task template attr
                for sg_var in self.sg_variation:
                    if sg_var.get('code') == variation_found_in_dict:
                        variation_task_template = sg_var.get('task_template_helper').description
                        continue
                # Create var set
                variation_set = '{}_{}_{}'.format(variation_found_in_dict, self.step_name, self.set_suffixe)
                if variation_set not in current_sets:
                    if variation_set not in read_nodes.list_non_default_set():
                        cmds.sets(n=variation_set, em=True)
                        self.extra_logging.info('Variation set "{}" has been created.'.format(variation_set))
                    else:
                        self.extra_logging.info('Variation set "{}" already exists.')
                    cmds.sets(variation_set, add=self.root_set)
                    cmds.addAttr(variation_set, ln=self.task_template_attr, dt='string')
                    cmds.setAttr('{}.{}'.format(variation_set, self.task_template_attr), variation_task_template, type='string')
                    self.extra_logging.info('Variation set "{}" has been parented to "{}".'.format(variation_set, self.root_set))
                # Create sub sets
                for sub_found in self.shotgun_assets[variation_found_in_dict]:
                    sub_set = '{}_{}_{}'.format(sub_found, self.step_name, self.set_suffixe)
                    # We need to query current sets dynamically
                    if sub_set not in read_nodes.list_non_default_set():
                        cmds.sets(n=sub_set, em=True)
                        cmds.sets(sub_set, add=variation_set)
                        self.extra_logging.info('Sub set "{}" has been created.'.format(sub_set))
                    else:
                        self.extra_logging.info('Sub set "{}" already exists.')
                    cmds.sets(sub_set, add=variation_set)
                    self.extra_logging.info('Sub set "{}" has been added to variation set "{}".'.format(sub_set, variation_set))
        else:
            self.extra_logging.error('This tool has been created for {} only!'.format(self.task_name))

    def is_root_set_existing(self):
        if not cmds.objExists(self.root_set):
            self.extra_logging.error('"{}" not found! You need to recreate your sets by clicking on the Update Sets button!'.format(self.root_set))
            raise Exception('"{}" not found!'.format(self.root_set))

    # -------------------------------------------------------------------------------------------------------------------------------
    # UPDATE ELT DEFAULT

    def import_elt_default(self, sg_sub):
        sub_name = sg_sub.get('name')
        sg_path = sg_sub.get('path')
        sg_publish_id = sg_sub.get('publish_id')
        sub_top_node = '{}_{}_{}'.format(sub_name, self.step_name, self.topnode_suffixe)
        if sg_path and sg_publish_id:
            publish_data = self.shotgun_read_published_files.get_published_data(self.sg, sg_publish_id, self.project_id)
            list_of_nodes = self.execute_load_file('import', publish_data, params={'use_namespace': False})
            # Add publish scene source attr
            # It will allow us to track transforms and orphans in master scene
            self.apply_source_attr(sg_sub.get('path'), sg_sub.get('sg_derived_task'), list_of_nodes)
            # Parent imported topnode to self.elt_group
            top_nodes = cmds.ls(read_nodes.get_top_node())
            top_nodes.remove(self.master_group)
            for top_node in top_nodes:
                if sub_top_node in top_node:
                    cmds.parent(top_node, self.elt_group)
                    self.extra_logging.info('Sub "{}" has been parented to "{}"'.format(top_node, self.elt_group))
                elif top_node not in self.master_groups_list and top_node not in self.failures:
                    update_scene.set_outliner_color_attr('error', top_node)
                    self.failures.append(top_node)
                    self.extra_logging.error('Sub "{}" cannot be parented to "{}" because its topnode is not named properly.'.format(sub_name, self.step_name))
                    self.extra_logging.error('Sub topnode "{}" should be named "{}".'.format(top_node, '{}_{}_{}'.format(sub_name, self.step_name, self.topnode_suffixe)))
        else:
            self.extra_logging.error('Publish path or publish id not found for "{}"!'.format(sub_name))

    def update_elt_default(self):
        """
        From existing selection subs sets, import relative scene if exists
        """
        # Be sure self.root_set exists
        self.is_root_set_existing()
        # Get sub sets and only sub sets
        current_sets = read_nodes.list_non_default_set()
        for set_found in list(current_sets):
            # TODO: CLEANUP
            if self.task_template_attr in cmds.listAttr(set_found):
                if "element" not in cmds.getAttr('{}.{}'.format(set_found, self.task_template_attr)).lower():
                    current_sets.remove(set_found)
            elif set_found == self.root_set:
                current_sets.remove(set_found)
        self.clean_master_set(current_sets)
        # Be sure we need to import something
        for sub_set_found in current_sets:
            need_import = False
            sub_top_node = sub_set_found.replace(self.set_suffixe, self.topnode_suffixe)
            asset_grp_name_list = cmds.ls(sub_top_node, l=True)
            if asset_grp_name_list:
                asset_grp_name = asset_grp_name_list[0]
            else:
                asset_grp_name = sub_top_node
            # Be sure groups exist and take a look at their content
            if cmds.objExists(asset_grp_name):
                if not cmds.listRelatives(asset_grp_name, ad=True):
                    self.extra_logging.warning('Asset group is empty: {}'.format(sub_top_node))
                    self.extra_logging.warning('Need to import: {}'.format(sub_top_node))
                    need_import = True
                    # Else update if needed, see below
            else:
                self.extra_logging.warning('Asset group not found: {}'.format(sub_top_node))
                self.extra_logging.warning('Need to import: {}'.format(sub_top_node))
                need_import = True
            # Get sub data
            sub_name = sub_top_node.split('_{}'.format(self.step_name))[0]
            sg_sub = self.get_asset_dict(sub_name, self.elt_group)
            sg_path = sg_sub.get('path')
            # And import the latest scene we can find on file system if needed
            if need_import is True:
                self.import_elt_default(sg_sub)
            # Or check if we need to update sub
            else:
                transform_source_dict = {}
                source_transform_dict = {}
                attr_value_list = []
                # Get source path of all transforms and store them in a dict
                sub_transform_list = cmds.ls(cmds.listRelatives(asset_grp_name, ad=True, f=True), exactType='transform', l=True) + cmds.ls(asset_grp_name, l=True)
                for transform_found in sub_transform_list:
                    source_attr = '{}.{}'.format(transform_found, self.source_attr)
                    if cmds.objExists(source_attr):
                        attr_value = cmds.getAttr(source_attr)
                        transform_source_dict[transform_found] = attr_value
                        attr_value_list.append(attr_value)
                clean_value_list = list(set(attr_value_list))
                # Put all transform with same value in a list
                for value_found in clean_value_list:
                    transform_list = []
                    for transform, attr in transform_source_dict.items():
                        if attr == value_found:
                            transform_list.append(transform)
                    source_transform_dict[value_found] = transform_list
                # Looking for new version
                for source_found in source_transform_dict:
                    if source_found != sg_path:
                        self.extra_logging.info('Source path and Shotgun path are different!')
                        self.extra_logging.info('Source path: "{}"'.format(source_found))
                        self.extra_logging.info('Shotgun path: "{}"'.format(sg_path))
                        self.extra_logging.info('Prepare to import "{}" and remove old version.'.format(sg_path))
                        # Get all old elements wherever they are in scene
                        what_to_delete = cmds.ls(source_transform_dict[source_found])
                        # Be sure to clear selection sets before deleting assets
                        for element_to_delete in what_to_delete:
                            list_of_co = cmds.listConnections(element_to_delete)
                            if list_of_co:
                                for connection_found in list_of_co:
                                    if connection_found.endswith(self.set_suffixe):
                                        cmds.sets(clear=connection_found)
                        # Delete assets
                        cmds.delete(what_to_delete)
                        # And import scene from Shotgun path
                        self.import_elt_default(sg_sub)

    # -------------------------------------------------------------------------------------------------------------------------------
    # UPDATE ASSEMBLIES

    def import_missing_references(self, create=False):
        """
        From existing selection subs sets, import relative scene if exists
        """
        self.extra_logging.info('----------------------------------------------------------------------------')
        # Be sure self.root_set exists
        self.is_root_set_existing()
        # Create assemblies topnodes
        for variation_name in self.shotgun_assets:
            self.extra_logging.info('----------------------------------------------------------------------------')
            self.extra_logging.info('Working on Variation: "{}"'.format(variation_name))
            variation_id = None
            for var_dict in self.sg_variation:
                task_template_helper = var_dict.get("task_template_helper")
                name = var_dict['code']
                if name == variation_name:
                    variation_id = var_dict['id']
                    elt = False
                    if task_template_helper.is_element():
                        self.extra_logging.info('Variation "{}" is not an Assembly.'.format(variation_name))
                        elt = True
                        continue
            # NOTE Vicky: `if elt:` is the same check, since elt is a boolean (either true/false)
            if elt is True:
                continue

            # Check the number of subassets of variation_name
            instances_count_dict = self.shotgun_read_assets.get_instance_number(self.sg, variation_id)
            self.extra_logging.info("Instance count dict {}".format(instances_count_dict))

            variation_top_node = '{}_{}_{}'.format(variation_name, self.step_name, self.topnode_suffixe)
            variation_top_node_tmp = '|{}'.format(variation_top_node)
            if create is False:
                variation_top_node_ln = '|{}|{}|{}'.format(self.master_group, self.assembly_group, variation_top_node)
            else:
                variation_top_node_ln = '|{}|{}'.format(self.assembly_group, variation_top_node)
            if not cmds.objExists(variation_top_node_ln):
                cmds.createNode('transform', n=variation_top_node)
                cmds.parent(variation_top_node_tmp, self.assembly_group)

            # Get subassets to import under each assembly node // A sub can be an ELT or an ASB
            for sub_name in self.shotgun_assets[variation_name]:
                # Get exact sub instance count we need to import: Add sub children var to count and remove sub already found in scene
                sub_count = self.get_exact_instance_count_of_sub(sub_name, instances_count_dict, variation_name, variation_id)

                # If sub_top_node already exists, ignore it
                if sub_count == 0:
                    continue

                # Importing the subasset in ref for each time it's casted // TODO WIP ASB OF ASB
                for _ in range(1, sub_count + 1):
                    elt = True
                    for var_dict in self.sg_variation:
                        task_template_helper = var_dict.get("task_template_helper")
                        name = var_dict['code']
                        if name == sub_name:
                            # If sub is Assembly
                            if task_template_helper.is_assembly():
                                self.extra_logging.info('Need to import ASB Variation: "{}"'.format(variation_name))
                                self.import_subasset_ref(sub_name, variation_top_node_ln)
                                elt = False

                    # If sub is ELT Default
                    if elt is True:
                        self.extra_logging.info('Need to import ELT Variation: "{}"'.format(sub_name))
                        self.import_subasset_ref(sub_name, variation_top_node_ln)

        # Hide reference nodes from outliner
        display_change = update_scene.display_reference_nodes(False)
        if display_change is True:
            self.extra_logging.info('References Nodes display has been hidden.')
            self.extra_logging.info('You can set it by using the Display menu of the Outliner.')

    def get_exact_instance_count_of_sub(self, sub_name, instances_count_dict, variation_name, variation_id):
        variation_top_node = '{}_{}_{}'.format(variation_name, self.step_name, self.topnode_suffixe)
        self.extra_logging.info('Looking for instance count of: "{}" and its children.'.format(sub_name))
        # Look at sub_count of sub in instances_count_dict
        try:
            # Could be None or a number > 1
            sub_count = instances_count_dict[sub_name]
            self.extra_logging.info('Instance count for "{}" is {}.'.format(sub_name, sub_count))
        except Exception as e:
            # If sub_name not in instances_count_dict
            sub_count = 0
            self.extra_logging.warning('Asset "{}" is not directly breakdowned in "{}" (probably because the Assembly is using children variations)'.format(sub_name, variation_name))
            self.extra_logging.warning(e)
        # If sub_name found and its sub_count is None, put default value to 1
        if sub_count is None:
            sub_count = 1
            self.extra_logging.info('Instance count for "{}" was "None and has been set to 1.'.format(sub_name))

        # If parent variation in shotgun_assets, look for their children
        children_found = self.shotgun_read_assets.find_child_variation(self.sg, sub_name, variation_id)
        if children_found:
            self.extra_logging.info('Found children variations and add them to parent variation count: "{}"'.format(children_found))
            for child_found in children_found:
                child_name = child_found.get('code')
                child_count = instances_count_dict[child_name]
                if child_count is None:
                    child_count = 1

                sub_count += child_count
                self.extra_logging.info('Add "{}" to "{}" instance count for child variation "{}".'.format(child_count, sub_name, child_name))

            self.extra_logging.info('The instance count of parent variation "{}" is now "{}".'.format(sub_name, sub_count))

        # Check if sub already exists under assembly/variation top node
        sub_top_node = '{}_{}_{}'.format(sub_name, self.step_name, self.topnode_suffixe)
        sub_top_node_ln = '|{}|{}|{}|*:{}'.format(self.master_group, self.assembly_group, variation_top_node, sub_top_node)

        if cmds.ls(sub_top_node_ln) != []:
            sub_found_count = len(cmds.ls(sub_top_node_ln))
            self.extra_logging.info('Found {}/{}: "{}"'.format(sub_found_count, sub_count, sub_top_node_ln))
            sub_count = sub_count - sub_found_count

        return sub_count

    def import_subasset_ref(self, sub_name, variation_top_node):
        """
        Import a subasset as reference
        """
        sg_sub = {}
        already_known_sub = {}
        sub_top_node = '{}_{}_{}'.format(sub_name, self.step_name, self.topnode_suffixe)

        # Be sure we don't know sub before querying shotgun
        if sub_name not in already_known_sub:
            sg_sub = self.get_asset_dict(sub_name, self.assembly_group)
            if sg_sub:
                already_known_sub[sub_name] = sg_sub
        else:
            sg_sub = already_known_sub.get(sub_name)
            self.extra_logging.info('"{}" reference path already known: {}.'.format(sub_name, sg_sub))

        if sg_sub.get('path') and sg_sub.get('publish_id'):
            if sg_sub['path'] is not None:
                publish_data = self.shotgun_read_published_files.get_published_data(self.sg, sg_sub['publish_id'], self.project_id)
                returned_nodes = self.execute_load_file('reference', publish_data)
                if not returned_nodes:
                    raise Exception('Something went wrong during "{}" import! The loader may be broken.'.format(sg_sub['path']))

                top_nodes = cmds.ls(read_nodes.get_top_node())
                top_nodes.remove(self.master_group)
                for top_node in top_nodes:
                    if sub_top_node in top_node:
                        cmds.parent(top_node, variation_top_node)
                        self.extra_logging.info('Reference "{}" has been parented to "{}"'.format(top_node, variation_top_node))
                    elif top_node not in self.master_groups_list and top_node not in self.failures:
                        update_scene.set_outliner_color_attr('error', top_node)
                        self.failures.append(top_node)
                        self.extra_logging.error('Reference "{}" cannot be parented to "{}" because its topnode is not named properly.'.format(sub_name, variation_top_node))
                        self.extra_logging.error('Reference topnode "{}" should be named "{}".'.format(top_node, '*:{}_{}_{}'.format(sub_name, self.step_name, self.topnode_suffixe)))
        else:
            self.extra_logging.error('Publish path or publish id not found for "{}"!'.format(sub_name))
        # Hide reference nodes from outliner
        display_change = update_scene.display_reference_nodes(False)
        if display_change is True:
            self.extra_logging.info('References Nodes display has been hidden.')
            self.extra_logging.info('You can set it by using the Display menu of the Outliner.')

    def update_existing_references(self):
        """
        Get latest published files from reference nodes
        Replace ref if latest path found different
        TODO: should use shotgun breakdown: C:/Shotgun/tk-config-millimages/hooks/tk_multi_breakdown/tk_maya/scene_operations.py'
        """
        # Be sure self.root_set exists
        self.is_root_set_existing()

        nodes = cmds.ls(type='reference')
        for node in nodes:
            ref_connections = cmds.listConnections(node)
            if not ref_connections or len(ref_connections) < 2:
                reference_path = cmds.referenceQuery(node, f=True)
                # Reference string operation
                if '{' in reference_path:
                    reference_path = reference_path.split('{')[0]
                asset_name = os.path.normpath(reference_path).split(os.sep)[7]
                sg_asset = self.shotgun_read_assets.get_asset_by_name(self.sg, asset_name, self.project_id, 'Asset')
                # Get latest path on Shotgun
                latest_publish_path = self.get_asset_publish_path(sg_asset, self.assembly_group)
                # Update file if needed
                if os.path.normpath(reference_path) != os.path.normpath(latest_publish_path.get('path').get('local_path_windows')):
                    cmds.file(latest_publish_path.get('path').get('local_path_windows'), loadReference=node)
                    self.extra_logging.info('"{}" path has been updated:'.format(node))
                    self.extra_logging.info('Old path: {}'.format(reference_path))
                    self.extra_logging.info('New path: {}'.format(latest_publish_path.get('path').get('local_path_windows')))

    def get_assembly_transforms(self, selected_set):
        """
        Get transforms edits from references in scene ['translate', 'rotate', 'scale']
        Only looking forsub topnode ref edit
        """
        assembly_transforms_dict = {}
        assembly_dict = {}
        refs_list = cmds.ls(type='reference', rf=True)
        transform_attrs = ['translate', 'rotate', 'scale']
        # Be sure assembly selected set exists
        if cmds.objExists(selected_set):
            assembly_name = selected_set.split('_{}'.format(self.step_name))[0]
            assembly_top_node = cmds.ls(selected_set.replace(self.set_suffixe, self.topnode_suffixe), l=True)[0]  # TODO: ignore Trash Grp
            references_to_split = cmds.listRelatives(assembly_top_node, f=True)
        else:
            self.extra_logging.error('Set "{}" does not exist!'.format(selected_set))
            return
        # Get subs ref edit of assembly
        for ref in refs_list:
            list_of_edits = []
            wrong_ref_edit = []
            transform_dict = {}
            # Get the topnode of the reference
            sub_topnode = [i for i in cmds.ls(cmds.referenceQuery(ref, nodes=True), l=True, type='transform', r=True) if i.endswith('_{}'.format(self.topnode_suffixe))]
            if sub_topnode:
                sub_name = sub_topnode[0]
                sub_path = cmds.referenceQuery(ref, filename=True)
                # Be sure it is related to the selected split set
                if sub_name in references_to_split:
                    self.extra_logging.info('Looking for reference edit on: "{}" ({})'.format(sub_name, ref))
                    # Get ref edit attr on topnode
                    edit_attr_list = cmds.referenceQuery(ref, editAttrs=True)
                    if edit_attr_list:
                        # Log an error if wrong ref edit found
                        for edited_attr in edit_attr_list:
                            list_of_edits = cmds.referenceQuery(ref, editStrings=True)
                            # Remove parent edit if found
                            for edit in list(list_of_edits):
                                if edit.startswith('parent'):
                                    list_of_edits.remove(edit)
                            if edited_attr not in transform_attrs:
                                wrong_ref_edit.append(edited_attr)
                            if wrong_ref_edit:
                                self.extra_logging.error('Found reference edit on wrong attr: {}'.format(wrong_ref_edit))
                                continue
                        # Get values from mel command foundM in ref edit
                        for edit_found in list_of_edits:
                            set_attr = edit_found.split('{}.'.format(sub_name))[-1].split(' -type')[0]
                            pattern = 'setAttr {}.{}'.format(sub_name, set_attr)
                            result = re.match(edit_found, pattern)
                            # If match found, get values
                            if result:
                                values = edit_found.split('"double3" ')[-1]
                                transform_dict[set_attr] = values.split(' ')
                            else:
                                self.extra_logging.warning('No transform edit found for "{}"'.format(pattern))
                        # Log all edits found on sub, this is the dict we will use to create assembly scene
                        self.extra_logging.info('Found reference edit: {}'.format(transform_dict))
                    else:
                        self.extra_logging.info('Found no reference edit.')

                    transform_dict['path'] = sub_path
                    assembly_transforms_dict[sub_name] = transform_dict
            else:
                self.extra_logging.info('No topnode found,')

        assembly_dict[assembly_name] = assembly_transforms_dict
        self.extra_logging.info('Create assembly params: {}'.format(assembly_dict))

        return assembly_dict


if __name__ == "__main__":
    UpdateMasterScene().execute()
