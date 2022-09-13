# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#
#   DESCRIPTION :       This tool is used conform shading assets
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging
try:
    import sgtk
    import maya.cmds as cmds
except ImportError:
    pass

from ....studio.libs.reads import nodes as read_nodes
from ....studio.libs.updates import nodes as update_nodes
from ....studio.libs.deletes import nodes as delete_nodes
from ....studio.libs.updates import scene as update_scene
from ....studio.libs.reads import shaders as read_shaders
from ....studio.libs.checks import nodes as check_nodes


class CleanAssetScene(object):
    """
    This script will rename topnodes by using the detect sym auto
    """
    def __init__(self):
        # Get the engine instance that is currently running.
        current_engine = sgtk.platform.current_engine()
        # Grab the pre-created Sgtk instance from the current engine.
        self.tk = current_engine.sgtk
        self.sg = current_engine.shotgun
        self.subassets_group = 'Subassets_Grp'
        self.bridge_name = 'BridgeShadingPreRig'

    def clean_shading_scene(self):
        if cmds.objExists(self.subassets_group):
            # Get reference bridge list
            reference_list = cmds.ls('{}*'.format(self.bridge_name), type='reference')
            # Clean ASB shading scene
            for sub_ref in reference_list:
                ref_file = cmds.referenceQuery(sub_ref, f=True)
                cmds.file(ref_file, rr=True)
            cmds.delete(self.subassets_group)

    def prepare_shading_bridge(self):
        """
        Prepare scene of shading for bridge.
        - Remove reference
        - Store shaders assignations on top node
        - Remove everything except topNode and shaders+ shading network of given type
        """
        top_nodes = read_nodes.get_top_node()
        top_node_sha = [top for top in top_nodes if top.endswith("_SHA_Top")]
        if top_node_sha:
            top_node_sha = top_node_sha[0]
        else:
            logging.error("No Shading top node found")
            return

        # Store shaders on top node, then get shaders and shading network
        shaders_data = update_nodes.store_shaders_assign(topNode=top_node_sha)
        shaders_to_keep = update_scene.get_shaders_stored(topNode=top_node_sha)
        shading_network = read_shaders.get_shading_network(shadersList=shaders_to_keep)

        obj_to_keep = [top_node_sha] + shaders_to_keep + shading_network
        obj_to_del = [cmds.ls(obj, long=True)[0] for obj in cmds.ls() if cmds.ls(obj, long=True)[0] not in obj_to_keep and obj not in check_nodes.get_basic_nodes()]

        delete_nodes.delete_nodes(obj_to_del)
        # Cleaning up
        delete_nodes.delete_unknown_nodes()

        return shaders_data

    def execute(self):
        self.prepare_shading_bridge()
        self.clean_shading_scene()
