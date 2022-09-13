# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       Import of the lighting in reference.
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         When cancel button is hit, an error happens
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import logging

try:
    import maya.cmds as cmds
    import sgtk

except ImportError:
    pass

from ....studio.libs.reads import references as read_references
from ....studio.libs.updates import references as update_references

LGT_ASSET_ID = 4962
LGT_TASK_NAME = "LgtModule"
LGT_STEP_NAME = "LookDev"
LGT_ASSET_NAME = "LGTDefault01_Classic"

LIGHTING_TMP_SCENE = r"P:\PIRATA&CAPITANO2\10_TEMPS\Adrien_M\02_SHA\02_LRG\LRG_HDR_LightingDay_v018.ma"
NAMESPACE = "LIGHTING_TMP_SCENE"


class LightingManager(object):
    def __init__(self):
        current_engine = sgtk.platform.current_engine()
        current_context = sgtk.platform.current_engine().context
        self.sg = current_engine.shotgun

        self.entity = current_context.entity
        self.asset_type = "Asset"
        self.asset_name = current_context.entity['name']
        self.task_name = current_context.task['name']

        self.lgt_entity = self.sg.find_one("Asset", [["code", "is", LGT_ASSET_NAME]], [])
        self.lighting_path = self.get_lighting_module()

        # Import module from tk-framework-shotgun
        fw_shotgun = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-shotgun')
        self.shotgun_read_steps = fw_shotgun.import_module('studio.libs.reads.steps')
        self.shotgun_read_published_files = fw_shotgun.import_module('studio.libs.reads.published_files')

    def get_lighting_module(self):
        """
        Get latest published file of lgt module
        """
        step_entity = self.shotgun_read_steps.get_step_by_name(self.sg, LGT_STEP_NAME, "Asset")
        task_entity = self.shotgun_read_steps.get_task_by_name(self.sg, LGT_TASK_NAME, step_entity, self.lgt_entity)
        publishes = self.shotgun_read_published_files.get_latest_publish_for_task(self.sg, self.lgt_entity, task_entity)
        if publishes:
            return publishes['path']['local_path_windows']
        else:
            return LIGHTING_TMP_SCENE

    def import_lighting(self):
        lighting = cmds.textField(self.text_field, text=True, q=True)
        cmds.file(lighting, r=True, ns=NAMESPACE)

    def remove_lighting(self):
        myRef = read_references.list_references(filterRef=NAMESPACE)
        update_references.remove_reference(deleteRef=True, refList=myRef)

    def browse_file(self):
        selected_file = cmds.fileDialog2(fileMode=1, returnFilter=True)
        selected_file = os.path.realpath(str(selected_file[0]))
        cmds.textField(self.text_field, edit=True, text=str(selected_file))

    def lighting_manager_ui(self, *args):
        """
        Init scene, list all meshes/shapes and then check sym options.
        """
        logging.info("...LAUNCHING WINDOW....")
        winName = "IMPORT LIGHTS"
        if cmds.window(winName, exists=True):
            cmds.deleteUI(winName, window=True)

        fenetre = cmds.window(
            title=winName, iconName='', widthHeight=(210, 300), menuBar=True)

        # cmds.menu( label='Help', tearOff=True)
        # cmds.menuItem( label='Help page', command= lambda x: launch_help())

        cmds.columnLayout(adjustableColumn=True)
        cmds.text(label=" ")

        self.text_field = cmds.textField(text=self.lighting_path)
        self.btn_browse = cmds.button(label="browse", c=lambda x: self.browse_file())
        cmds.text(label=" ")
        cmds.text(label="-------------------")
        cmds.text(label=" ")
        cmds.button(label='Import lighting', c=lambda x: self.import_lighting())
        cmds.text(label=" ")
        cmds.button(label='Remove Ligthing', c=lambda x: self.remove_lighting())
        cmds.text(label=" ")
        cmds.button(label='Close', command=(
            'cmds.deleteUI(\"' + fenetre + '\", window=True)'))

        cmds.showWindow(fenetre)


    def launch_ui(self):
        """
        Launch window UI
        """
        logging.info('*' * 30 + "START" + "*" * 30)

        all_win = cmds.lsUI(windows=True)
        for win in all_win:
            if win != "MayaWindow":
                cmds.deleteUI(win, window=True)
        self.lighting_manager_ui()
        logging.info('*' * 30 + "END" + "*" * 30)
