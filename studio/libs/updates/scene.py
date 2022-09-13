# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Utils for scene updates
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging
import ast

try:
    import maya.cmds as cmds
    import maya.mel as mel
except ImportError:
    pass

from ..reads import nodes as read_nodes
from ..reads import scene as read_scene
from ..reads import shaders as read_shaders
from ..updates import nodes as update_nodes
from ..deletes import nodes as deletes_nodes  # keep this name because the module already has a func delete_nodes, this method should be renamed!

# FIXME: IMPORTANT! Remove set_redshift_attr import to avoid loop between libs and tools!
# from ....projects.pirataetcapitano02.shading import set_redshift_attr as set_rs_at  ## FIXME!


# FIXME: delete this method, use logger in tk-framework-common
def format_log(log_file, logger=logging):
    """
    Format log with day, hours and sec.
    Memo//close logging : logging.shutdown()
    """
    from logging.handlers import RotatingFileHandler
    formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s', datefmt='%Y/%m/%d_%H:%M:%S-')
    logger = logging.getLogger()
    file_handler = RotatingFileHandler(log_file, 'w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


# _________________________________________________________________________________________________________
##########################
# ---- PREFERENCES ----- #
##########################

def setup_scene_pal():
    """
    Setup scene in 25 FPS PAL
    :return: True or False => depending if pal has been set or not
    :rtype: boolean
    """
    current_time = cmds.currentUnit(time=True, q=True)
    if current_time != "pal":
        try:
            cmds.currentUnit(time="pal")
            logging.info('Scene s current time unit {} has been changed to PAL.'.format(current_time))
            return True
        except Exception as e:
            logging.error('Cannot set current unit to pal: "{}"'.format(e))
            return False


# TODO: use snakecase in args
def setup_color_management(colorMode="Linear"):
    """
    Setup color management
    For Redshift only
    :param: colorMode => string, "linear" by default
    """
    post_effects = cmds.ls(exactType="RedshiftPostEffects")
    for post_effect in post_effects:
        cmds.setAttr(post_effect + ".clrMgmtDisplayMode", "RS_COLORMANAGEMENTDISPLAYMODE_" + colorMode.upper(), type="string")
        logging.info('Your color scene management has been changed to : %s' % colorMode)


#  _________________________________________________________________________________________________________
##########################
# --- MANAGE PLUGIN ---- #
##########################

def load_plugin(plugin_file):
    """
    Try to load  plugin
    Raise an error if plugin cannot be load
    :param: plugin_file => string, exact plugin name, eg 'AbcExport.mll'
    """
    # If plugin is already loaded
    if cmds.pluginInfo(plugin_file, query=True, loaded=True):
        return
    # Else, try to load it
    try:
        cmds.loadPlugin(plugin_file, quiet=True)
        logging.info('Plugin "{}" has been loaded.'.format(plugin_file))
    except Exception:
        raise Exception('Unable to load plugin "{}"!'.format(plugin_file))


# Used in SC - but commented out
def unload_plugin(plugin_file, logger=logging):
    """
    Unload plugin
    :param: plugin_file => string, exact plugin name, eg 'AbcExport.mll'
    """
    if cmds.pluginInfo(plugin_file, query=True, loaded=True):
        cmds.unloadPlugin(plugin_file, f=True)
        optimize_scenesize(custom_list=["shaderOption"])
        logger.info('"{}" has been unloaded.'.format(plugin_file))
    else:
        logger.info('"{}" was already unloaded.'.format(plugin_file))


#  _________________________________________________________________________________________________________
##########################
# --- MANAGE DISPLAY --- #
##########################

# Unused
def viewport_off():
    mel.eval('paneLayout -e -manage false $gMainPane')
    logging.warning("Viewport has been shutdown!")


# Unused
def viewport_on():
    mel.eval('paneLayout -e -manage true $gMainPane')
    logging.info("Viewport has been activated.")


# Unused
def manage_viewportpanels():
    # Viewport Panels
    viewportpanels_list = [
        'modelPanel1',
        'modelPanel2',
        'modelPanel3',
        'modelPanel4'
    ]
    for viewportpanel in viewportpanels_list:
        cmds.modelEditor(viewportpanel, e=True, allObjects=1)
        cmds.modelEditor(viewportpanel, e=True, nurbsCurves=0)
        logging.info('"{}" has been managed.'.format(viewportpanel))


#  _________________________________________________________________________________________________________
##########################
# --- MANAGE RENDERER -- #
##########################

def set_renderer(my_renderer):
    """
    :param: my_renderer => Specify the exact name of your renderer
    :return: True or False => depending if renderer has been loaded or not
    :rtype: boolean
    """
    current_renderer, available_renderers = read_scene.get_current_renderer()
    logging.info('Renderer was setted to "{}".'.format(current_renderer))
    if my_renderer in available_renderers:
        if cmds.getAttr('defaultRenderGlobals.currentRenderer') != my_renderer:
            try:
                cmds.setAttr('defaultRenderGlobals.currentRenderer', l=False)
                cmds.setAttr('defaultRenderGlobals.currentRenderer', my_renderer, type='string')
                logging.info('Current renderer has been set to "{}".'.format(my_renderer))
                return True
            except Exception as e:
                logging.error(e)
                return False
    else:
        logging.error('Renderer "{}" is not available!'.format(my_renderer))
        raise Exception('Available renderers: {}'.format(available_renderers))


def restore_render_settings(renderer='mayaSoftware'):
    """
    Set currentRenderer to renderer
    Restore Render Settings UI
    :param: renderer => 'mayaSoftware' by default
    """
    try:
        # Unlock defaultRenderGlobals.currentRenderer attr and sets it to given renderer
        set_renderer(renderer)
        # Delete Render Settings UI
        if cmds.window('unifiedRenderGlobalsWindow', exists=True):
            cmds.deleteUI('unifiedRenderGlobalsWindow')
        # Restore Render Settings UI
        mel.eval('unifiedRenderGlobalsWindow;')
        logging.info("Render Settings UI has been restored.")
    except Exception as e:
        logging.error('Unable to restore render settings: "{}"'.format(e))


# _________________________________________________________________________________________________________
# #########################
# -------- BAKE --------- #
# #########################

# TODO use snakecase in func name, args
# FIXME: remove hardcodee, clean this method
# TODO: maybe add a return
def redshiftCustomBake(w=4096, h=4096, launchBake=True, selected=True):
    """
    Bake redshift with custom options
    "redshiftBakeDefaultsTileMode": 4 => mari
    :param: w => 4096 by default
    :param: h => 4096 by default
    :param: launchBake => if False, just modify settings in maya withou launch baking
    :param: selected => True by default
    """
    # Set vars
    if selected:
        bake_mode = 2  # Selected
    else:
        bake_mode = 1  # Wip : to check
    int_options_to_set = {
        "redshiftBakeMode": bake_mode,
        "redshiftSkipObjectsWithoutBakeSets": False,
        "redshiftBakeDefaultsWidth": w,
        "redshiftBakeDefaultsHeight": h,
        "redshiftBakeDefaultsTileMode": 4,
        "redshiftBakeDefaultsAutoTileCount": True,
        "redshiftBakeDefaultsNumTilesU": 1,
        "redshiftBakeDefaultsNumTilesV": 1,
    }
    str_options_to_set = {
        "redshiftBakeDefaultsUvSet": "map1",
    }
    # Set option
    for option_found in int_options_to_set:
        cmds.optionVar(intValue=(option_found, int_options_to_set[option_found]))
    for option_found in str_options_to_set:
        cmds.optionVar(stringValue=(option_found, str_options_to_set[option_found]))
    # Launch bake
    if launchBake:
        logging.info('Launching render bake...')
        mel.eval('rsRender -bake')
    logging.info('Rendering bake has been done.')


# TODO use snakecase in args and vars
# TODO: put attr in a dict to avoid multiple cmds.setAttr
# FIXME: remove hardcodee, clean this method
# TODO: add docstring param/return/rtype
def setup_render_settings(fileName, aovList, resolution="HD 1080", customResol=[],
                          fileFormat="png", fileBits=16, animationMode=0, startFr=1, endFr=1):
    """
    Format renderer with options
    """
    FORMATS = {
        "iff": 0,
        "exr": 1,
        "png": 2,
        "tif": 5,
        "tga": 3,
        "jpg": 4
    }
    imgFrt = FORMATS[fileFormat]
    RESOL = {
        "HD 1080": [1920, 1080],
        "HD 720": [1280, 720],
        "Custom": customResol
    }
    # File name
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", fileName, type="string")
    # Resolution
    cmds.setAttr("defaultResolution.width", RESOL[resolution][0])
    cmds.setAttr("defaultResolution.height", RESOL[resolution][1])
    # File format type
    cmds.setAttr("redshiftOptions.imageFormat", imgFrt)
    # Bits
    cmds.setAttr("redshiftOptions.{}Bits".format(fileFormat), fileBits)
    # Animation option
    cmds.setAttr("defaultRenderGlobals.animation", animationMode)
    cmds.setAttr("defaultRenderGlobals.startFrame", startFr)
    cmds.setAttr("defaultRenderGlobals.endFrame", endFr)
    mel.eval('unifiedRenderGlobalsWindow')
    mel.eval('redshiftUpdateActiveAovList')
    # Aov Setup
    if aovList:
        for aov in aovList:
            testName = "rsAov_" + aov.replace(" ", "")
            if testName not in cmds.ls(type="RedshiftAOV"):
                ao = cmds.rsCreateAov(type=aov)
                cmds.setAttr(ao + ".enabled", True)
                if imgFrt == 0:
                    logging.error('IFF format is not supported for renderpasses!')
                cmds.setAttr(ao + '.fileFormat', imgFrt)
                cmds.setAttr(ao + ".{}Bits".format(fileFormat), fileBits)
            mel.eval('unifiedRenderGlobalsWindow')
            mel.eval('redshiftUpdateActiveAovList')
    if cmds.window('unifiedRenderGlobalsWindow', exists=True):
        cmds.deleteUI('unifiedRenderGlobalsWindow')
        mel.eval('redshiftUpdateActiveAovList')


# TODO: use full names especially in the func names: copy_shader_assignments
# NOTE: maybe not the best place
def copy_shdr_assign(imported_topnode, origin_topnode):
    """
    Copy Values of top nodes Imported's notes to base one
    :param: imported_topnode
    :return: assigned_shaders_note
    :rtype: string
    """
    assigned_shaders_note = cmds.getAttr(imported_topnode + ".notes")
    update_nodes.add_custom_attr(node=origin_topnode, attrName="notes", content=str(assigned_shaders_note))
    return assigned_shaders_note


# _________________________________________________________________________________________________________
# #########################
# ------ OPTIMIZE ------- #
# #########################

def optimize_scenesize(custom_list=None):
    """
    Optimize size size with custom otions.
    :param: custom_list => list of custom options that will be only performed.
    For ex: ['brushOption', 'locatorOption'] will do optimize size only on these 2 options
    """
    default_options = {
        "nurbsSrfOption": 1,
        "nurbsCrvOption": 0,
        "unusedNurbsSrfOption": 0,
        "deformerOption": 1,
        "unusedSkinInfsOption": 1,
        "poseOption": 0,
        "clipOption": 0,
        "expressionOption": 0,
        "groupIDnOption": 1,
        "animationCurveOption": 1,
        "shaderOption": 1,
        "cachedOption": 0,
        "transformOption": 1,
        "displayLayerOption": 1,
        "renderLayerOption": 1,
        "setsOption": 1,
        "partitionOption": 0,
        "locatorOption": 0,
        "ptConOption": 1,
        "pbOption": 1,
        "snapshotOption": 1,
        "unitConversionOption": 1,
        "referencedOption": 1,
        "brushOption": 1,
        "unknownNodesOption": 0,
        "shadingNetworksOption": 0
    }
    user_options = {}
    if custom_list:
        for key, value in default_options.items():
            user_options[key] = 1 if key in custom_list else 0
    # Changing options var to user
    for var, value in user_options.items():
        cmds.optionVar(intValue=(var, value))
    logging.info('Launching optimize scene size')
    mel.eval('cleanUpScene -userCleanUp_PerformCleanUpScene')
    # Reinit var by default
    for var, value in user_options.items():
        cmds.optionVar(intValue=(var, value))


# _________________________________________________________________________________________________________
# #########################
# --------- CLEAN ------- #
# #########################

# Used in hooks: create_out_build, actions_pirata2
def clean_shading_scene_for_anim(imported_nodes, logger=logging):
    """
    Clean shading scene for render, wich means get only lambert shaders
    :param: imported_nodes
    :rtpe: _clean_shading_scene
    """
    return _clean_shading_scene(imported_nodes=imported_nodes, shader_type="lambert", logger=logger)


# Used in hooks: create_out_build, actions_pirata2
def clean_shading_scene_for_render(imported_nodes, logger=logging):
    """
    Clean shading scene for render, wich means get only Redshift shaders
    :param: imported_nodes
    :return: _clean_shading_scene
    :rtype: list
    """
    # Unsmooth mesh
    shapes = read_nodes.list_all_shapes()
    update_nodes.unsmooth_meshes(shapes, 0)
    # Activate smooth for all redshift attributs
    set_rs_at.SetRedshiftAttr(batch=False).set_rs_on_shapes(shapes)
    return _clean_shading_scene(imported_nodes=imported_nodes, shader_type="Redshift", logger=logger)


# NOTE: private method?
# TODO: snakecase
def _clean_shading_scene(imported_nodes, shader_type, logger=logging):
    """
    Reassign shaders of a specific type and delete unused imported nodes.
    :param: imported_nodes => list of nodes imported from shading scene file
    :param: shader_type => string, shader type to reassign on modeling (could be "redshift" or "lambert")
    :return: imported nodes without deleted ones
    :rtype: list
    """
    # Set vars
    sha_short_name = "SHA"
    topnode_suffix = "Top"
    logger.info('> Clean Shading scene')
    if not imported_nodes:
        logger.info('No Shaders imported!')
        return
    top_nodes = read_nodes.get_top_node()
    logger.info('{} top_nodes: {}'.format("=" * 25, top_nodes))
    # Target top node (the modeling one)
    target_top_node = [tn[1:] for tn in top_nodes if tn not in imported_nodes if tn.startswith('|') and tn.endswith('_{}_{}'.format(sha_short_name, topnode_suffix)) is False]
    target_top_node = target_top_node[0]
    logger.info('Target topnode: {}'.format(target_top_node))
    # Source top node (the shading one)
    src_top_node = cmds.ls(imported_nodes, assemblies=True, long=True)[0]
    if not src_top_node:
        logger.error('No top nodes in imported nodes!')
        return
    logger.info('Source topnode: "{}"'.format(src_top_node))
    # Copy dict of assignation shaders inside the old top node
    dict_shdr = copy_shdr_assign(imported_topnode=src_top_node, origin_topnode=target_top_node)
    # Convert to dictionnary the string of the top
    dict_shdr = ast.literal_eval(str(dict_shdr))
    # Get shaders assignation stored in top node
    usedShaders = read_scene.get_shaders_stored(topnode=target_top_node, shader_type=shader_type)
    # Get shading network of used shaders to avoid delete
    shadingNetwork = read_shaders.get_shading_network(shadersList=usedShaders)
    # Reassignation of shaders
    read_shaders.reassign_shaders(dict_shdr, shader_type)
    logger.info('> Shaders reassignement')
    # Delete unecessary nodes
    # filters to get objects to delete
    all_objects = cmds.ls()
    objToDel = []
    for obj in all_objects:
        obj = cmds.ls(obj, long=True)[0]
        if (
            obj in imported_nodes
            and obj not in usedShaders
            and obj not in shadingNetwork
        ):
            objToDel.append(obj)
    logger.info("About to delete objects: {}".format(objToDel))
    deletes_nodes.delete_nodes(nodesList=objToDel)
    return list(set(imported_nodes) - set(objToDel))


# TODO: remove hardcode
def clean_rig_scene(imported_nodes, task_name, logger=logging):
    """
    Parent groups in the module
    :param: imported_nodes
    :param: task_name
    :return: top_node => of rigging hierarchy
    :rtype: string
    """
    # Set vars
    topnode_suffix = "Top"
    group_suffix = "Grp"
    rig_short_name = "RIG"
    mdl_short_name = "MDL"
    rigmodule_mdl_node = "MOD"
    rigmodule_asset_node = "AssetName_{}".format(topnode_suffix)
    rig_top_nom = "_{}_{}".format(rig_short_name, topnode_suffix)
    mdl_top_nom = "_{}_{}".format(mdl_short_name, topnode_suffix)
    # Get top nodes
    top_nodes = read_nodes.get_top_node()
    rig_top = [top for top in top_nodes if rig_top_nom in top and top not in imported_nodes]
    mdl_top = [top for top in top_nodes if mdl_top_nom in top and top not in imported_nodes]
    # Check if we found a rig topnode
    if not rig_top:
        logger.error('No "{}" topnode found!'.format(rig_short_name))
        rig_top = []
    else:
        rig_top = rig_top[0]
    # Check if we found a mdl topnode
    if not mdl_top:
        logger.error('No "{}" topnode found!'.format(mdl_short_name))
        mdl_top = []
    else:
        mdl_top = mdl_top[0]
    # Get relatives list
    top_node = [top for top in top_nodes if top not in rig_top and top not in mdl_top and rigmodule_asset_node in top][0]  # FIXME: hardcoding
    mod_grp = [grp for grp in cmds.listRelatives(top_node, c=True) if "{}_{}".format(rigmodule_mdl_node, group_suffix) in grp][0]
    rig_grp = [grp for grp in cmds.listRelatives(top_node, c=True) if "{}_{}".format(rig_short_name, group_suffix) in grp][0]
    if cmds.objExists(mod_grp):
        mod_grp = mod_grp.replace("_{}".format(topnode_suffix), "_{}".format(group_suffix))
    if cmds.objExists(rig_grp):
        rig_grp = rig_grp.replace("_{}".format(topnode_suffix), "_{}".format(group_suffix))
    # Parenting
    if cmds.objExists(rig_top) and cmds.objExists(rig_grp):
        cmds.parent(rig_top, rig_grp)
    if cmds.objectType(mdl_top) and cmds.objExists(mod_grp):
        cmds.parent(mdl_top, mod_grp)
    return top_node


# _________________________________________________________________________________________________________
# #########################
# ------- OUTLINER ------ #
# #########################

def set_outliner_color_attr(key, element):
    """
    Set outliner color ON and color element
    :param: key
    :param: element
    """
    outliner_color_attr = cmds.getAttr('{}.useOutlinerColor'.format(element))
    # Set color attr to True
    if outliner_color_attr is not True:
        cmds.setAttr('{}.useOutlinerColor'.format(element), True)
    # Apply color we want
    if key == 'unique':
        cmds.setAttr('{}.outlinerColor'.format(element), 1, 1, 0)
    elif key == 'common':
        cmds.setAttr('{}.outlinerColor'.format(element), 0, 1, 0)
    elif key == "no track":
        cmds.setAttr('{}.outlinerColor'.format(element), 1, 0, 1)
    elif key == "error":
        cmds.setAttr('{}.outlinerColor'.format(element), 1, 0, 0)
    # Refresh outliners
    outliners = cmds.getPanel(type='outlinerPanel')
    for outliner in outliners:
        cmds.outlinerEditor(outliner, e=True, refresh=True)


# TODO: maybe give a better name in the arg? its type and functionality is not obvious
# rename to reflect that it's an update: change_reference_nodes_visibility()
def display_reference_nodes(show_or_hide):
    """
    Show RN nodes or not in the outliner
    :param: show_or_hide
    :return: display_change
    :rtype: boolean
    """
    display_change = False
    outliners = cmds.getPanel(type='outlinerPanel')
    for outliner in outliners:
        show_ref_nodes = cmds.outlinerEditor(outliner, q=True, rn=True)
        if show_ref_nodes != show_or_hide:
            cmds.outlinerEditor(outliner, e=True, rn=show_or_hide)
            display_change = True
    return display_change


# ________________________________________________________________________________________________________
##########################
# ----- FRAME RANGE ---- #
##########################

# TODO: put a try except and return if framerange has been set properly?
# TODO: snakecase
# FIXME: rtype? There is no return
def modify_frame_range(startFr, endFr):
    """
    Modify frame range, animationf rame range and global range.
    :param: startFr => start of frame range
    :param: endFr => end of frame range
    :rtype : int
    """
    cmds.playbackOptions(minTime=startFr)
    cmds.playbackOptions(animationStartTime=startFr)
    cmds.playbackOptions(animationEndTime=endFr)
    cmds.playbackOptions(maxTime=endFr)
    logging.info('Frame range has been changed to {} - {}'.format(startFr, endFr))
