# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       Modeling checker tool to help clean modeling master scenes.
#                       help : https://hackmd.io/CyC_faH1S0W3PgL0qg0vGg?view
#
#   Creation :          24/04/2020.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging

try:
    import maya.cmds as cmds
    import sgtk
except ImportError:
    pass

from . import mdl_checker
from ....studio.libs.reads import nodes as read_nodes
from ....studio.libs.reads import references as read_references


class ModelingCheckerMaster(object):
    """
    Modeling checker master tool.
    Check and correct:
    - Scene setup and content.``
    - Top node number, nomenclature, position and values.
    - Groups values, nomenclature, visibility.
    - Mesh values, nomenclature, visibility, integrity.

    The redshift's attributes on nodes is not corrected..
    The polygons' integrity is not modified.
    """
    def __init__(self, logger=logging):
        current_engine = sgtk.platform.current_engine()
        current_context = sgtk.platform.current_engine().context
        self.sg = current_engine.shotgun
        self.assetlib_name = current_context.entity['name']
        self.task_name = current_context.task['name']
        self.assetID = current_context.task['id']
        # Import module from tk-framework-shotgun
        fw_shotgun = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-shotgun')
        self.shotgun_read_steps = fw_shotgun.import_module('studio.libs.reads.steps')
        self.shotgun_read_assets = fw_shotgun.import_module('studio.libs.reads.assets')
        # Import module from tk-framework-common
        fw_common = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-common')
        self.update_dicts = fw_common.import_module("studio.libs.dicts.updates")
        self.step_name = self.shotgun_read_steps.get_step_short_name(self.sg, current_context.step['name'])
        self.logger = logger
        # Get variations lists but exclusion of SHA VARIATION template ID
        self.variationsList = self.shotgun_read_assets.get_variation_list(shotgun_api=self.sg, project_id=137, asset_name=self.assetlib_name, substractSub=False, excludeTaskTemplateId=115)
        self.logger.info('Variations list {} '.format(self.variationsList))

        self.mdl_check = mdl_checker.ModelingChecker()
        self.sanity_check = mdl_checker.ModelingChecker().sanity_check
        self.check_all = self.sanity_check.check_all

        self.refresh_lists()
        self.buttonLst = self.mdl_check.buttonLst
        self.ordreButtonLst = self.mdl_check.ordreButtonLst

        self.mdl_check.master = True
        self.ui = self.mdl_check.ui

        # removing useless buttons for master and creating overrides
        self.ui.editButtons('__ALL FUNCTIONS__', 'Run All Functions')
        self.ui.editButtons('__ALL FUNCTIONS__', 'Run All Functions', [self.run_all_funct, None], 0)
        self.ui.editButtons('__SCENE__', 'Selection sets')
        self.ui.editButtons('__SCENE__', 'References')
        self.ui.editButtons('__SCENE__', 'Namespaces')
        self.ui.editButtons('__GROUPS__', 'Subassets', [self.run_subasset_nom_ui, None], 0)
        self.ui.editButtons('__GROUPS__', 'Grp nomenclature')
        self.ui.editButtons('__GROUPS__', 'Grp nomenclature', [self.run_grp_nom_ui, self.fix_grps_nom_ui], 0)

    def launch(self):
        self.ui.launchUI()
        # self.run_all_funct()

    def run_subasset_nom_ui(self):
        """"
        Check subasset grp nomenclature:
        -Checking prefix
        -Checking suffix
        """
        self.refresh_lists()
        if self.sanity_check._valid_subasset_nom():
            self.ui.changeColorStat('Subassets', 'green', True)
        else:
            self.ui.changeColorStat('Subassets', 'red', True)

    def run_grp_nom_ui(self):
        """"
        Check group nomenclature:
        -Checking prefix
        -Checking suffix (with padding)
        """
        self.refresh_lists()
        self.badGrpNom = self.sanity_check._valid_grps_nom(customGrpList=self.all_groups)

        if not self.badGrpNom:
            self.ui.changeColorStat('Grp nomenclature', 'green', True)
        else:
            self.ui.changeColorStat('Grp nomenclature', 'red', True)

    def fix_grps_nom_ui(self):
        """
        Correcting nomenclature
        Checking grp prefix (from its children)
        And correct if
        """
        # self.sanity_check.all_groups = self.all_groups
        self.sanity_check._fix_grps_nom(customList=self.badGrpNom)
        self.run_grp_nom_ui()

    def refresh_lists(self):
        """
        Fills list of items in scene
        """
        self.all_meshes = read_nodes.list_all_meshes()
        self.all_groups = read_nodes.list_all_groups()
        self.top_node = read_nodes.get_top_node()
        self.defaults_grp = ["Elt_Default_Grp", "Common_Grp", "Assemblies_Grp", "Trash_Grp"]
        self.defaults_grp = [cmds.ls(grp, long=True)[0] for grp in self.defaults_grp if cmds.objExists(grp)]
        self.subassets = [elmt for elmt in cmds.listRelatives("Elt_Default_Grp", fullPath=True) if cmds.objExists("Elt_Default_Grp")]
        self.variationsDict = self.shotgun_read_assets.get_variation_list(shotgun_api=self.sg, project_id=137, asset_name=self.assetlib_name, substractSub=False, excludeTaskTemplateId=115)
        self.variationsList = self.update_dicts.convert_dict_to_flat_list(dictionary=self.variationsDict)

        self.variations = []
        # adding nomenclature of scene inside the supposed variation list
        for var in self.variationsList:
            mdlName = var + "_MDL_Top"
            longName = cmds.ls(mdlName, long=True)
            self.variations += longName

        self.variations = list(set(self.variations))

        self.all_groups = []
        for grp in read_nodes.list_all_groups():
            if (
                grp not in self.variations
                and grp not in self.defaults_grp
                and grp not in self.subassets
                and read_references.is_reference(grp) is False
            ):
                self.all_groups.append(grp)


    def run_all_funct(self):
        """
        Run all functions together
        """
        self.logger.info('*' * 10 + 'START OF SANITY CHECK MASTER' + "*" * 10)
        self.refresh_lists()
        self.mdl_check.run_check_time_unit_ui()
        self.mdl_check.run_frame_range_ui()
        self.mdl_check.run_rs_load_ui()
        self.mdl_check.run_unauthorized_ui()
        self.mdl_check.run_unknown_nodes_ui()
        self.mdl_check.run_dispay_layers_ui()
        self.mdl_check.run_mtl_ui()
        self.mdl_check.run_non_default_cam_ui()

        if self.mdl_check.check_scene_elmt():
            if self.mdl_check.run_many_top_node_ui():
                self.mdl_check.run_tn_name_ui()
                self.mdl_check.run_tn_piv_ui()
                self.mdl_check.run_tn_ft_ui()
                self.run_subasset_nom_ui()
            self.run_grp_nom_ui()
            self.mdl_check.run_grps_ft_ui()
            self.mdl_check.run_grp_visib_ui()
            self.mdl_check.run_mesh_nom_ui()
            self.mdl_check.run_mesh_shape_nom_ui()
            self.mdl_check.run_mesh_ft_ui()
            self.mdl_check.run_mesh_history_ui()
            self.mdl_check.run_mesh_double_shape_ui()
            self.mdl_check.run_mesh_visibility_ui()
            self.mdl_check.run_mesh_renderStats_ui()
            self.mdl_check.run_mesh_instance_ui()
            self.mdl_check.run_mesh_cleanup_ui()
            self.mdl_check.run_mesh_polyColor_ui()
            self.mdl_check.run_mesh_ngones_ui()
            self.mdl_check.run_mesh_geo_issues_ui()

        if self.sanity_check.check_all is True:
            self.logger.info("....SCENE READY TO BE PUBLISHED ....!")

        else:
            self.logger.info("....SCENE MASTER IS NOT CLEAN ! See log for details ....!")

        self.logger.info('*' * 10 + 'END OF SANITY CHECK' + "*" * 10)
