# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#
#   DESCRIPTION :       This tool is used to update BKL from asset library Masterscene
#   DOC :               https://hackmd.io/PznYjv9ZQNqTQznznvbwMA
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         Not used, probably need fixes
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

try:
    import maya.cmds as cmds
    import sgtk
except ImportError:
    pass

from . import update_assetLibrary_master as update_master


# TODO: Clean hardcoded stuff around task template / use TaskTemplateHelper
class UpdateMasterSceneBKL(update_master.UpdateMasterScene):
    """
    OBSOLETE SCRIPT
    This class been created to update Shotgun BKL
    - It will compare Shotgun BKL to scene sets
    - Open a window to tell you what you can change on Shotgun
    - You can accept/reject updates by checking boxes or not
    - Create new variations or subassets if needed
    - Create their filesystem folders
    - Update assetLibrary and their variations BKL
    - Script will ignore obsolete sets and variation sets without subs
    - This tool only create ASSEMBLY variation, no ELT Default
    """

    def __init__(self):
        super(UpdateMasterSceneBKL, self).__init__()
        # Get the engine instance that is currently running.
        current_engine = sgtk.platform.current_engine()
        # Set vars
        self.assembly_template_id = 118
        self.elt_default_template_id = 97
        self.add_sub_bkl_dict = {}
        self.remove_sub_bkl_dict = {}
        self.add_variation_to_breadown = []
        self.remove_variation_from_breakdown = []
        self.checkbox_content = []
        self.update_bkl_command = []
        self.var_to_add = []
        self.var_to_rmv = []
        self.sub_to_add = {}
        self.sub_to_rmv = {}
        self.add_var_in_scene = {}
        self.rmv_var_from_scene = {}
        self.var_to_edit_dict = {}
        # Import module from tk-framework-shotgun
        fw_shotgun = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-shotgun')
        self.shotgun_read_assets = fw_shotgun.import_module('studio.libs.reads.assets')
        self.shotgun_read_asset_libraries = fw_shotgun.import_module('studio.libs.reads.asset_libraries')
        self.shotgun_create_assets = fw_shotgun.import_module('studio.libs.creates.assets')
        self.shotgun_update_common = fw_shotgun.import_module('studio.libs.updates.common')

    def launch_update_bkl(self):
        """
        AssetLib BKL Updater launcher
        - Get difference between assteLib and variations Shotgun BKL and scene sets
        - Launch UI if yes
        """
        edit_bkl = self.detect_bkl_difference()
        if edit_bkl is True:
            self.update_bkl_UI()

    def get_asset_from_scene(self):
        """
        TODO: there's something similar in split_master_scene.py
        :return: a dict {variation : [sub1, sub2]}
        :rtype: dict
        """
        variation_pattern = '{}_*_{}'.format(self.assetlib_name, self.set_suffixe)
        variation_sets_list = cmds.ls(variation_pattern, l=True, set=True)
        sets_dict = {}
        for variation_set_found in variation_sets_list:
            sub_sets_list = []
            variation_name = variation_set_found.split('_{}'.format(self.step_name))[0]
            self.extra_logging.info('Variation set found: "{}"'.format(variation_set_found))
            variation_set_content = cmds.ls(cmds.sets(variation_set_found, q=True), set=True)
            if variation_set_content:
                for sub_set_found in variation_set_content:
                    if sub_set_found.endswith('_{}'.format(self.set_suffixe)):
                        self.extra_logging.info('   > Subasset set found: "{}"'.format(sub_set_found))
                        sub_name = sub_set_found.split('_{}'.format(self.step_name))[0]
                        sub_sets_list.append(sub_name)
            sets_dict[variation_name] = sub_sets_list
        return sets_dict

    def detect_bkl_difference(self):
        """
        Compare AssetLib and variations Shotgun BKL to scene sets
        Put difference in 2 dict: self.add_sub_bkl_dict and self.remove_sub_bkl_dict
        :return: True if there's at least one difference / False if nothing has changed
        """
        edit_bkl = False
        sorted_shotgun_key = sorted(list(dict.fromkeys(self.shotgun_assets)))
        scene_assets = self.get_asset_from_scene()
        sorted_scene_key = sorted(list(dict.fromkeys(scene_assets)))
        self.extra_logging.info('----------------------------------------------------------------------------')
        self.extra_logging.info('Looking for all added and removed assets in your scene by comparing scene sets and shotgun BKL:')
        # Add / remove variation to bkl
        self.add_variation_to_breadown = [value for value in sorted_scene_key if value not in sorted_shotgun_key]
        self.remove_variation_from_breakdown = [value for value in sorted_shotgun_key if value not in sorted_scene_key]
        if self.add_variation_to_breadown:
            self.extra_logging.warning('"{}": "{}" has been added to scene.'.format(self.assetlib_name, self.add_variation_to_breadown))
            edit_bkl = True
        else:
            self.extra_logging.info('"{}": No variation has been added to scene.'.format(self.assetlib_name))
        if self.remove_variation_from_breakdown:
            self.extra_logging.warning('"{}": "{}" has been removed from scene.'.format(self.assetlib_name, self.remove_variation_from_breakdown))
            edit_bkl = True
        else:
            self.extra_logging.info('"{}": No variation has been removed from scene.'.format(self.assetlib_name))
        # Add / remove sub from bkl
        for variation_found in sorted_scene_key:
            add_sub_to_breadown = []
            remove_sub_from_breakdown = []
            sub_list = scene_assets.get(variation_found)
            if sub_list and sub_list is not None:  # if not [] and not None
                scene_sub = scene_assets.get(variation_found)
                shotgun_sub = self.shotgun_assets.get(variation_found)
                # If variation has sub in scene and shotgun
                if scene_sub is not None and shotgun_sub is not None:
                    add_sub_to_breadown = [add_sub_name for add_sub_name in scene_sub if add_sub_name not in shotgun_sub]
                    remove_sub_from_breakdown = [rem_sub_name for rem_sub_name in shotgun_sub if rem_sub_name not in scene_sub]
                # If variation has sub in shotgun but not in scene
                elif scene_sub is not None and shotgun_sub is None:
                    for sub in scene_sub:
                        add_sub_to_breadown.append(sub)
                # If variation has sub in scene but not in shotgun
                elif scene_sub is None and shotgun_sub is not None:
                    for sub in shotgun_sub:
                        remove_sub_from_breakdown.append(sub)
                # If difference found between scene and shotgun, store diff in lists
                if add_sub_to_breadown:
                    self.extra_logging.warning('"{}": "{}" has been added to scene.'.format(variation_found, add_sub_to_breadown))
                    self.add_sub_bkl_dict[variation_found] = add_sub_to_breadown
                    edit_bkl = True
                else:
                    self.extra_logging.info('"{}": No sub has been added to scene.'.format(variation_found))
                if remove_sub_from_breakdown:
                    self.extra_logging.warning('"{}": "{}" has been removed from scene.'.format(variation_found, remove_sub_from_breakdown))
                    self.remove_sub_bkl_dict[variation_found] = remove_sub_from_breakdown
                    edit_bkl = True
                else:
                    self.extra_logging.info('"{}": No sub has been removed from scene.'.format(variation_found))
            else:
                # If var has no sub: check for task template attr, it should be a self.elt_default_template
                attr = '{}_{}_{}.{}'.format(variation_found, self.step_name, self.set_suffixe, self.task_template_attr)
                if cmds.objExists(attr):
                    if cmds.getAttr(attr) == self.elt_default_template:
                        self.extra_logging.info('Variation set "{}" has no sub because of its task template: "{}".'.format(variation_found, self.elt_default_template))
                    else:
                        self.extra_logging.error('Variation set "{}" should have sub because of its task template!'.format(variation_found))
                else:
                    self.extra_logging.error('Cannot find Task Template extra attribute for "{}" set!.'.format(variation_found))
        if edit_bkl is False:
            self.extra_logging.info('Found no difference between Shotgun BKL and Master scene.')
        return edit_bkl

    def update_bkl_UI(self):
        """
        AssetLib BKL Updater UI
        """
        # Create window and close existing ones
        update_window = "updateAssetLibraryBKL"
        if cmds.window(update_window, q=1, exists=True):
            cmds.deleteUI(update_window)
        window = cmds.window(update_window, title='Update BKL from {}'.format(self.assetlib_name))
        cmds.columnLayout(adjustableColumn=True)
        # Add variation checkox
        if self.add_variation_to_breadown:
            cmds.text(label='Add variation(s) from "{}"'.format(self.assetlib_name), align='left')
            for element_to_add in self.add_variation_to_breadown:
                checkbox_name = '{}_{}_add'.format(self.assetlib_name, element_to_add)
                self.checkbox_content.append(checkbox_name)
                cmds.checkBox(checkbox_name, label='Add "{}" to "{}" BKL'.format(element_to_add, self.assetlib_name), v=False)
            cmds.separator(height=10, style="none")
        # Remove variation checkox
        if self.remove_variation_from_breakdown:
            cmds.text(label='Remove variation(s) from "{}"'.format(self.assetlib_name), align='left')
            for element_to_rem in self.remove_variation_from_breakdown:
                checkbox_name = '{}_{}_rmv'.format(self.assetlib_name, element_to_rem)
                self.checkbox_content.append(checkbox_name)
                cmds.checkBox(checkbox_name, label='Remove "{}" from "{}" BKL'.format(element_to_rem, self.assetlib_name), v=False)
            cmds.separator(height=10, style="none")
        # Add sub checkox
        for variation_found in self.add_sub_bkl_dict:
            cmds.text(label='Add sub(s) to "{}"'.format(variation_found), align='left')
            for sub_to_add in self.add_sub_bkl_dict.get(variation_found):
                checkbox_name = '{}_{}_add'.format(variation_found, sub_to_add)
                self.checkbox_content.append(checkbox_name)
                cmds.checkBox(checkbox_name, label='Add "{}" to "{}" BKL'.format(sub_to_add, variation_found), v=False)
        cmds.separator(height=10, style="none")
        # Remove sub checkox
        for variation_found in self.remove_sub_bkl_dict:
            cmds.text(label='Remove sub(s) from "{}"'.format(variation_found), align='left')
            for sub_to_rem in self.remove_sub_bkl_dict.get(variation_found):
                checkbox_name = '{}_{}_rmv'.format(variation_found, sub_to_rem)
                self.checkbox_content.append(checkbox_name)
                cmds.checkBox(checkbox_name, label='Remove "{}" from "{}" BKL'.format(sub_to_rem, variation_found), v=False)
        # Get check and uncheck box info
        cmds.button(label='OK', command=lambda x: self.are_you_sure())
        cmds.setParent('..')
        cmds.showWindow(window)

    def get_checkbox_value(self, checkbox_name):
        return cmds.checkBox(checkbox_name, q=True, v=True)

    def are_you_sure(self):
        i_am_sure = cmds.confirmDialog(title='Confirm', message='Are you sure you want to update BKL?       ', button=['Yes', 'Abort'], defaultButton='Yes', cancelButton='No', dismissString='No')
        if i_am_sure == 'Yes':
            self.launch_ok()
        else:
            self.extra_logging.warning('Process aborted by user.')

    def launch_ok(self):
        """
        Get checbkoxes values and launch update
        """
        self.extra_logging.info('----------------------------------------------------------------------------')
        self.extra_logging.info('Shotgun update:')
        # Get checkbox values
        for checkbox_name in self.checkbox_content:
            checkbox_value = self.get_checkbox_value(checkbox_name)
            # Store informations in lists/dicts
            if checkbox_value is True:
                checkbox_name_parts = checkbox_name.split('_')
                if checkbox_name_parts[1] == self.assetlib_name:
                    var_name = '{}_{}'.format(checkbox_name_parts[1], checkbox_name_parts[2])
                    # Add var to bkl
                    if checkbox_name_parts[-1] == 'add':
                        self.extra_logging.info('Add "{}" to "{}" BKL'.format(var_name, self.assetlib_name))
                        self.var_to_add.append(var_name)
                    # Remove var from bkl
                    elif checkbox_name_parts[-1] == 'rmv':
                        self.extra_logging.info('Remove "{}" from "{}" BKL'.format(var_name, self.assetlib_name))
                        self.var_to_rmv.append(var_name)
                else:
                    var_name = '{}_{}'.format(checkbox_name_parts[0], checkbox_name_parts[1])
                    sub_name = '{}_{}'.format(checkbox_name_parts[2], checkbox_name_parts[3])
                    # Add sub to bkl
                    if checkbox_name_parts[-1] == 'add':
                        self.extra_logging.info('Add "{}" to "{}" BKL'.format(sub_name, var_name))
                        if not self.sub_to_add:
                            self.sub_to_add[var_name] = [sub_name]
                        else:
                            sub_list = self.sub_to_add.get(var_name)
                            if sub_name not in sub_list:
                                sub_list.append(sub_name)
                            self.sub_to_add.update({var_name: sub_list})
                    # Remove sub from bkl
                    elif checkbox_name_parts[-1] == 'rmv':
                        self.extra_logging.info('Remove "{}" from "{}" BKL'.format(sub_name, var_name))
                        if not self.sub_to_rmv:
                            self.sub_to_rmv[var_name] = [sub_name]
                        else:
                            sub_list = self.sub_to_rmv.get(var_name)
                            if sub_name in sub_list:
                                sub_list.append(sub_name)
                            self.sub_to_rmv.update({var_name: sub_list})
        # Update bkl
        if self.var_to_add or self.var_to_rmv:
            self.update_assetlib_bkl()
        if self.sub_to_add or self.sub_to_rmv:
            self.update_var_bkl(self.get_new_var_data())

    def create_shotgun_asset(self, asset, task_template_id, assetlibrary_id, entity_type):
        """
        Create a Shotgun asset + filesystem
        :return: data dict
        """
        # create_asset_lib(tk, shotgun_api, project_id, task_template_id, entity_name):
        self.shotgun_create_assets.create_entity(self.tk, self.sg, self.project_id, 'Asset', task_template_id, asset, assetlibrary_id)  # assetlibrary_id != self.assetlib_id
        self.extra_logging.info('Shotgun asset has been created: "{}"'.format(asset))
        return self.shotgun_read_assets.get_asset_by_name(self.sg, asset, self.project_id, entity_type)

    def code_to_name(self, data):
        """
        Get 'code' as asset name when querying
        Need 'name' as asset name when creating/updating
        :return: same data dict with 'name' key instead of 'code'
        """
        data['name'] = data.pop('code')
        return data

    def update_assetlib_bkl(self):
        """
        Do Shotgun assetLib data update
        Create Shotgun variation + filesystem if needed
        """
        # Get var from assetlib
        sg_assetlib_bkl = []
        sg_assetlib_bkl_tmp = self.shotgun_read_asset_libraries.get_assets_from_assetslib_name(self.sg, self.assetlib_name, self.project_id)
        # TODO: Needed??
        self.update_variations_task_template(sg_assetlib_bkl_tmp)

        # Replace 'code' key by 'name'
        for var_dict in sg_assetlib_bkl_tmp:
            var_dict = self.code_to_name(var_dict)
            sg_assetlib_bkl.append(var_dict)
        # Remove variation from assetlib
        for variation in self.var_to_rmv:
            for var_dict in list(sg_assetlib_bkl):
                # 'code' key has been changed for 'name' key
                if variation == var_dict.get('name'):
                    sg_assetlib_bkl.remove(var_dict)
                    self.rmv_var_from_scene.update({variation: []})
                    continue
        # Add variation to assetlib
        for variation in self.var_to_add:
            var_data = self.shotgun_read_assets.get_asset_by_name(self.sg, variation, self.project_id, 'Asset')
            # Create shotgun variation if it does not exist
            if not var_data:
                var_data = self.create_shotgun_asset(variation, self.assembly_template_id, self.assetlib_id, 'AssetLibrary')
            # Replace 'code' key by 'name'
            var_data = self.code_to_name(var_data)
            # Now we are sure that variation exists in Shotgun
            self.extra_logging.info('Add "{}" to "{}" BKL'.format(variation, self.assetlib_name))
            sg_assetlib_bkl.append(var_data)
            # Prepare new var for sub update if needed
            self.add_var_in_scene.update({variation: []})
        # Update Add/Remove AssetLibrary
        data = {'sg_assets': sg_assetlib_bkl}
        self.shotgun_update_common.update_entity(self.sg, 'AssetLibrary', self.assetlib_id, data)
        self.extra_logging.info('BKL has been updated "{}": {}'.format(self.assetlib_name, data))

    def get_new_var_data(self):
        """
        Get variation data and put them in a list of dict
        [{var1: [sub1, sub2]}, {var2: [sub2, sub3, sub4]}]
        Create Shotgun subassets + filesystem if nedeed
        :return: a list of dict
        """
        # Create variation data
        sg_var_bkl_list = []
        if self.add_var_in_scene:
            self.shotgun_assets.update(self.add_var_in_scene)
        if self.rmv_var_from_scene:
            for var in self.rmv_var_from_scene:
                self.shotgun_assets.pop(var)
        for var in self.shotgun_assets:
            sub_list = []
            sg_sub_list = self.shotgun_assets.get(var)
            for sg_sub in sg_sub_list:
                sub_data = self.shotgun_read_assets.get_asset_by_name(self.sg, sg_sub, self.project_id, 'Asset')
                # Replace 'code' key by 'name'
                sub_data = self.code_to_name(sub_data)
                sub_list.append(sub_data)
            sg_var_bkl_list.append({var: sub_list})

        # Get all var data to edit
        if self.sub_to_add:
            self.var_to_edit_dict.update(self.sub_to_add)
        if self.sub_to_rmv:
            self.var_to_edit_dict.update(self.sub_to_rmv)

        # Remove sub from variation data
        for var in self.sub_to_rmv:
            sub_to_rmv_list = self.sub_to_rmv.get(var)
            for var_dict in list(sg_var_bkl_list):
                field, sub_data = var_dict.items()[0]
                if var == field:
                    # Remove var from dict
                    sg_var_bkl_list.remove(var_dict)
                    for sub in list(sub_data):
                        # Get 'name' instead of 'code' because we have replaced it
                        if sub.get('name') in sub_to_rmv_list:
                            # Remove sub from var
                            sub_data.remove(sub)
                            data = {var: sub_data}
                            # Add new var data
                            sg_var_bkl_list.append(data)

        # Add sub to variation data
        for var in self.sub_to_add:
            sub_to_add_list = self.sub_to_add.get(var)
            # Remove var from dict and store data
            for var_dict in list(sg_var_bkl_list):
                field, sub_list = var_dict.items()[0]
                if var == field:
                    # Remove var from dict
                    sub_data = var_dict.get(var)
                    sg_var_bkl_list.remove(var_dict)
                    # Get new data
                    for sub in sub_to_add_list:
                        new_sub_data = self.shotgun_read_assets.get_asset_by_name(self.sg, sub, self.project_id, 'Asset')
                        # Create shotgun sub if it does not exist
                        if not new_sub_data:
                            assetlibrary_name = sub.split('_')[0]
                            assetlibrary = self.shotgun_read_assets.get_asset_by_name(self.sg, assetlibrary_name, self.project_id, 'AssetLibrary')
                            assetlibrary_id = assetlibrary.get('id')
                            new_sub_data = self.create_shotgun_asset(sub, self.elt_default_template_id, assetlibrary_id, 'Asset')
                        # Replace 'code' key by 'name'
                        new_sub_data = self.code_to_name(new_sub_data)
                        # Now we are sure that sub exists in Shotgun
                        sub_data.append(new_sub_data)
                        data = {var: sub_data}
                        sg_var_bkl_list.append(data)
        return sg_var_bkl_list

    def update_var_bkl(self, sg_var_bkl_list):
        """
        Do Shotgun variation data update
        """
        for var in self.var_to_edit_dict:
            for element in sg_var_bkl_list:
                element_field, element_value = element.items()[0]
                if element_field == var:
                    value = element_value
                    continue
            update_data = {'assets': value}
            var_id = self.shotgun_read_assets.get_asset_by_name(self.sg, var, self.project_id, 'Asset').get('id')
            self.shotgun_update_common.update_entity(self.sg, 'Asset', var_id, update_data)
            self.extra_logging.info('BKL has been updated "{}": {}'.format(var, update_data))


if __name__ == "__main__":
    UpdateMasterSceneBKL().launch_update_bkl()
