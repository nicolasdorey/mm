# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       Modeling checker tool to help clean modeling scenes.
#   DOC :               https://hackmd.io/CyC_faH1S0W3PgL0qg0vGg?view
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

from ....studio.libs.reads import nodes as read_nodes

# FIXME IMPORT THEM WHEN MOVED OR FROM TK-MULTI-SANITYCHECK
from ...Common.common.sanity_checks import sanity_check
from ..common import checker_UI


class ModelingChecker(checker_UI.ModelingCheckerUI):
    """Modeling checker tool.
    Check and correct:
    - Scene setup and content.
    - Top node number, nomenclature, position and values.
    - Groups values, nomenclature, visibility.
    - Mesh values, nomenclature, visibility, integrity.

    The redshift's attributes on nodes is not corrected..
    The polygons' integrity is not modified.
    """

    def __init__(self):
        """
        Init scene, list of meshes
        """
        current_engine = sgtk.platform.current_engine()
        current_context = sgtk.platform.current_engine().context
        self.sg = current_engine.shotgun
        self.assetlib_name = current_context.entity['name']
        self.task_name = current_context.task['name']
        self.master = False

        self.sanity_check = sanity_check.SanityCheck()

        self.check_all = self.sanity_check.check_all
        # dictionary list of all buttons :
        # [{'__SCENE__' : {button1 : [f1, f2]}, ...}, ...]
        self.buttonLst = []

        # order button dictionaries list :
        # [{'__SCENE__' : [button1, button2, ...] }, ...]
        self.ordreButtonLst = []
        self.createButtons()

        self.refresh_lists()

        url = 'https://hackmd.io/CyC_faH1S0W3PgL0qg0vGg?view'
        self.ui = checker_UI.ModelingCheckerUI(self, url)

    def launch(self):
        self.ui.launchUI()
        # self.run_all_funct()

    def createButtons(self):
        """
        Create all buttons filled with the datas
        """
        # ################ SCENE ################
        category = "__ALL FUNCTIONS__"
        # dict to store ordoned list
        ordreButtonLst = {
            category: [
                "Run All Functions",
            ]
        }

        # dict of functions datas
        allDataButtons = {
            category: {
                ordreButtonLst[category][0]: [self.run_all_funct, None],
            }
        }

        self.buttonLst.append(allDataButtons)
        self.ordreButtonLst.append(ordreButtonLst)

        # ################ SCENE ################
        category = "__SCENE__"
        # dict to store ordoned list
        ordreButtonLst = {
            category: [
                "Redshift load",
                "Time unit",
                "Frame range",
                "Selection sets",
                "Authorized nodes",
                "Unknown nodes",
                "Display layers",
                "Non default mtl",
                "References",
                "Namespaces",
                "Non default cam"
            ]
        }

        # dict of functions datas
        allDataButtons = {
            category: {
                ordreButtonLst[category][0]: [self.run_rs_load_ui, self.fix_rs_load_ui],
                ordreButtonLst[category][1]: [self.run_check_time_unit_ui, self.fix_time_unit_ui],
                ordreButtonLst[category][2]: [self.run_frame_range_ui, self.fix_frame_range_ui],
                ordreButtonLst[category][3]: [self.run_ss_sets_ui, self.fix_ss_sets_ui],
                ordreButtonLst[category][4]: [self.run_unauthorized_ui, self.fix_unauthorized_ui],
                ordreButtonLst[category][5]: [self.run_unknown_nodes_ui, self.fix_unknown_ui],
                ordreButtonLst[category][6]: [self.run_dispay_layers_ui, self.fix_display_layers_ui],
                ordreButtonLst[category][7]: [self.run_mtl_ui, self.fix_mtl_ui],
                ordreButtonLst[category][8]: [self.run_ref_ui, self.fix_ref_ui],
                ordreButtonLst[category][9]: [self.run_namespaces_ui, self.fix_namespaces_ui],
                ordreButtonLst[category][10]: [self.run_non_default_cam_ui, self.fix_non_default_cam_ui],

            }
        }

        self.buttonLst.append(allDataButtons)
        self.ordreButtonLst.append(ordreButtonLst)

        # ################ TOP NODE ################
        category = "__TOP NODE__"
        # dict to store ordoned list
        ordreButtonLst = {
            category: [
                "Many top nodes",
                "Nomenclature",
                "Pivot values",
                "Freeze Transform",
            ]
        }

        allDataButtons = {
            category: {
                ordreButtonLst[category][0]: [self.run_many_top_node_ui, None],
                ordreButtonLst[category][1]: [self.run_tn_name_ui, self.fix_tn_name_ui],
                ordreButtonLst[category][2]: [self.run_tn_piv_ui, self.fix_tn_piv_ui],
                ordreButtonLst[category][3]: [self.run_tn_ft_ui, self.fix_tn_ft_ui],
            }
        }
        self.buttonLst.append(allDataButtons)
        self.ordreButtonLst.append(ordreButtonLst)

        ################ GROUPS ################
        category = "__GROUPS__"
        # dict to store ordoned list
        ordreButtonLst = {
            category: [
                "Grp nomenclature",
                "Grp freeze transform",
                "Grp visibility",
            ]
        }
        # dict of functions datas
        allDataButtons = {
            category: {
                ordreButtonLst[category][0]: [self.run_grp_nom_ui, self.fix_grps_nom_ui],
                ordreButtonLst[category][1]: [self.run_grps_ft_ui, self.fix_grp_ft_ui],
                ordreButtonLst[category][2]: [self.run_grp_visib_ui, self.fix_grp_visib_ui],
            }
        }
        self.buttonLst.append(allDataButtons)
        self.ordreButtonLst.append(ordreButtonLst)

        ################ MESHES ################
        category = "__MESH__"
        # dict to store ordoned list
        ordreButtonLst = {
            category: [
                "Mesh nomenclature",
                "Mesh shape nomenclature",
                "Mesh freeze transform",
                "Mesh history",
                "Mesh double shape",
                "Mesh visibility",
                "Mesh wrong renderStats",
                "Mesh instance",
                "Mesh cleanup",
                "Mesh polyColor",
                "Mesh nGones",
                "Mesh geo Issues",
            ]
        }
        # dict of functions datas
        allDataButtons = {
            category: {
                ordreButtonLst[category][0]: [self.run_mesh_nom_ui, self.fix_mesh_nom_ui],
                ordreButtonLst[category][1]: [self.run_mesh_shape_nom_ui, self.fix_meshes_shape_nom_ui],
                ordreButtonLst[category][2]: [self.run_mesh_ft_ui, self.fix_mesh_ft_ui],
                ordreButtonLst[category][3]: [self.run_mesh_history_ui, self.fix_mesh_history],
                ordreButtonLst[category][4]: [self.run_mesh_double_shape_ui, self.fix_mesh_double_shape_ui],
                ordreButtonLst[category][5]: [self.run_mesh_visibility_ui, self.fix_mesh_visibility_ui],
                ordreButtonLst[category][6]: [self.run_mesh_renderStats_ui, self.fix_mesh_renderStats_ui],
                ordreButtonLst[category][7]: [self.run_mesh_instance_ui, self.fix_mesh_instance_ui],
                ordreButtonLst[category][8]: [self.run_mesh_cleanup_ui, None],
                ordreButtonLst[category][9]: [self.run_mesh_polyColor_ui, self.fix_mesh_polyColor_ui],
                ordreButtonLst[category][10]: [self.run_mesh_ngones_ui, None],
                ordreButtonLst[category][11]: [self.run_mesh_geo_issues_ui, None],
            }
        }
        self.buttonLst.append(allDataButtons)
        self.ordreButtonLst.append(ordreButtonLst)

    def refresh_lists(self):
        """Fills list of items in scene"""
        self.all_meshes = read_nodes.list_all_meshes()
        self.all_groups = read_nodes.list_all_groups()
        self.top_node = read_nodes.get_top_node()
        if len(self.top_node) == 1:
            self.top_node = self.top_node[0]

    def run_rs_load_ui(self):
        """Check if scene has RedShift loaded"""
        if self.sanity_check._check_valid_redshift_load():
            self.ui.changeColorStat('Redshift load', 'green')
        else:
            self.ui.changeColorStat('Redshift load', 'red')

    def fix_rs_load_ui(self):
        """Unload redshift"""
        self.sanity_check._fix_rs_load()
        self.run_rs_load_ui()

    def run_check_time_unit_ui(self):
        """Check time unit"""
        # check scene settings
        if self.sanity_check._check_valid_time_unit():
            # edit in green the time unit button
            self.ui.changeColorStat('Time unit', 'green')

        else:
            # edit in red the time unit button
            self.ui.changeColorStat('Time unit', 'red')

    def fix_time_unit_ui(self):
        """Correcting time unit to PAL."""
        self.sanity_check._fix_time_unit()
        self.run_check_time_unit_ui()

    def run_frame_range_ui(self):
        """Check if frame range is set between START_FRAME and END_FRAME"""
        if self.sanity_check._check_valid_framerange():
            self.ui.changeColorStat('Frame range', 'green')

        else:
            self.ui.changeColorStat('Frame range', 'red')

    def fix_frame_range_ui(self):
        """Set frame range in correct fr range"""
        self.sanity_check._fix_frame_range()
        self.run_frame_range_ui()

    def run_ss_sets_ui(self):
        """Check if scene has selection sets"""
        if self.sanity_check._check_valid_selection_sets():
            self.ui.changeColorStat('Selection sets', 'green')
        else:
            self.ui.changeColorStat('Selection sets', 'red')

    def fix_ss_sets_ui(self):
        """Deleting selection sets"""
        self.sanity_check._fix_selection_sets()
        self.run_ss_sets_ui()
        self.run_unauthorized_ui()

    def run_unauthorized_ui(self):
        """"Check if scene has unauthorized ndoes"""
        self.unAuth = self.sanity_check._check_valid_authorized_nodes()
        if self.unAuth is None:
            self.ui.changeColorStat('Authorized nodes', 'green')
        else:
            self.ui.changeColorStat('Authorized nodes', 'red')

    def fix_unauthorized_ui(self):
        """Deleting unauthorized nodes: all except Transform and Shapes"""
        self.sanity_check._fix_unauthorized()
        self.run_unauthorized_ui()

    def run_unknown_nodes_ui(self):
        """Check if scene has display layers"""
        self.refresh_lists()
        if self.sanity_check._check_valid_unknownnodes():
            self.ui.changeColorStat('Unknown nodes', 'green')
        else:
            self.ui.changeColorStat('Unknown nodes', 'red')

    def fix_unknown_ui(self):
        """Deleting unknown """
        self.sanity_check._fix_unknown()
        self.run_unknown_nodes_ui()

    def run_non_default_cam_ui(self):
        """Check if scene has display layers"""
        if self.sanity_check.check_valid_default_cam():
            self.ui.changeColorStat('Non default cam', 'green')
        else:
            self.ui.changeColorStat('Non default cam', 'red')

    def fix_non_default_cam_ui(self):
        self.sanity_check._fix_non_defaut_camera()
        self.run_non_default_cam_ui()

    def run_dispay_layers_ui(self):
        """Check if scene has display layer"""
        self.refresh_lists()
        self.badDispLyr = self.sanity_check._check_valid_displaylayers()
        if self.badDispLyr is True:
            self.ui.changeColorStat('Display layers', 'green')
        else:
            self.ui.changeColorStat('Display layers', 'red')

    def fix_display_layers_ui(self):
        """Deleting display layers"""
        self.sanity_check._fix_display_layers()
        self.run_dispay_layers_ui()

    def run_mtl_ui(self):
        """Check if scene has unauthorized materials."""
        self.refresh_lists()
        if self.sanity_check._check_valid_materials() is None:
            self.ui.changeColorStat('Non default mtl', 'green')
        else:
            self.ui.changeColorStat('Non default mtl', 'red')

    def fix_mtl_ui(self):
        """Delete unauthorized mtl"""
        self.sanity_check._fix_mtl()
        self.run_mtl_ui()

    def run_ref_ui(self):
        """Check if scene has references"""
        self.refresh_lists()
        if self.sanity_check._check_valid_ref():
            self.ui.changeColorStat('References', 'green')
        else:
            self.ui.changeColorStat('References', 'red')

    def fix_ref_ui(self):
        """Remove ref"""
        self.sanity_check._fix_ref()
        self.run_ref_ui()

    def run_namespaces_ui(self):
        """Check if scene has namespace"""
        if self.sanity_check._check_valid_namespace():
            self.ui.changeColorStat('Namespaces', 'green')
        else:
            self.ui.changeColorStat('Namespaces', 'red')

    def fix_namespaces_ui(self):
        """Remove Namespaces"""
        self.sanity_check._fix_namespaces()
        self.run_namespaces_ui()

    def check_scene_elmt(self):
        """Check if scene has groups and meshes
        :return : check_elmt
        :rtype : boolean
        """
        self.refresh_lists()
        check_elmt = True
        # check if scene has mesh and group
        if len(self.all_meshes) == 0 and len(self.all_groups) == 0:
            logging.info('No meshes or group in scene. Passing...')
            check_elmt = False
            btn_to_disable = [self.ordreButtonLst[1].get('__TOP NODE__')]
            btn_to_disable.append(self.ordreButtonLst[2].get('__GROUPS__'))
            btn_to_disable.append(self.ordreButtonLst[3].get('__MESH__'))

            for btn_lst in btn_to_disable:
                for btn in btn_lst:
                    self.changeColorStat(btn, color='grey', state=False)
        return check_elmt

    def run_many_top_node_ui(self):
        """Check if scene has more than one top node
        :return : top_node_check
        :rtype : boolean
        """
        self.refresh_lists()
        btn_to_change = self.ordreButtonLst[2].get('__TOP NODE__')
        if not self.sanity_check._check_valid_top_node_number(top_node=self.top_node):
            for btn in btn_to_change:
                self.ui.changeColorStat(btn, state=False)
            self.ui.changeColorStat('Many top nodes', color='red', state=True)
            return False

        else:
            for btn in btn_to_change:
                self.ui.changeColorStat(btn, state=True)
            self.ui.changeColorStat('Many top nodes', color='green')
            return True

    def run_tn_name_ui(self):
        """Check top node name"""
        self.refresh_lists()
        if self.sanity_check._check_valid_top_node_name():
            self.ui.changeColorStat('Nomenclature', 'green', True)
        else:
            cmds.select(self.top_node)
            self.ui.changeColorStat('Nomenclature', 'red', True)

    def fix_tn_name_ui(self):
        """Renaming top nodes"""
        self.sanity_check._fix_tn_name()
        self.run_tn_name_ui()

    def run_tn_piv_ui(self):
        """"Check top node pivot position"""
        self.refresh_lists()

        if self.sanity_check._check_valid_top_node_pos(top_node=self.top_node):
            self.ui.changeColorStat('Pivot values', 'green', True)
        else:
            self.ui.changeColorStat('Pivot values', 'red', True)

    def fix_tn_piv_ui(self):
        """Fixing top node pivot values to 0 0 0."""
        self.sanity_check._fix_tn_piv(top_node=self.top_node)
        self.run_tn_piv_ui()

    def run_tn_ft_ui(self):
        """"Check if pivot is freeze transformed"""
        self.refresh_lists()
        if self.sanity_check._check_valid_top_node_ft(top_node=self.top_node):
            self.ui.changeColorStat("Freeze Transform", 'green', True)
        else:
            self.ui.changeColorStat("Freeze Transform", 'red', True)

    def fix_tn_ft_ui(self):
        """Freeze Transform top node"""
        self.sanity_check._fix_tn_ft(top_node=self.top_node)
        self.run_tn_ft_ui()

    def run_grp_nom_ui(self):
        """"Check group nomenclature:
        -Checking prefix
        -Checking suffix (with padding)"""
        self.refresh_lists()
        self.badGrpNom = self.sanity_check._valid_grps_nom()
        if self.badGrpNom is None:
            self.ui.changeColorStat('Grp nomenclature', 'green', True)
        else:
            cmds.select(self.badGrpNom)
            self.ui.changeColorStat('Grp nomenclature', 'red', True)

    def fix_grps_nom_ui(self):
        """Correcting nomenclature
        Checking grp prefix (from its children)
        And correct if"""
        self.sanity_check._fix_grps_nom()
        self.run_grp_nom_ui()

    def run_grps_ft_ui(self):
        """Check if groups are freeze transformed"""
        self.refresh_lists()
        self.badGrpFt = self.sanity_check._valid_grps_ft()
        if self.badGrpFt is None:
            self.ui.changeColorStat('Grp freeze transform', 'green', True)
        else:
            self.ui.changeColorStat('Grp freeze transform', 'red', True)

    def fix_grp_ft_ui(self):
        """Fixing group freeze transform"""
        self.sanity_check._fix_grps_ft()
        self.run_grps_ft_ui()

    def run_grp_visib_ui(self):
        """Check if groups are hidden"""
        self.refresh_lists()
        self.badGrpVisib = self.sanity_check._valid_grps_visib()
        if self.badGrpVisib is None:
            self.ui.changeColorStat('Grp visibility', 'green', True)
        else:
            self.ui.changeColorStat('Grp visibility', 'red', True)

    def fix_grp_visib_ui(self):
        """Fixing groupe visibility"""
        self.sanity_check._fix_grps_visib()
        self.run_grp_visib_ui()

    def run_mesh_nom_ui(self):
        """Check is meshes have correct nomenclature"""
        # self.refresh_lists()
        self.badMshNom = self.sanity_check._valid_meshes_nom()
        if self.badMshNom is None:
            self.ui.changeColorStat('Mesh nomenclature', 'green', True)
        else:
            self.ui.changeColorStat('Mesh nomenclature', 'red', True)

    def fix_mesh_nom_ui(self):
        """Fixing mesh nomenclature"""
        self.sanity_check._fix_meshes_nom()
        self.run_mesh_nom_ui()

    def run_mesh_shape_nom_ui(self):
        """Check the nomenclature of shape"""
        self.refresh_lists()
        self.badMshShapeNom = self.sanity_check._valid_meshes_shape_nom()
        if self.badMshShapeNom is None:
            self.ui.changeColorStat('Mesh shape nomenclature', 'green', True)
        else:
            self.ui.changeColorStat('Mesh shape nomenclature', 'red', True)

    def fix_meshes_shape_nom_ui(self):
        """Fixing bad shape nomenclature"""
        self.sanity_check._fix_meshes_shape_nom()
        self.run_mesh_shape_nom_ui()

    def run_mesh_ft_ui(self):
        """Check if meshes are freeze transformed"""
        self.refresh_lists()
        self.badMshFt = self.sanity_check._valid_meshes_ft()
        if self.badMshFt is None:
            self.ui.changeColorStat('Mesh freeze transform', 'green', True)
        else:
            self.ui.changeColorStat('Mesh freeze transform', 'red', True)

    def fix_mesh_ft_ui(self):
        """Fixing freeze transform on meshes"""
        self.sanity_check._fix_meshes_ft()
        self.run_mesh_ft_ui()

    def run_mesh_history_ui(self):
        """Check if meshes have history deleted."""
        self.refresh_lists()
        self.badMshHist = self.sanity_check._valid_meshes_history()
        if self.badMshHist is None:
            self.ui.changeColorStat('Mesh history', 'green', True)
        else:
            self.ui.changeColorStat('Mesh history', 'red', True)

    def fix_mesh_history(self):
        """Fixing history on meshes"""
        self.sanity_check._fix_meshes_history()
        self.run_mesh_history_ui()

    def run_mesh_double_shape_ui(self):
        """Check of double shapes of mesh"""
        self.refresh_lists()
        self.badMshDoubleShape = self.sanity_check._valid_meshes_double_shape()
        if self.badMshDoubleShape is None:
            self.ui.changeColorStat('Mesh double shape', 'green', True)

        else:
            self.ui.changeColorStat('Mesh double shape', 'red', True)

    def fix_mesh_double_shape_ui(self):
        """Fixing double Shapes"""
        self.sanity_check._fix_meshes_double_shape()
        self.run_mesh_double_shape_ui()

    def run_mesh_visibility_ui(self):
        """Check if mesh is visible"""
        self.refresh_lists()
        self.badMshVisib = self.sanity_check._valid_meshes_visibility()
        if not self.badMshVisib:
            self.ui.changeColorStat('Mesh visibility', 'green', True)
        else:
            self.ui.changeColorStat('Mesh visibility', 'red', True)

    def fix_mesh_visibility_ui(self):
        """Fixing visibility"""
        self.sanity_check._fix_meshes_visibility()
        self.run_mesh_visibility_ui()

    def run_mesh_renderStats_ui(self):
        """Check if meshes have correct render stats"""
        self.refresh_lists()
        self.badMshRs = self.sanity_check._valid_meshes_renderStats()
        if self.badMshRs is None:
            self.ui.changeColorStat('Mesh wrong renderStats', 'green', True)
        else:
            self.ui.changeColorStat('Mesh wrong renderStats', 'red', True)

    def fix_mesh_renderStats_ui(self):
        """Fixing render stats"""
        self.sanity_check._fix_meshes_renderStats()
        self.run_mesh_renderStats_ui()

    def run_mesh_instance_ui(self):
        """Check if meshes are an instance"""
        self.refresh_lists()
        self.badMshInst = self.sanity_check._valid_meshes_instance()
        if self.badMshInst is None:
            self.ui.changeColorStat('Mesh instance', 'green', True)
        else:
            self.ui.changeColorStat('Mesh instance', 'red', True)

    def fix_mesh_instance_ui(self):
        """Fixing instance on meshes"""
        self.sanity_check._fix_meshes_instance()
        self.run_mesh_instance_ui()

    def run_mesh_cleanup_ui(self):
        """"Check if meshes can pass clean up options."""
        self.refresh_lists()
        self.badMshCleanup = self.sanity_check._valid_meshes_cleanup()
        if self.badMshCleanup is None:
            self.ui.changeColorStat('Mesh cleanup', 'green', True)
        else:
            self.ui.changeColorStat('Mesh cleanup', 'red', True)

    def run_mesh_polyColor_ui(self):
        """"Check if polyColor is applied on mesh."""
        self.refresh_lists()
        self.badMshPolyCol = self.sanity_check._valid_meshes_polyColor()
        if self.badMshPolyCol is None:
            self.ui.changeColorStat('Mesh polyColor', 'green', True)
        else:
            self.ui.changeColorStat('Mesh polyColor', 'red', True)

    def fix_mesh_polyColor_ui(self):
        """Fixing polyColor"""
        self.sanity_check._fix_meshes_polyColor()
        self.run_mesh_polyColor_ui()

    def run_mesh_ngones_ui(self):
        """Check if meshes have ngones"""
        self.refresh_lists()
        self.badMshNgones = self.sanity_check._valid_meshes_ngones()
        if self.badMshNgones is None:
            self.ui.changeColorStat('Mesh nGones', 'green', True)
        else:
            self.ui.changeColorStat('Mesh nGones', 'red', True)

    def run_mesh_geo_issues_ui(self):
        """Check if meshes have geo issues"""
        self.refresh_lists()
        self.badMshGeo = self.sanity_check._valid_meshes_geo_issues()
        if not self.badMshGeo:
            self.ui.changeColorStat('Mesh geo Issues', 'green', True)
        else:
            self.ui.changeColorStat('Mesh geo Issues', 'red', True)

    def run_all_funct(self):
        """Run all functions together"""
        logging.info('*'*10 + 'START OF SANITY CHECK' + "*"*10)
        self.refresh_lists()
        self.run_rs_load_ui()
        self.run_check_time_unit_ui()
        self.run_frame_range_ui()
        self.run_ss_sets_ui()

        self.run_unauthorized_ui()
        self.run_unknown_nodes_ui()
        self.run_dispay_layers_ui()
        self.run_mtl_ui()
        self.run_ref_ui()
        self.run_namespaces_ui()
        self.run_non_default_cam_ui()

        if self.check_scene_elmt():
            if self.run_many_top_node_ui():
                self.run_tn_name_ui()
                self.run_tn_piv_ui()
                self.run_tn_ft_ui()
            self.run_grp_nom_ui()
            self.run_grps_ft_ui()
            self.run_grp_visib_ui()
            self.run_mesh_nom_ui()
            self.run_mesh_shape_nom_ui()
            self.run_mesh_ft_ui()
            self.run_mesh_history_ui()
            self.run_mesh_double_shape_ui()
            self.run_mesh_visibility_ui()
            self.run_mesh_renderStats_ui()
            self.run_mesh_instance_ui()
            self.run_mesh_cleanup_ui()
            self.run_mesh_polyColor_ui()
            self.run_mesh_ngones_ui()
            self.run_mesh_geo_issues_ui()

        if self.check_all is True:
            logging.info("....SCENE READY TO BE PUBLISHED ....!")

        else:
            logging.info("....SCENE IS NOT CLEAN ! See log for details ....!")

        logging.info('*'*10 + 'END OF SANITY CHECK' + "*"*10)

    def fix_all_functions(self):
        self.run_all_funct()
        self.refresh_lists()
        self.fix_time_unit_ui()
        self.fix_frame_range_ui()
        self.fix_ss_sets_ui()
        self.fix_rs_load_ui()
        self.fix_unauthorized_ui()
        self.fix_unknown_ui()
        self.fix_display_layers_ui()
        self.fix_mtl_ui()
        self.fix_ref_ui()
        self.fix_namespaces_ui()

        if self.check_scene_elmt():
            if self.run_many_top_node_ui():
                self.fix_tn_name_ui()
                self.fix_tn_piv_ui()

            self.fix_grps_nom_ui()
            self.fix_grp_ft_ui()
            self.fix_grp_visib_ui()
            self.fix_mesh_nom_ui()
            self.fix_meshes_shape_nom_ui()
            self.fix_mesh_ft_ui()
            self.fix_mesh_history()
            self.fix_mesh_double_shape_ui()
            self.fix_mesh_visibility_ui()
            self.fix_mesh_renderStats_ui()
            self.fix_mesh_instance_ui()
            self.fix_mesh_polyColor_ui()
