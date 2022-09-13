
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#
#   DESCRIPTION :       This tool is used to create assets whatever their task / step / task template is
#   DOC :               https://hackmd.io/qVvpQWXMRwas9C78kbrE3g
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import logging
import sys
import ast

from ....studio.libs.reads import nodes as read_nodes

try:
    import sgtk
    import maya.cmds as cmds
except ImportError:
    pass


class UpdateAssetScene(object):
    """
    - Create hierarchy
    - Import parent bridge modeling as reference
    - Import subassets bridge from right context as reference
    Or
    - Update references
    """
    def __init__(self):
        # Get the engine instance that is currently running.
        current_engine = sgtk.platform.current_engine()
        # Grab the pre-created Sgtk instance from the current engine.
        self.tk = current_engine.sgtk
        self.sg = current_engine.shotgun
        current_context = current_engine.context
        # Get apps
        self.loader_app = current_engine.apps.get('tk-multi-loader2')
        self.breakdown_app = current_engine.apps.get('tk-multi-breakdown')
        # Import module from tk-framework-resources
        self.fw_resources = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-resources')
        # Import module from tk-framework-shotgun
        fw_shotgun = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-shotgun')
        shotgun_reads = fw_shotgun.import_module('studio.libs.reads')
        self.shotgun_read_steps = shotgun_reads.steps
        self.shotgun_read_assets = shotgun_reads.assets
        self.shotgun_read_published_files = shotgun_reads.published_files
        self.shotgun_read_tasks = shotgun_reads.tasks
        task_template_helper = fw_shotgun.import_module('studio.tools.task_templates.task_template_helper')
        self.TaskTemplateHelper = task_template_helper.TaskTemplateHelper()
        # Set asset var
        self.project_id = 137
        self.trash_group = 'Trash'
        self.rigging_step_name = 'Rigging'
        self.shading_step_name = 'Shading'
        self.modeling_step_name = 'Modeling'
        self.topnode_suffixe = 'Top'
        self.mesh_suffixe = 'Msh'
        self.proxy_group = 'PROXY_GRP'
        self.subassets_group = 'Subassets_Grp'
        self.asset_name = current_context.entity.get('name')
        self.modeling_bridge_name = 'BridgeModelingPreRig'
        self.mdl_step_sn = 'MDL'
        self.bridge_mdl_topnode = '{}*:{}_*_{}'.format(self.modeling_bridge_name, self.asset_name, self.topnode_suffixe)
        self.current_step = current_context.step.get('name')
        self.asset_id = current_context.entity.get('id')
        self.sg_task_template = self.shotgun_read_assets.get_asset_task_template(self.sg, current_context.entity.get('name'), self.project_id)
        self.task_template_helper = self.TaskTemplateHelper(self.sg_task_template, self.sg)
        self.task_template_name = self.sg_task_template.get('name')
        self.sg_build_step = {'type': 'Step', 'name': 'Build', 'id': 206}
        current_step_sn = self.shotgun_read_steps.get_step_short_name(self.sg, self.current_step)
        modeling_step_sn = self.shotgun_read_steps.get_step_short_name(self.sg, self.modeling_step_name)
        self.step_asset_group = '{}_{}_{}'.format(self.asset_name, current_step_sn, self.topnode_suffixe)
        self.mdl_asset_group = '{}_{}_{}'.format(self.asset_name, modeling_step_sn, self.topnode_suffixe)
        self.shading_note = 'notes'
        self.modeling_note = 'modeling_note'
        # Set bridge name depending on step
        if self.current_step == self.shading_step_name:
            self.bridge_name = 'BridgeShadingPreRig'
        elif self.current_step == self.rigging_step_name:
            self.bridge_name = 'BridgeRigging'
        elif self.current_step == self.modeling_step_name:
            self.bridge_name = self.modeling_bridge_name
        else:
            logging.error('Cannot use this tool for step "{}"'.format(self.current_step))
            raise Exception('Cannot use this tool for step "{}"'.format(self.current_step))

    # -------------------------------------------------------------------------------------------------------------
    # APPS

    def execute_load_file(self, load_as, sg_data, params=None):
        """
        Call the loader method to import elt default and reference assemblies
        """
        app = self.loader_app
        if not app:
            logging.error("App {} wasn't found. ".format(app))
            return
        if not load_as or not sg_data:
            logging.error("Loading file failed because of missing info")
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

    def update_breakdown_references(self):
        """
        Call the tk-multi-breakdown method to update asset reference and sub references if exist
        """
        results = []
        new_version = {}
        app = self.breakdown_app
        if not app:
            logging.error("App {} wasn't found. ".format(app))
            return
        # Looking for references to update
        try:
            items = app.analyze_scene()
        except Exception, e:
            app.log_exception("Could not execute execute hook action: %s" % e)
        # If reference found
        if items:
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
                if new_version.get('version') is not None and new_version.get('version') != old_version:
                    fields.update(new_version)
                    # Update reference with new version
                    try:
                        app.update_item(node_type, node_name, template, fields)
                        logging.info('Reference path of "{}" has been updated'.format(node_name))
                        logging.info('Old version: "{}" / New version: "{}"'.format(old_version, new_version.get('version')))
                        results.append(item_found)
                    except Exception, e:
                        app.log_exception("Could not execute execute hook action: %s" % e)
        else:
            logging.error('No reference found!')
        return results

    # -------------------------------------------------------------------------------------------------------------
    # UTILS

    def create_sub_groups(self):
        """
        Create Assembly scene hierarchy
        """
        if not cmds.objExists(self.subassets_group):
            cmds.createNode('transform', n=self.subassets_group)
            if self.current_step == self.rigging_step_name:
                cmds.createNode('transform', n=self.rigging_step_name)
                cmds.parent(self.rigging_step_name, self.subassets_group)
                cmds.createNode('transform', n=self.modeling_step_name)
                cmds.parent(self.modeling_step_name, self.subassets_group)
                cmds.createNode('transform', n=self.trash_group)
                cmds.hide(self.trash_group)
                cmds.parent(self.trash_group, self.subassets_group)
        else:
            logging.error('"{}" already exists in scene! If you want to import sub, please delete current group.'.format(self.subassets_group))
            raise Exception('"{}" already exists in scene!'.format(self.subassets_group))

    def create_proxy(self):
        """
        - Create proxy if asb topnode exists
        - Update proxy if already exists
        - Rename default proxy name
        """
        asb_topnode = '*:{}'.format(self.mdl_asset_group)
        # Be sure mdl parent group exists
        if not cmds.objExists(asb_topnode):
            logging.error('"{}" not found. Cannot create/update "{}" group!'.format(self.mdl_asset_group, self.proxy_group))
            return
        asb_topnode_ln = cmds.ls(asb_topnode)[0]
        # Hide ASB reference
        cmds.hide(asb_topnode)
        # Delete current proxy if already exists
        if cmds.objExists(self.proxy_group):
            logging.info('Update: "{}" group already exists and will be deleted and replaced by a new one.'.format(self.proxy_group))
            cmds.delete(self.proxy_group)
        # Then create new proxy
        karlab_location = os.path.join(self.fw_resources.disk_location, 'thirdparty')
        sys.path.append(karlab_location)
        import karlab.krig.geomproxy as geo_proxy
        geo_proxy.dupliModGeomAsProxy(mod_grp=asb_topnode_ln, suffix="", flatten=False)
        # Rename proxy group
        cmds.rename(self.proxy_group, self.mdl_asset_group)

    def check_task_template(self):
        if not self.task_template_helper.is_assembly():
            error_log = 'This tool is not available for current task template: "{}"!'.format(self.task_template_name)
            logging.error(error_log)
            raise Exception(error_log)
    # -------------------------------------------------------------------------------------------------------------
    # IMPORT

    def create_assembly(self):
        """
        Create Assembly
        - Create hierarchy
        - Import asset bridge modeling as reference
        - Import subassets bridge from right context as reference
        """
        # Be sure we are in Assembly context
        # self.check_task_template() TODO uncomment this when TaskTemplateHelper will be ok
        # If yes, create assembly
        self.load_subassets_references()
        self.load_asset_reference()


    def load_reference(self, asset_name, task_name):
        """
        Import reference
        """
        logging.info('Looking for the latest "{}" scene of "{}"'.format(task_name, asset_name))
        sg_asset = self.shotgun_read_assets.get_asset_by_name(self.sg, asset_name, self.project_id, 'Asset')
        sg_bridge_task = self.shotgun_read_tasks.get_task_by_name(self.sg, task_name, self.sg_build_step, sg_asset)
        sg_latest_publish = self.shotgun_read_published_files.get_latest_publish_for_task(self.sg, sg_asset, sg_bridge_task)
        if sg_latest_publish:
            latest_publish_path = sg_latest_publish.get('path').get('local_path_windows')
            logging.info('Found: "{}'.format(latest_publish_path))
            publish_id = sg_latest_publish.get('id')
            publish_data = self.shotgun_read_published_files.get_published_data(self.sg, publish_id, self.project_id)
            logging.info('Publish data: {}'.format(publish_data))
            returned_nodes = self.execute_load_file('reference', publish_data, params={'use_namespace': True})
        else:
            logging.warning('No publish found for: "{}"'.format(asset_name))
            returned_nodes = None
        return returned_nodes

    def load_asset_reference(self):
        """
        - Load asset (elt or assembly) modeling bridge as reference
        - Create Proxy
        """
        mdl_topnode = '*:{}'.format(self.mdl_asset_group)
        if not cmds.objExists(mdl_topnode):
            returned_nodes = self.load_reference(self.asset_name, self.modeling_bridge_name)
            logging.info('Asset has been imported as reference.')
            if not returned_nodes:
                logging.error('Found no node in referenced scene!')
                return
        else:
            logging.info('Asset reference "{}" already exists.'.format(self.mdl_asset_group))

        # For rigging only
        if self.current_step == self.rigging_step_name:
            # Create proxy
            if cmds.objExists(self.mdl_asset_group):
                cmds.delete(self.mdl_asset_group)
            self.create_proxy()
            logging.info('Proxy group "{}" has been replaced.'.format(self.mdl_asset_group))
        # For rigging and shading
        if self.current_step == self.rigging_step_name or self.current_step == self.shading_step_name:
            # Create step top node when importing asb mdl
            if not cmds.objExists(self.step_asset_group):
                cmds.createNode('transform', n=self.step_asset_group)
            else:
                logging.info('Asset {} group already exists.'.format(self.current_step))

    def load_subassets_references(self):
        """
        - Load subassets from right context as reference
        - The result of this method depends on step
        """
        # Be sure we are in Assembly context
        # self.check_task_template() TODO uncomment this when TaskTemplateHelper will be ok
        # Get instance count for modeling step
        if self.current_step == self.modeling_step_name:
            subassets_list = []
            subassets_instance_count = self.shotgun_read_assets.get_instance_number(self.sg, self.asset_id)
            for sub_found in subassets_instance_count:
                if subassets_instance_count.get(sub_found) is None:
                    subassets_list.append(sub_found)
                while subassets_list.count(sub_found) < subassets_instance_count.get(sub_found):
                    subassets_list.append(sub_found)
        # We don't need instance count for other steps
        else:
            subassets_list = self.shotgun_read_assets.get_sub_assets_from_asset(self.sg, self.asset_id, 137)

        if subassets_list:
            # Create subassets groups
            self.create_sub_groups()
            # Import sub
            for subasset_name in subassets_list:
                logging.info('Looking for "{}" latest bridge scene.'.format(subasset_name))
                returned_nodes = self.load_reference(subasset_name, self.bridge_name)
                # Parent to Subassets groups
                if returned_nodes:
                    for node_found in returned_nodes:
                        if node_found.endswith('_Top'):
                            # If current step is Rigging
                            if self.current_step == self.rigging_step_name:
                                if 'RIG' in node_found:
                                    cmds.parent(node_found, self.rigging_step_name)
                                elif 'MDL' in node_found:
                                    cmds.parent(node_found, self.modeling_step_name)
                            # If current step is Shading
                            else:
                                cmds.parent(node_found, self.subassets_group)
                else:
                    logging.error('Found nothing to import!')
        else:
            logging.warning('Found no subassets for "{}"!'.format(self.asset_name))

    # -------------------------------------------------------------------------------------------------------------
    # AUTO

    def get_bridge_mdl_note(self):
        bridge_mdl_topnode_list = cmds.ls(self.bridge_mdl_topnode)
        print bridge_mdl_topnode_list
        if len(bridge_mdl_topnode_list) != 1:
            error_msg = 'Be sure you have at least and not more than one {} reference!'.format(self.modeling_bridge_name)
            logging.error(error_msg)
            raise Exception(error_msg)
        # Be sure note exists en bridge modeling
        bridge_mdl_topnode = bridge_mdl_topnode_list[0]
        bridge_mdl_note_attr = '{}.{}'.format(bridge_mdl_topnode, self.modeling_note)
        if not cmds.objExists(bridge_mdl_note_attr):
            log_error = 'Modeling note not found on "{}"!'.format(bridge_mdl_topnode)
            logging.error(log_error)
            raise Exception(log_error)
        bridge_mdl_note = ast.literal_eval(cmds.getAttr(bridge_mdl_note_attr))

        return bridge_mdl_note

    def auto_link_shaders(self, batch_mode=True):
        """
        Use modeling note and shading note to auto assign shading engine to bridge's transforms
        At the end, if not batch_mode, open a popup of all meshes without shading engine connections
        """
        # Be sure we are in Assembly context
        # self.check_task_template() TODO uncomment this when TaskTemplateHelper will be ok
        # Get bridge mdl note
        bridge_mdl_note = self.get_bridge_mdl_note()
        # Get all subs bridge shading topnode in scene
        bridge_sha_list = cmds.listRelatives(self.subassets_group)

        for bridge_sha in bridge_sha_list:
            logging.info('----------------------------------------')
            logging.info('----------------------------------------')
            # Be sure note exists en bridge shading
            bridge_sha_note_attr = '{}.{}'.format(bridge_sha, self.shading_note)
            if not cmds.objExists(bridge_sha_note_attr):
                logging.error('Shading note not found on "{}"!'.format(bridge_sha))
                continue
            bridge_sha_dict = ast.literal_eval(cmds.getAttr(bridge_sha_note_attr))
            # Be sure shad note is right
            if not bridge_sha_dict:
                logging.error('Cannot find shading note on: "{}"!'.format(bridge_sha))
                continue
            # Count iteration for logging
            i = 0
            how_many_sg = len(bridge_sha_dict)
            # If ok
            logging.info('Found shading note on "{}".'.format(bridge_sha))
            for shading_group_found in bridge_sha_dict:
                i = i + 1
                logging.info('----------------------------------------')
                logging.info('Shading group to apply {}/{}: {}'.format(i, how_many_sg, shading_group_found))
                # Get transforms values from shading group in dict
                shading_group_infos = bridge_sha_dict.get(shading_group_found)
                old_names_from_sha = shading_group_infos.get('transforms_names')
                if not old_names_from_sha:
                    logging.error('Cannot find transforms longnames for "{}" in shading note!'.format(shading_group_found))
                    continue
                shaders_from_sha = shading_group_infos.get('shaders')
                if not old_names_from_sha:
                    logging.error('Cannot find shaders for "{}" in shading note!'.format(shaders_from_sha))
                    continue
                # For transform found in shading note
                for transform_found in old_names_from_sha:
                    logging.info('Found transform in shading note: {}'.format(transform_found))
                    # Be sure transform is well named
                    right_topnode_end = '_{}_{}'.format(self.mdl_step_sn, self.topnode_suffixe)
                    if right_topnode_end not in transform_found:
                        logging.error('Transform is not named properly: "{}"!'.format(transform_found))
                        logging.error('Topdnode should end with: "{}"!'.format(right_topnode_end))
                        continue
                    # Get asset name from transform name
                    asset_name = transform_found.split('|')[1].split('_{}'.format(self.mdl_step_sn))[0]
                    # Then looking for instance name of each sub in mdl note
                    for sub, values in bridge_mdl_note.items():
                        for instance_value in values:
                            if sub == asset_name:
                                old_name_from_mdl = '|{}'.format(instance_value.get('old_name'))
                                new_name_from_mdl = instance_value.get('new_name')
                                new_name_with_no_ns = transform_found.replace(old_name_from_mdl, new_name_from_mdl)
                                modeling_bridge_ns = cmds.ls(self.bridge_mdl_topnode)[0].split(':')[0]
                                new_name_with_ns = new_name_with_no_ns.replace('|', '|{}:'.format(modeling_bridge_ns))
                                if cmds.objExists(new_name_with_ns):
                                    logging.info('Found relation between sha note: "{}"'.format(transform_found))
                                    logging.info('and current assembly bridge: "{}".'.format(new_name_with_ns))
                                else:
                                    logging.error('Found no relation between sha note "{}" and assembly bridge!'.format(transform_found))
                                    continue
                                # Apply shading group to transform
                                shading_group_list = cmds.ls(shading_group_found, r=True)
                                if len(shading_group_list) > 1:
                                    logging.warning('Found more than one shading group with same name: {}'.format(shading_group_list))
                                bridge_sha_ns = bridge_sha.split(':')[0]
                                shading_group_to_assign = None
                                for shading_group in shading_group_list:
                                    if bridge_sha_ns in shading_group:
                                        shading_group_to_assign = shading_group
                                        continue
                                if shading_group_to_assign is None:
                                    logging.error('Found no shading group to assign for "{}"!'.format(sub))
                                    continue

                                logging.info('Shading group to assign: "{}"'.format(shading_group_to_assign))
                                try:
                                    cmds.sets(new_name_with_ns, add=shading_group_to_assign)
                                except Exception as e:
                                    logging.error('An error as occurred: {}'.format(e))
                                logging.info('Shading group has been assign to: "{}"'.format(new_name_with_ns))
                                continue

        # Check if everything is okay
        transforms_list = read_nodes.non_default_nodes_only(cmds.ls('{}_*:*_{}'.format(self.modeling_bridge_name, self.mesh_suffixe), type='transform', l=True))
        self.check_assignation(transforms_list, batch_mode=batch_mode)

    def check_assignation(self, transforms_list, batch_mode=True):
        """
        Check if transforms are linked to a shading group
        TODO Extract to lib
        """
        logging.info('----------------------------------------')
        transform_with_no_sg = []
        for transform_found in transforms_list:
            rel = cmds.listRelatives(transform_found, f=True)
            if not cmds.ls(cmds.listConnections(rel), type='shadingEngine'):
                transform_with_no_sg.append(transform_found)
        if transform_with_no_sg:
            how_many_went_wrong = len(transform_with_no_sg)
            # Log errors
            log_string = 'Something went wrong during auto assignation for {} transform(s):\n{}       '.format(how_many_went_wrong, transform_with_no_sg)
            if batch_mode is False:
                cmds.confirmDialog(title='Assignation errors', message=log_string)
            logging.error(log_string)
        return transform_with_no_sg

    def auto_placement(self):
        """
        Auto placement of Subassets
        Use Modeling note of the Assembly BridgeModelingPreRig
        TODO: need it in master scene, with JSON
        TODO: if no bridge modeling, check JSON
        """
        logging.info('----------------------------------------')
        # Be sure we are in Assembly context
        # self.check_task_template() TODO uncomment this when TaskTemplateHelper will be ok
        # Get bridge mdl note
        bridge_mdl_note = self.get_bridge_mdl_note()
        # Get all subs bridge modeling topnode in scene
        sub_bridge_mdl_list = cmds.listRelatives(self.subassets_group)
        # Use for instance counted subassets
        already_done_sub = []
        # Set placement of each sub
        for sub_bridge in sub_bridge_mdl_list:
            logging.info('Looking for transforms of: "{}"'.format(sub_bridge))
            subasset_name = sub_bridge.split('_{}'.format(self.mdl_step_sn))[0].split(':')[1]
            already_done_sub.append(subasset_name)
            # If instance counted asset, look for the next data in sub_dict sub list
            which_in_list = already_done_sub.count(subasset_name) - 1
            sub_dict = bridge_mdl_note.get(subasset_name)[which_in_list]
            sub_transforms = sub_dict.get('transform')
            logging.info('Found transforms: "{}"'.format(sub_transforms))
            for sub_transform in sub_transforms:
                cmds.setAttr('{}.{}'.format(sub_bridge, sub_transform), sub_transforms.get(sub_transform))

    def clean_asset_scene(self):
        if self.task_template_helper.is_assembly():
            logging.warning('This tool is available for Assembly scene only.')
            return
        # Get reference bridge list
        reference_list = cmds.ls('{}*'.format(self.bridge_name), type='reference')
        # Clean ASB rigging scene
        if self.current_step == self.rigging_step_name:
            for sub_ref in reference_list:
                ref_file = cmds.referenceQuery(sub_ref, f=True)
                cmds.file(ref_file, rr=True)
            cmds.delete(self.subassets_group)
        # Clean ASB modeling scene
        elif self.current_step == self.modeling_step_name:
            for sub_ref in reference_list:
                ref_file = os.path.normpath(cmds.referenceQuery(sub_ref, f=True))
                path_parts = ref_file.split(os.sep)
                if path_parts:
                    asset_name = path_parts[7]
                    if asset_name == self.asset_name:
                        cmds.file(ref_file, rr=True)
        logging.info('Scene has been cleaned.')


if __name__ == "__main__":
    logging.warning('You must use a method of the class "UpdateAssetScene"!')

# import millimages.maya.tools.PirataEtCapitano.common.update_asset_step as uas
# reload(uas)
# uas.UpdateAssetScene().auto_link_shaders()
