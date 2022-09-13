# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#                       Nicolas Dorey
#
#   DESCRIPTION :       Nodes checks lib
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging
import re

try:
    import maya.cmds as cmds
    import sgtk
except ImportError:
    pass

from ..reads import nodes as read_nodes
from ..reads import scene as read_scene


PREFIXES = ['U_', 'C_', 'L_', 'R_', 'B_', 'F_']
ELT_GRP = "Elt_Default_Grp"
ASB_GRP = "Assemblies_Grp"
COMMON_GRP = "Common_Grp"
TRASH_GRP = "Trash_Grp"
TOP_SUFFIX = 'Top'
SPLIT_SET_SUFFIX = 'SplitSet'
MDL_STEP_SN = 'MDL'
MASTER_ROOT_SET = 'MasterSets'
SOURCE_ATTR = 'source'


# ________________________________________________________________________________________________________
##########################
# ----- NODE TYPE -------#
##########################

# FIXME: Important! Find a better way to define basic_nodes, this is not a method!
# Used in out_task_asset
def get_basic_nodes():
    """
    List of basic maya scene nodes
    """
    basic_nodes = [
        'time1', 'sequenceManager1', 'hardwareRenderingGlobals', 'renderPartition', 'renderGlobalsList1', 'defaultLightList1', "MayaNodeEditorSavedTabsInfo",
        'defaultShaderList1', 'postProcessList1', 'defaultRenderUtilityList1', 'defaultRenderingList1', 'lightList1', 'defaultTextureList1', 'lambert1',
        'standardSurface1', 'particleCloud1', 'initialShadingGroup', 'initialParticleSE', 'initialMaterialInfo', 'shaderGlow1', 'dof1',
        'defaultRenderGlobals', 'defaultRenderQuality', 'defaultResolution', 'defaultLightSet', 'defaultObjectSet', 'defaultViewColorManager',
        'defaultColorMgtGlobals', 'hardwareRenderGlobals', 'characterPartition', 'defaultHardwareRenderGlobals', 'ikSystem', 'hyperGraphInfo',
        'hyperGraphLayout', 'globalCacheControl', 'strokeGlobals', 'dynController1', 'lightLinker1', 'persp', 'perspShape', 'top', 'topShape', 'hyperShadePrimaryNodeEditorSavedTabsInfo',
        'front', 'frontShape', 'side', 'sideShape', 'shapeEditorManager', 'poseInterpolatorManager', 'layerManager', 'defaultLayer', 'sceneConfigurationScriptNode',
        'renderLayerManager', 'defaultRenderLayer', 'ikSCsolver', 'ikRPsolver', 'ikSplineSolver', 'hikSolver', 'shapeEditorManager1', 'poseInterpolatorManager1',
        'objectFilter49', 'selectionListOperator107', 'DefaultCreateNodeFilter2', 'selectionListOperator108', 'objectFilter50', 'selectionListOperator109', 'objectFilter51',
        'selectionListOperator110', 'objectFilter52', 'selectionListOperator111', 'objectFilter53', 'selectionListOperator112', 'objectFilter54', 'selectionListOperator113',
        'DefaultMaterialsFilter16', 'DefaultLightsAndOpticalFXFilter14', 'selectionListOperator114', 'DefaultAllLightsFilter16', 'DefaultOpticalFXFilter15', 'objectTypeFilter108',
        'DefaultTexturesFilter13', 'DefaultRenderUtilitiesFilter10', 'DefaultRenderingFilter5', 'DefaultImagePlanesFilter8', 'objectTypeFilter109', 'DefaultMrLayerFilter3',
        'objectFilter55', 'selectionListOperator115', 'DefaultCameraShapesFilter7', 'objectTypeFilter110', 'DefaultShadingGroupsFilter11', 'objectTypeFilter111',
        'DefaultMaterialsAndShaderGlowFilter7', 'selectionListOperator116', 'DefaultMaterialsFilter17', 'DefaultShaderGlowFilter9', 'objectTypeFilter112', 'defaultBrush', 'uiConfigurationScriptNode'
    ]
    return basic_nodes


# TODO: MODIFY when better list // WIP
# TODO: snakecase
def check_unauthorized_nodes(exception=None, blackList=[], logger=logging):
    """
    Check if other nodes besides transform and shape
    :param: exception => None by default
    :param: blackList => empty list by default
    :return: unauthorized
    :rtype: list
    """
    basic_nodes = get_basic_nodes()
    authorized = ['transform', 'mesh']
    if exception:
        if type(exception) == list:
            authorized += exception
        else:
            authorized.append(exception)
    all_nodes = cmds.ls()
    unauthorized = []
    for node in all_nodes:
        split_node = node.split(':')[-1]
        if split_node not in basic_nodes:
            node_type = cmds.nodeType(node)
            # split for references
            if node in blackList:
                unauthorized.append(node)
            else:
                if node_type not in authorized:
                    unauthorized.append(node)
    if unauthorized:
        logger.error('WARNING! Unauthorized nodes in scene! {}'.format(unauthorized))
    return unauthorized


# TODO: rename function => check_unknown_nodes()
def check_unknow_nodes(logger=logging):
    """
    Check if scene has unknown nodes
    :return: unknown
    :rtype: list
    """
    unknown = read_nodes.list_unknown_nodes()
    if len(unknown) > 0:
        logger.error("Warning! Unknown nodes found: {}".format(unknown))
    return unknown


# ________________________________________________________________________________________________________
##########################
# ---GROUPS HIERARCHY ---#
##########################

def check_base_grp(grp, logger=logging):
    """
    Check if basic groups are present
    :param: grp
    :return: check_grp
    :rtype: boolean
    """
    check_grp = True
    if cmds.objExists(grp) is False:
        check_grp = False
    return check_grp


# TODO snakecase
# FIXME: This is not the right place for this function!
# There is already a function with the same name here:
# C:\Shotgun\tk-framework-shotgun\python\studio\libs\reads\assets.py
def get_variation_list(sg, assetLib_Name, logger=logging):
    """
    Get Variation list with sub assets
    :param: sg
    :param: assetLib_Name
    :return: variation_sub_dict
    :rtype: dict
    """
    # Import module by using current engine to get tk-framework-common throw tk-multi-accessor
    try:
        current_engine = sgtk.platform.current_engine()
        # Import module from tk-framework-shotgun
        fw_shotgun = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-shotgun')
        shotgun_read_asset_libraries = fw_shotgun.import_module('studio.libs.reads.asset_libraries')
        shotgun_read_assets = fw_shotgun.import_module('studio.libs.reads.assets')
    except ImportError:
        raise('Current engine not found!')
    variation_sub_dict = {}
    variation_list = shotgun_read_asset_libraries.get_assets_from_assetslib_name(sg, assetLib_Name, 137)
    for variation_found in variation_list:
        sub_list = shotgun_read_assets.get_sub_assets_from_asset(sg, variation_found['id'], 137)
        variation_sub_dict[variation_found['code']] = sub_list
    return variation_sub_dict


# TODO: snakecase
# FIXME: This is not the right place for this function!
def get_subasset_list(variationList, logger=logging):
    """
    :param: variationList
    :return: sub_assets, list from dictionnary of assets
    :rtype: list
    """
    sub_assets = []
    for value in variationList.values():
        for item in value:
            sub_assets.append(item)
    sub_assets = list(set(sub_assets))
    return sub_assets


# TODO: snakecase
def check_master_hi(variationList, step_name, logger=logging):
    """
    Check top node content in Master Scene
    - Check if default groups are there
    - Check if all master's variation are under top nodes.
    - Check if all subassets are in subasset grp.
    :param: variationList
    :param: step_name
    :return: check_master_hi
    :rtype: boolean
    """
    check_master_hi = True
    tn = read_nodes.get_top_node()
    # Childs of top node
    childs = cmds.listRelatives(tn, fullPath=True, c=True)
    # Short names
    short_children = [cmds.ls(child, sn=True)[0] for child in childs]
    # Must be always presents
    defaults = [
        ELT_GRP,
        ASB_GRP,
        COMMON_GRP,
        TRASH_GRP
    ]
    non_defaults = []
    for child in short_children:
        # Check for intruder under top node
        if child not in defaults:
            logger.error('Unauthorized children under top node! {}'.format(child))
            check_master_hi = False
        sub_child = cmds.listRelatives(child, fullPath=True)
        if sub_child:
            for sub in sub_child:
                sub = cmds.ls(sub, sn=True)[0].split('|')[-1]
                sub = sub.split(':')[-1]
                non_defaults.append(sub)
    grp_format = '{grp}_{step_name}_{top}'
    for default in defaults:
        if default not in short_children:
            logger.error('Default Group %s is missing!' % default)
            check_master_hi = False
    # Check if under top node are allowed only defaults nodes + variations groups
    variation_sub_dict = variationList
    # Check if each variation is in top node
    for key in variation_sub_dict:
        variationIdealName = grp_format.format(grp=key, step_name=step_name, top=TOP_SUFFIX)
        if variationIdealName not in non_defaults:
            logger.error("Missing variation %s in top node hierarchy!" % variationIdealName)
            check_master_hi = False
    # Check subassets
    sub_assets = get_subasset_list(variationList)
    # sub_children = cmds.listRelatives(cmds.ls(ELT_GRP)[0])
    sub_children = [elmt for elmt in cmds.listRelatives(ELT_GRP) if cmds.objExists(ELT_GRP)]
    if sub_assets:
        for sub in sub_assets:
            ideal_value = grp_format.format(grp=sub, step_name=step_name, top=TOP_SUFFIX)
            if ideal_value not in sub_children:
                logger.error("Missing subasset %s in Subasset folder!" % sub)
                check_master_hi = False
    return check_master_hi


# ________________________________________________________________________________________________________
##########################
# ------- NAMING --------#
##########################

# TODO: snakecase
def check_camelCase(mesh, logger=logging):
    """
    True if nomenclature is camel case upper
    :param: mesh
    :return: check_cc
    :rtype: boolean
    """
    check_cc = True
    # mesh = cmds.ls(mesh, sn=True)[0]
    if "|" in mesh:
        mesh = mesh.split('|')[-1]
    split_name = mesh.split('_')
    for part in split_name:
        if part[0].isupper() is False:
            check_cc = False
            logging.error('Wrong camel case convention!')
    return check_cc


def check_validate_prefix(mesh, logger=logging):
    """
    Check the prefix of object.
    NEED SHORT NAME.
    valid_headings = ['U_', 'C_', 'L_', 'R_']
    :param: mesh
    :return: valide_head
    :rtype: boolean
    """
    mesh_sn = mesh.split('|')[-1]
    valide_head = False
    valid_headings = PREFIXES
    reg_list = map(re.compile, valid_headings)
    if any(regex.match(mesh_sn) for regex in reg_list):
        valide_head = True
    else:
        logger.error("Wrong prefix found on mesh: {}".format(mesh))
    return valide_head


def check_top_node_name(task=None, logger=logging):
    """
    Check if top node name is same as scene -- removing the task name
    :param: task => None by default
    :return: good_name
    :rtype: boolean
    """
    good_name = True
    top_node = read_nodes.get_top_node()[0]
    file_name = read_scene.get_file_informations()[1]
    # Get rid of version in file name and add grp
    correct_name = file_name.split('.v')[0] + "_{}".format(TOP_SUFFIX)
    if task:
        correct_name = correct_name.replace("_" + task, "")
    top_node = cmds.ls(top_node, sn=True)[0]
    if top_node != correct_name:
        logger.error("Top Node doesn't match scene filename: scene_name={scene_name} -- top_node_name = {top_node_name}".format(scene_name=correct_name, top_node_name=top_node))
        good_name = False
    return good_name


def check_master_tn(assetlib_name, step_name, task_name, logger=logging):
    """
    Check if top node name is correct in Masterscene
    :param: assetlib_name
    :param: step_name
    :param: task_name
    :return: correct_name
    :rtype: boolean
    """
    correct_name = True
    ideal_topnode_name = "|{assetlib_name}_{step_name}_{task_name}_{top}".format(assetlib_name=assetlib_name, step_name=step_name, task_name=task_name, top=TOP_SUFFIX)
    tn = read_nodes.get_top_node()[0]
    if ideal_topnode_name != tn:
        logger.error('Wrong top node name for master scene!')
        correct_name = False
    return correct_name


def check_top_node_pos(logger=logging):
    """
    Check if topnode is at 0,0,0.
    :return: validate_pos
    :rtype: list
    """
    top_node = read_nodes.get_top_node()[0]
    piv = cmds.xform(top_node, piv=True, q=True)
    validate_pos = all(pos == 0 for pos in piv)
    # return values of pos
    if not validate_pos:
        validate_pos = piv
    elif validate_pos is True:
        validate_pos = None
    return validate_pos


def check_grp_prefix(grp, logger=logging):
    """
    True if grp has the right naming regarding its childrens
    :param: grp
    :return: check_grp
    :rtype: boolean
    """
    check_grp = True
    grp_sn = cmds.ls(grp, sn=True)[0]
    if "|" in grp_sn:
        grp_sn = grp_sn.split('|')[-1]
    # prefix grp
    prefix_grp = read_nodes.get_prefix(grp_sn)
    if prefix_grp is None:
        check_grp = False
    else:
        # get prefix of children
        all_pref_childs = read_nodes.get_children_prefix(grp)
        if all_pref_childs is None:
            logging.error('Please rename correctly children of grp : %s' % grp)
            check_grp = False
        else:
            # determine what prefix must be used
            prefix = read_nodes.determine_prefix(all_pref_childs)
            if prefix_grp != prefix:
                logging.info('Prefix of group is not correct regarding its children')
                check_grp = False
    return check_grp


# TODO: fix name "check_valid_suffix()"
def check_valide_suffix(mesh, regexp, logger=logging):
    """
    Check the suffix of object
    :param: mesh
    :param: regexp
    :return: valide_end
    :rtype: bool
    """
    valide_end = True
    # check if mesh name ends with regexp
    pattern = re.compile(regexp)
    match = pattern.search(mesh)
    if match is None:
        valide_end = False
    return valide_end


# TODO: remove hardcode regex from here
def check_obj_nomenclature(mesh, top=False, logger=logging):
    """
    Check if mesh name starts with R, L, C or U
    And ends with an expression given
    :param: mesh
    :param: top => False by default
    :return: valide_name
    :rtype: boolean
    """
    valide_name = True
    # Check if mesh ends with _Msh
    wrong_names = read_nodes.list_wrong_mesh_names()
    if mesh in wrong_names:
        valide_name = False
    mesh_sn = cmds.ls(mesh, sn=True)[0]
    if read_nodes.is_reference(mesh=mesh):
        mesh_sn = mesh_sn.split(':')[-1]
    # TODO check de spliter les regexp en (*) et affiner en split
    grp_pattern = r'[C-U]_(?:[A-Z][aA-zZ]{1,}\d\d){1,}_Grp'
    mesh_pattern = r'[C-U]_[A-Z][aA-zZ]{1,}\d\d_\d\d\d_Msh$'
    shape_pattern = r'[C-U]_[A-Z][aA-zZ]{1,}\d\d_\d\d\d_MshShape$'
    if top:
        grp_pattern = r'\w_\w[^_]{1,}_Top$'
    # Check prefix
    valide_prefix = check_validate_prefix(mesh=mesh_sn)
    # Check suffixe for mesh or grp
    valide_suffix = False
    if read_nodes.is_group(mesh) is True:
        # valide_prefix = check_grp_prefix(grp=mesh_sn)  for the moment, disabling the check of the symetry of hierarchy
        valide_suffix = check_valide_suffix(mesh=mesh_sn, regexp=grp_pattern)
    elif cmds.objectType(mesh, isa="shape"):
        valide_suffix = check_valide_suffix(mesh=mesh_sn, regexp=shape_pattern)
    else:
        valide_suffix = check_valide_suffix(mesh=mesh_sn, regexp=mesh_pattern)
    if valide_prefix is False:
        valide_name = False
    if valide_suffix is False:
        valide_name = False
    return valide_name


def check_node_type_suffix_nom(nom_dict, white_list=[], logger=logging):
    """
    Check for each nodes of type that it ends with the right nomenclature
    from the dictionnary
    :param: nom_dict
    :param: white_list => empty list by default
    :return: True or False
    :rtype: boolean
    """
    wrong_nom_nodes = []
    for node_type, nom in nom_dict.items():
        if node_type == "Group":
            all_type_nodes = read_nodes.list_all_groups()
        else:
            all_type_nodes = cmds.ls(type=node_type, long=True)
        if white_list:
            all_type_nodes = [x for x in all_type_nodes if x not in white_list]
        for node in all_type_nodes:
            in_list = False
            if type(nom) == list:
                for typ in nom:
                    if node.endswith(typ):
                        in_list = True
                if not in_list:
                    wrong_nom_nodes.append(node)
            else:
                if not node.endswith(nom):
                    wrong_nom_nodes.append(node)
    if wrong_nom_nodes:
        logger.error('SANITY CHECK SCENE PROBLEM: Wrong nomenclature of node type for : {}'.format(wrong_nom_nodes))
        return False
    else:
        return True


def check_shape_name(mesh, logger=logging):
    """
    Check if name of mesh and shape are identical
    :param: mesh
    :return: name
    :rtype: boolean
    """
    name = True
    sn_mesh = cmds.ls(mesh, sn=True)[0]
    sn_mesh = sn_mesh.split("|")[-1]
    ideal_name = mesh + "|" + sn_mesh + "Shape"
    shape = read_nodes.get_shape_or_transform(mesh)
    if shape != ideal_name:
        name = False
    return name


# ________________________________________________________________________________________________________
##########################
# -------- SETS ---------#
##########################

# TODO: snakecase whiteList
def check_selection_sets(whiteList=[], logger=logging):
    """
    Check if scene has selection sets
    :param: whiteList => empty list by default
    :return: all_sets
    :rtype: list
    """
    defs = read_nodes.list_default_nodes()
    if whiteList:
        defs += whiteList
    all_sets = [ss for ss in cmds.ls(set=True) if ss not in defs]
    if all_sets:
        logger.error("Selection sets found: {}".format(all_sets))
    return all_sets


# Unused
def check_common(logger=logging):
    """
    Used in MasterScene
    True if content of all subassets set are in common grp
    :return: check_sets_common
    :rtype : boolean
    """
    # Import module by using current engine to get tk-framework-common throw tk-multi-accessor
    try:
        current_engine = sgtk.platform.current_engine()
        fw_common = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-common')
        common_read_dicts = fw_common.import_module("studio.libs.dicts.reads")
    except ImportError:
        raise('Current engine not found!')
    check_sets_common = True
    current_sets = read_nodes.list_non_default_set()
    common = cmds.ls(COMMON_GRP, type="transform")[0]
    set_dict = {}
    for s in current_sets:
        set_dict[s] = cmds.sets(s, q=True)
    multiple_sets = []
    repeats = common_read_dicts.get_dict_value_repeat(set_dict)
    for key, value in repeats.items():
        if value > 1:
            multiple_sets.append(key)
    common_members = cmds.listRelatives(common, fullPath=True, c=True)
    for mul in multiple_sets:
        members = read_nodes.list_set_members(mul)
        if members:
            for memb in members:
                if memb not in common_members:
                    logger.error('Element %s // not in Common!!' % memb)
                    check_sets_common = False
        else:
            logging.info('No element in common')
    return check_sets_common


# TODO: snakecase variationDict
def check_assets_sets(variationDict, step_name, logger=logging):
    """
    Used in Masterscene
    True if selection Sets have the right naming //var/ subassets
    :param: variationDict
    :param: step_name
    :return: check_sets
    :rtype: boolean
    """
    check_sets = True

    # Check to avoid empty sets
    non_defaut_sets = read_nodes.list_non_default_set()
    for set_found in non_defaut_sets:
        if not cmds.sets(set_found, q=True):
            check_sets = False
            logger.error("{} selection set is empty !".format(set_found))

    variation_sub_dict = variationDict
    variation_sub_sets_dict = {}
    variation_list = [key + "_{}_{}".format(MDL_STEP_SN, SPLIT_SET_SUFFIX) for key in variationDict]
    current_sets = read_nodes.list_non_default_set()

    if MASTER_ROOT_SET in current_sets:
        variations_sets = cmds.sets(cmds.ls(MASTER_ROOT_SET, sets=True)[0], q=True)
        variations_sets.sort()
        variations_sets.sort()
        if variations_sets != variation_list:
            logger.error("Variation List and selections sets are not the same!")
            check_sets = False
        else:
            for variation_set in variations_sets:
                subs_assets = cmds.sets(variation_set, q=True)
                if subs_assets:
                    variation_sub_sets_dict[variation_set] = subs_assets
                else:
                    # if the set is empty, the check is failed
                    logger.error("Variation %s set is empty!" % variation_set)
                    check_sets = False
                    return check_sets
            for var, subassets in variation_sub_dict.items():
                set_name = "{var}_{step}_{splitset}".format(var=var, step=step_name, splitset=SPLIT_SET_SUFFIX)
                if set_name not in current_sets:
                    logger.error("Variation %s is not present in current sets" % var)
                    check_sets = False
                set_children = cmds.sets(set_name, q=True)
                for sub in subassets:
                    set_name = "{var}_{step}_{splitset}".format(var=sub, step=step_name, splitset=SPLIT_SET_SUFFIX)
                    if set_name not in set_children:
                        logger.error("Subasset %s of %s is not present in current sets" % (sub, var))
                        check_sets = False

            return check_sets


# ________________________________________________________________________________________________________
##########################
# ------ HISTORY --------#
##########################

def check_history(mesh, logger=logging):
    """
    Return true / false if mesh has history
    :param: mesh
    :return: check_hist
    :rtype: boolean
    """
    check_hist = True
    shape = read_nodes.get_shape_or_transform(mesh)
    shape = cmds.ls(shape, sn=True)
    history = cmds.listHistory(mesh, lv=0)
    history = [h for h in history if h not in shape]
    if history:
        check_hist = False
    return check_hist


def check_skin_on_mesh(mesh, logger=logging):
    """
    Check if skin exists on mesh
    :param: mesh
    :return: any node with hist
    :rtype: boolean
    """
    hist = cmds.listHistory(mesh, lv=0)
    return any("skinCluster" in cmds.nodeType(node) for node in hist)


# ________________________________________________________________________________________________________
##########################
# ----- ATTRIBUTS -------#
##########################

# TODO: snakecase attrName
def check_mesh_attr(mesh, attrName):
    """
    Check if custom attribut is present and return value
    :param: mesh
    :param: attrName
    :return: attrib_value
    :rtype: string or None
    """
    attr_mesh = '{}.{}'.format(mesh, attrName)
    if cmds.attributeQuery(attrName, node=mesh, exists=True):
        attrib_value = cmds.getAttr(attr_mesh)
        if not attrib_value:
            attrib_value = None
    return attrib_value


# TODO: clean comment
def check_visbility(mesh, logger=logging):
    """
    Check if shape has visibility ON
    Correct the visibility
    :param: mesh
    :return: check_visib
    :rtype: boolean
    """
    check_visib = True
    if type(mesh) == list:
        mesh = mesh[0]
    visibility = cmds.getAttr(mesh + ".visibility")
    if visibility is False:
        check_visib = False
        # logger.info('OBJECT HAVE BEEN DISPLAYED {}'.format(mesh))
        # cmds.setAttr(mesh+".visibility", True)
    return check_visib


def check_is_freeze_transf(mesh, logger=logging):
    """
    Return true / false if mesh has transform values
    :param: mesh
    :return: check_ft
    :rtype: boolean
    """
    check_ft = True
    dico_transf = read_nodes.get_transform_info([mesh])[mesh]
    attr_ = dico_transf['t'] + dico_transf['r']
    attr_scale = dico_transf['s']
    for att in attr_:
        if att != 0:
            check_ft = False
    for att in attr_scale:
        if att != 1:
            check_ft = False
    return check_ft


def check_render_stats(mesh, logger=logging):
    """
    Check render stats of mesh. Must have:
        - Cast Shadows: ON
        - Receive Shadows: ON
        - Hold Out: OFF
        - Motion Blur: ON
        - Primary Visibility: ON
        - Smooth Shading: ON
        - Visible in Reflections: ON
        - Visible in Reflractions: ON
        - Double Sided: ON
    Only check, wont correct it if not good.
    :param: mesh
    :return: correct_rs
    :rtype: boolean
    """
    correct_rs = True
    shape = read_nodes.get_shape_or_transform(mesh)
    attrb_on = [
        "castsShadows",
        "receiveShadows",
        "motionBlur",
        "primaryVisibility",
        "smoothShading",
        "visibleInReflections",
        "visibleInRefractions"]
    attrb_off = [
        "holdOut",
    ]
    if type(shape) == list:
        shape = shape[0]
    for attr in attrb_on:
        if cmds.getAttr(shape + "." + attr) is False:
            correct_rs = False
            # logger.info('ATTRIBUTE HAS BEEN REINIT {}'.format(attr))
            # cmds.setAttr(shape+"."+attr, True)
    for attr in attrb_off:
        if cmds.getAttr(shape + "." + attr) is True:
            correct_rs = False
            # logger.info('ATTRIBUTE HAS BEEN REINIT {}'.format(attr))
            # cmds.setAttr(shape+"."+attr, False)
    return correct_rs


def check_version(mesh, logger=logging):
    """
    Check if custom attrb source on mesh is the last version
    Attr SOURCE_ATTR is only used in MasterScene for ELT element which are import and not referenced
    :param: mesh
    :return: check_version
    :rtype: boolean
    """
    check_version = True
    source_path = check_mesh_attr(mesh=mesh, attrName=SOURCE_ATTR)
    if not source_path:
        # logger.warning("Mesh {} has not custom source attr".format(mesh))
        check_version = False
    else:
        last_version = read_scene.get_latest_scene(file_path=source_path)
        if last_version != source_path:
            # logger.warning("Mesh %s doesnt point to latestest scene!!" % mesh)
            check_version = False
    return check_version


# ________________________________________________________________________________________________________
##########################
# -------- POLY ---------#
##########################

def check_clean_up(mesh, logger=logging):
    """
    Check if mesh passes clean up
    :param: mesh
    :return: check_clean_up
    :rtype: boolean
    """
    check_clean_up = True
    if cmds.polyInfo(mesh, nonManifoldEdges=True) is False:
        check_clean_up = False
    if cmds.polyInfo(mesh, laminaFaces=True) is False:
        check_clean_up = False
    if cmds.polyInfo(mesh, invalidEdges=True) is False:
        check_clean_up = False
    if cmds.polyInfo(mesh, invalidVertices=True) is False:
        check_clean_up = False
    return check_clean_up


# TODO: snakecase
def check_polyColorSet(mesh, logger=logging):
    """
    Check poly color set on mesh
    :param: mesh
    :return: clean_pcs
    :rtype: boolean
    """
    clean_pcs = True
    nb_vtx = read_nodes.get_nb_of_component_of_mesh(meshElement=mesh, co_type="vtx")
    idx_vtx = 1
    while idx_vtx <= nb_vtx:
        try:
            result = cmds.polyColorPerVertex(mesh + ".vtx[{}]".format(idx_vtx), query=True, r=True, g=True, b=True)
        except Exception as e:
            result = [0, 0, 0]
            print e
        for num in result:
            if num > 0:
                clean_pcs = False
        idx_vtx += 1
    return clean_pcs


def check_n_gones(mesh, logger=logging):
    """
    Check Ngones polygones, return if mesh has non_quads
    :param: mesh
    :return: check_polys
    :rtype: bool
    """
    check_polys = True
    cmds.select(mesh)
    cmds.polySelectConstraint(m=3, t=8, sz=3)  # to get N-sided
    nb_ngones = cmds.polyEvaluate()["faceComponent"]
    cmds.polySelectConstraint(m=0)
    if nb_ngones != 0:
        logger.error("Ngone(s) found on " + mesh)
        check_polys = False
    return check_polys


# TODO: Optimization - since at least *one* check is enough to return false, consider
# having the check right after the query at the nodes, and if it's false return immediately.
# Like this we avoid unnecessary scene searches.
# Example:
# """
#     nb_face = read_nodes.get_nb_of_component_of_mesh(meshElement=mesh, co_type="face")
#     if nb_face < 1:
#         return False
#     # then continue with the rest of the checks.
# """
def check_geo_size(mesh, logger=logging):
    """
    Check if mesh has at least one face, 4 vtx, 4 edges
    :param: mesh
    :return: check_geo
    :rtype: boolean
    """
    check_geo = True
    nb_face = read_nodes.get_nb_of_component_of_mesh(
        meshElement=mesh, co_type="face")
    nb_vtx = read_nodes.get_nb_of_component_of_mesh(
        meshElement=mesh, co_type="vtx")
    nb_edge = read_nodes.get_nb_of_component_of_mesh(
        meshElement=mesh, co_type="edge")
    if nb_face < 1:
        check_geo = False
    if nb_vtx < 4:
        check_geo = False
    if nb_edge < 4:
        check_geo = False
    return check_geo


# ________________________________________________________________________________________________________
##########################
# ------- OTHERS --------#
##########################

def check_is_instanced(mesh, logger=logging):
    """
    Return false is shape is instanced
    :param: mesh
    :return: check_instance
    :rtype: boolean
    """
    check_instance = True
    shape = read_nodes.get_shape_or_transform(mesh)
    if len(cmds.listRelatives(shape, ap=True) or []) > 1:
        check_instance = False
    return check_instance


def check_double_shape(mesh, logger=logging):
    """
    Check if mesh has double shape
    :param: mesh
    :return: no_double
    :rtype: boolean
    """
    no_double = True
    shapes = cmds.listRelatives(mesh, shapes=True, fullPath=True)
    if len(shapes) > 1:
        no_double = False
    return no_double
