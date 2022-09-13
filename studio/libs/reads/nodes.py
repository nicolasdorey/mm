# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie #
#
#   DESCRIPTION :       Utils for nodes queries
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
except ImportError:
    pass


# ________________________________________________________________________________________________________
##########################
# -------- DAG ----------#
##########################

def list_dag_assets(maya_type=None):
    """
    Return a list of dag assets from maya_type
    :param: maya_type => None by default
    :return: non_default_nodes_only(list_all)
    :rtype: list
    """
    list_all = []
    if maya_type is None:
        list_all = cmds.ls(long=True, dag=True)
        # l : long [boolean] [] Return full path names for Dag objects.
        # By default the shortest unique name is returned.
        # dag : dagObjects [boolean] [] List Dag objects of any type.
        # If object name arguments are passed to the command then this
        # flag will list all Dag objects below the specified object(s).
    else:
        list_all = cmds.ls(long=True, dag=False, et=maya_type)

    return non_default_nodes_only(list_all)


# Unused
def list_non_dag_assets():
    """
    l: long [boolean] [] Return full path names for Dag objects.
    # By default the shortest unique name is returned.
    # dag : dagObjects [boolean] [] List Dag objects of any type.
    # If object name arguments are passed to the command then this
    # flag will list all Dag objects below the specified object(s).
    :return: non dag assets list
    :rtype: list
    """
    list_non_dag_assets_only = []
    list_all = cmds.ls(long=True, dag=False)
    for elt in non_default_nodes_only(list_all):
        if elt not in list_dag_assets():
            list_non_dag_assets_only.append(elt)

    return list_non_dag_assets_only


# ________________________________________________________________________________________________________
##########################
# --- DEFAULT OR NOT ----#
##########################

# TODO: rename to "get_non_default_nodes_only"
def non_default_nodes_only(list_nodes):
    """
    List of nodes must be by default LONG names!
    :param: list_nodes
    :return: non default nodes in list
    :rtype: list
    """
    list_non_default_nodes_only = []
    default_nodes = list_default_nodes()
    default_cams = list_default_cams_maya()
    for elt in list_nodes:
        if elt not in default_cams:
            if elt not in default_nodes:
                list_non_default_nodes_only.append(elt)
    return list_non_default_nodes_only


def list_default_nodes():
    """
    dn : defaultsNodes [boolean] [] Returns defaults nodes,
    which are nodes that stay in the Maya session after a file > new.
    These are a special class of default nodes that do not get reset on file
    > new. Ex: itemFilter and selectionListOperator nodes.
    Some default nodes in our scene are not listed by dn, see default_hardcoded_nodes + list_default_cams_maya()
    :return: default nodes
    :rtype: list
    """
    default_hardcoded_nodes = [
        'lightLinker1',
        'shapeEditorManager',
        'poseInterpolatorManager',
        'layerManager',
        'defaultLayer',
        'renderLayerManager',
        'defaultRenderLayer',
        'uiConfigurationScriptNode',
        'sceneConfigurationScriptNode',
        'shapeEditorManager1',
        'poseInterpolatorManager1'
    ]
    default_maya_nodes = cmds.ls(dn=True) + list_default_cams_maya() + default_hardcoded_nodes
    return default_maya_nodes


# ________________________________________________________________________________________________________
##########################
# --------MESHES---------#
##########################

# TODO: snakecase
def list_all_shapes(nodeList=None):
    """
    :param: nodeList => None by default
    :return: all_shapes => list of shapes longname found in nodeList / found in scene
    :rtype: list
    """
    if not nodeList:
        all_shapes = cmds.ls(exactType='mesh', dag=1, ni=1, long=True)
    else:
        all_shapes = []
        for node in nodeList:
            if cmds.objectType(node) == 'mesh':
                all_shapes.append(cmds.ls(node, long=True)[0])
    return all_shapes


# TODO: snakecase
def list_all_meshes(nodeList=None):
    """"
    :param: nodeList => None by default
    :return: all_meshes => list of meshes longname found in nodeList / found in scene
    :rtype: list
    """
    if not nodeList:
        all_shapes = list_all_shapes()
        all_meshes = [cmds.ls(cmds.listRelatives(obj, fullPath=True, p=True)[0], long=True)[0] for obj in all_shapes]
    else:
        all_shapes = list_all_shapes(nodeList)
        all_meshes = [cmds.ls(cmds.listRelatives(obj, fullPath=True, p=True)[0], long=True)[0] for obj in all_shapes]
    return all_meshes


def list_wrong_mesh_names():
    """
    Get the meshes with the name doesnt end with _Msh
    :return: wrong_names
    :rtype: list
    """
    mesh_suffix = 'Msh'
    meshes = list_all_meshes()
    wrong_names = []
    for mesh in meshes:
        if mesh.endswith('_{}'.format(mesh_suffix)) is False:
            wrong_names.append(mesh)
    return wrong_names


def get_shape_or_transform(element):
    """
    Tip: if return = shapes: you should check if return is a string or a list to avoid error
    :param: element
    :if element = shape: return transform: parentFound
    :if element = transform: return shape: shapeFound/listOfShapes
    :if more than one shape found: return a list of shapes [myShape,myShapeOrig...]
    :return: element_to_return
    :rtype: string or list
    """
    element_to_return = None
    if not cmds.listRelatives(element, f=True, ad=True):
        list_rel_parent = cmds.listRelatives(element, f=True, ap=True)
        for parent_found in list_rel_parent:
            if cmds.objectType(parent_found) == "transform":
                element_to_return = parent_found
    else:
        list_rel_descendant = cmds.listRelatives(element, f=True, ad=True)
        list_of_shapes = []
        for shape_found in list_rel_descendant:
            if cmds.objectType(shape_found) == "mesh":
                list_of_shapes.append(shape_found)
                element_to_return = shape_found
        if len(list_of_shapes) > 1:
            element_to_return = list_of_shapes
    return element_to_return


# Unused
# TODO: snakecase
def get_renderstats(myElementList, *args):
    """
    Get renderstats of each mesh from myElementList
    Allows the user to get all renderstats from one object or all objects with a specific renderstat value
    :param: myElementList => must be a list of shapes
    :return: statements_dict_to_return: a dictionary of all the boolean values of render stats from myElementList {myMesh:{stat1:bool, stat2:bool}, }
    :rtype: dict
    """
    render_stats_attr = [
        'castsShadows',
        'receiveShadows',
        'holdOut',
        'motionBlur',
        'primaryVisibility',
        'smoothShading',
        'visibleInReflections',
        'visibleInRefractions',
        'doubleSided',
        'opposite'
    ]
    # Override attr if needed
    if len(args) > 0:
        render_stats_attr = list(args)
    statements_dict_to_return = {}
    for element in myElementList:
        renders_stat_dict = {}
        for render_stats_to_get in render_stats_attr:
            stats_string = '{}.{}'.format(element, render_stats_to_get)
            render_stat_value = cmds.getAttr(stats_string)
            renders_stat_dict[render_stats_to_get] = render_stat_value
        statements_dict_to_return[element] = renders_stat_dict
    return statements_dict_to_return


def get_recursive_meshes(mesh):
    """
    Get all meshes down in hierarchy from one group
    :param: mesh
    :return: meshes_found
    :rtype: list
    """
    meshes_found = []
    current = mesh
    while current:
        current = cmds.listRelatives(current, type="transform", pa=True)
        if current:
            for child in current:
                shape = cmds.listRelatives(child, type="shape", pa=True)
                if shape:
                    meshes_found.append(child)

    return meshes_found


def get_transform_info(myObjectList):
    """
    :param: myObjectList => must be a list of shapes transforms
    :return: dict_to_return =>a dict of myObject x/y/z translate/rotate/scale
    {element: {t: [x,y,z],r:[x,y,z],s[x,y,z]}}
    :rtype: dict
    """
    translateRotateScaleList = ['t', 'r', 's']
    axesList = ['x', 'y', 'z']
    dict_to_return = {}
    for element in myObjectList:
        transformDict = {}
        for transformType in translateRotateScaleList:
            transformValuesList = []
            for axe in axesList:
                whatToCheck = '{}.{}{}'.format(element, transformType, axe)
                if cmds.attributeQuery(transformType + axe, node=element, ex=True):
                    valueFound = cmds.getAttr(whatToCheck)
                    transformValuesList.append(valueFound)
            transformDict[transformType] = transformValuesList
        dict_to_return[element] = transformDict
    return dict_to_return


# TODO rename maybe to get_mesh_orientation()
def get_right_or_left(mesh):
    """
    Check if mesh is right of left to world
    :param: mesh
    :return: side, left of right
    :rtype: string
    """
    side = ""
    # check on center on x
    center = cmds.objectCenter(mesh)[0]
    side = "right" if center < 0 else "left"
    return side


# ________________________________________________________________________________________________________
##########################
# ------POLYCOUNT--------#
##########################

# TODO: snakecase
def get_nb_of_component_of_mesh(meshElement, co_type):
    """
    Get co_type polycount of meshElement
    :param: meshElement
    :param: co_type => vtx, edge, face, uv
    :return: nb_of_elmt
    :rtype: integer value
    """
    if co_type == "vtx":
        nb_of_elmt = cmds.polyEvaluate(meshElement, v=True)
    if co_type == "edge":
        nb_of_elmt = cmds.polyEvaluate(meshElement, e=True)
    if co_type == "face":
        nb_of_elmt = cmds.polyEvaluate(meshElement, f=True)
    if co_type == "uv":
        nb_of_elmt = cmds.polyEvaluate(meshElement, uv=True)

    if type(nb_of_elmt) != int:
        logging.error('NO UVS ON MESH !! : {}'.format(meshElement))
        nb_of_elmt = None
    return nb_of_elmt


# TODO: snakecase
def get_nb_of_component(meshesList, co_type):
    """
    Get co_type polycount of meshesList
    :param: meshesList
    :param: co_type => vtx, edge, face, uv
    :return: compon_of_obj => {meshName:vertexNumber, meshName2:vertexNumber2}
    :rtype: dict
    """
    compon_of_obj = {}
    for mesh in meshesList:
        nb_of_elmt = get_nb_of_component_of_mesh(meshElement=mesh, co_type=co_type)
        compon_of_obj[mesh] = nb_of_elmt
    return compon_of_obj


# Unused
def get_meshes_polycount_dict(meshes_list):
    """
    WIP: Using *args should be a better idea (When done, remove get_nb_of_component_of_mesh from this script)
    Get vertex/edges/faces/uvs polycount of each mesh from meshes_list
    :param: meshes_list => should be a list of mesh transforms
    :return: dict_to_return => a dict of meshes polycount {mesh01:{vtx:999,edge:999,face:999,uv:999}...}
    :rtype: dict
    """
    evaluation_list = ['vtx', 'edge', 'face', 'uv']
    dict_to_return = {}
    for mesh_element in meshes_list:
        value_dict = {}
        for what_to_evaluate in evaluation_list:
            nb_of_elmt = get_nb_of_component_of_mesh(mesh_element, what_to_evaluate)
            value_dict[what_to_evaluate] = nb_of_elmt
        dict_to_return[mesh_element] = value_dict
    return dict_to_return


# _________________________________________________________________________________________________________
# #########################
# -----------UVS----------#
# #########################

def get_udims_list(mesh):
    """
    Returns multiples udims space
    :param: mesh
    :return: all_udims => for ex: 1002,1004
    :rtype: list
    """
    uvs = get_nb_of_component_of_mesh(mesh, co_type="uv")
    pos = []
    if uvs:
        for u in range(uvs):
            uv_pos = cmds.polyEditUV("%s.map[%d]" % (mesh, u), q=1)
            uv_pos_u = int(uv_pos[0]) + 1
            uv_pos_v = int(uv_pos[1]) * 10
            pos.append(1000 + uv_pos_u + uv_pos_v)
    all_udim = list(set(pos))
    all_udim.sort()
    return all_udim


# TODO: snakecase args
# TODO: Make two separate methods: convert_udim_to_uv() convert_uv_to_udim()
def convert_udim(udim=None, uvPos=None):
    """
    Convert udim (1002) to uvPos (1,0) or vice versa
    :param: udim => None by default
    :apram: uvPos => None by default
    :return: u and v positions
    :rtype: 2 int
    """
    if udim:
        u = int(str(udim)[-1])
        v = int(str(udim)[-2])
        if u == 0:
            u = 10
            if v >= 1:
                v -= 1
        elif u <= 9:
            u = u
        u -= 1
        return u, v
    if uvPos:
        uv_pos_u = int(uvPos[0]) + 1
        uv_pos_v = int(uvPos[1]) * 10
        return 1000 + uv_pos_u + uv_pos_v


def return_uvs_from_udims(mesh, udim):
    """
    Return list of uvs components in given udim
    :param: mesh
    :param: udim
    :return: uvNb
    :rtype: list
    """
    uvs = get_nb_of_component_of_mesh(mesh, co_type="uv")
    u, v = convert_udim(udim=udim)
    uv_nb = []
    if uvs:
        for idx_uv in range(uvs):
            uv_pos = cmds.polyEditUV("%s.map[%d]" % (mesh, idx_uv), q=1)
            uv_pos_u = int(uv_pos[0])
            uv_pos_v = int(uv_pos[1])
            if uv_pos_u == u and uv_pos_v == v:
                uv_nb.append("%s.map[%d]" % (mesh, idx_uv))
    if not uv_nb:
        logging.warning('No udim found for mesh : %s' % mesh)
    return uv_nb


#  ________________________________________________________________________________________________________
# #########################
# ---------GROUP----------#
# #########################

# Used "everywhere"
def get_top_node():
    """
    Get top node of scene
    :return: top_node
    :rtype: list
    """
    all_transf = cmds.ls("|*", long=True, typ="transform", r=True)
    default_nodes = non_default_nodes_only(all_transf)
    top_node = default_nodes
    return top_node


def get_prefix(obj_name):
    """
    :param: obj_name
    :return: prefix or None
    :rtype: string or boolean
    """
    pattern_prefix = re.match(r'\w_', obj_name)
    if pattern_prefix is not None:
        prefix = pattern_prefix.group()
        return prefix
    else:
        return None


def get_children_prefix(grp):
    """
    Get prefix of all children. (short name)
    :param: grp
    :return: all_pref_childs : list of all prefix.
    :rtype: list
    """
    childs = cmds.listRelatives(grp, fullPath=True, children=True)
    all_pref_childs = []
    # Get all prefix of children
    for child in childs:
        child = cmds.ls(child, sn=True)[0].split('|')[-1]
        prefix = get_prefix(child)
        all_pref_childs.append(prefix)
    # Remove dupplicate in list; has for ex ["C,"L","R"]
    all_pref_childs = list(dict.fromkeys(all_pref_childs))
    return all_pref_childs


# TODO: childs? => children => rename arg all_pref_childs
def determine_prefix(all_pref_childs):
    """
    Determine what prefix must be for group
    :param: all_pref_childs
    :return: prefix
    :rtype: string
    """
    if len(all_pref_childs) == 1:
        prefix = all_pref_childs[0]
    else:
        if "U_" in all_pref_childs:
            prefix = "U_"
        else:
            prefix = "C_"
    return prefix


def list_all_groups():
    """
    Get groups in scene, except top node.
    :return: all_grps
    :rtype: list
    """
    top_node = get_top_node()
    transfr = cmds.ls(exactType="transform")
    groups = [cmds.ls(grp, long=True)[0] for grp in transfr if is_group(grp)]
    all_grps = [grp for grp in groups if grp not in top_node]
    return all_grps


def is_group(grp, logger=logging):
    """
    Check if node is a group
    :param: grp
    :rtype: boolean
    """
    try:
        children = cmds.listRelatives(grp, children=True)
        for child in children:
            if not cmds.ls(child, transforms=True):
                return False
        return True
    except Exception as e:
        logger.warning(e)
        return False


def is_reference(mesh, logger=logging):
    """
    Check if node is a reference (long name!!)
    :param: mesh
    :rtype: boolean
    """
    refs = cmds.ls(rn=True, long=True)
    if mesh in refs:
        return True
    return False


def get_empty_transf():
    """
    Get empty transform/grp
    :return: empty_grp
    :rtype: list
    """
    transforms = cmds.ls(type='transform')
    empty_grp = []
    for transf in transforms:
        if cmds.nodeType(transf) == 'transform':
            children = cmds.listRelatives(transf, c=True)
            if children is None:
                empty_grp.append(transf)
    return empty_grp


def get_bbs_displacement(shape):
    """
    :param: shape
    :return: bbs_shape_values => list of Bounding Box Scale displacement values
    :rtype: list
    """
    bbs_axes_list = [
        'boundingBoxScaleX',
        'boundingBoxScaleY',
        'boundingBoxScaleZ'
    ]
    bbs_shape_values = []
    for bbs_axe in bbs_axes_list:
        bbs_shape_values.append(cmds.getAttr('{}.{}'.format(shape, bbs_axe)))
    return bbs_shape_values


# ________________________________________________________________________________________________________
##########################
# -------CAMERA----------#
##########################

def list_default_cams_maya():
    """
    :return: default camera
    :rtype: list
    """
    list_default_cams = []
    for c in cmds.ls(long=True, cameras=True):
        if cmds.camera(c, q=True, startupCamera=True):
            cam_transform = cmds.listRelatives(c, p=True, path=True, f=True)
            list_default_cams.append(c)
            list_default_cams.append(cam_transform[0])
    return list_default_cams


def list_non_default_camera(white_list=[]):
    """
    :param: white_list => empty list by default
    :return: non_default_cameras => all non default camera in scene
    :rtype: list
    """
    non_default_cameras = []
    all_cameras = cmds.ls(long=True, cameras=True)
    default_cameras = list_default_cams_maya()
    if white_list:
        default_cameras += white_list

    for camera_in_scene in all_cameras:
        if camera_in_scene not in default_cameras:
            non_default_cameras.append(camera_in_scene)
    return non_default_cameras


# ________________________________________________________________________________________________________
##########################
# --------ANIM-----------#
##########################

def list_animated_nodes():
    """
    :return: all nodes connected to animCurves
    :rtype: list
    """
    animated_elements_list = cmds.ls(type='animCurve')
    result = []
    for animated_element in animated_elements_list:
        if cmds.listConnections(animated_element) is not None:
            if cmds.listConnections(animated_element)[0] not in result:
                result.append(cmds.listConnections(animated_element)[0])
    return result


# ________________________________________________________________________________________________________
##########################
# ---------SET-----------#
##########################

def list_set_members(sel_set):
    """
    List object in selection set.
    Check if not none, and exists, and return long name of objects
    :param: sel_set
    :return: obj_in_set => Return obj (long names) in sets.
    :rtype: list
    """
    obj_in_set = []
    if cmds.objExists(sel_set):
        obj_in_set = cmds.sets(sel_set, q=True)
        if obj_in_set:
            # For long names
            shapes_in_set = cmds.listRelatives(cmds.listConnections('{}.dagSetMembers'.format(sel_set)), f=True)
            if shapes_in_set:
                obj_in_set = [cmds.listRelatives(shape, p=True, f=True)[0] for shape in shapes_in_set]
            else:
                obj_in_set = []
        else:
            obj_in_set = []
    return obj_in_set


def list_non_default_set():
    """
    WIP: find a way to not hardcode default layer
    :return: a list of all non default set in scene
    :rtype: list
    """
    default_sets = [
        "defaultLightSet",
        "defaultObjectSet",
        "initialParticleSE",
        "initialShadingGroup"
    ]
    non_default_sets = []
    all_sets = cmds.ls(set=True)
    for set_found in all_sets:
        if set_found not in default_sets:
            non_default_sets.append(set_found)

    return non_default_sets


# TODO: snakecase
def get_parent_child_sets(setList=None, logger=logging):
    """
    Returns sets that have are parent or child
    :param: setList => None by default
    :return: parents_sets => sets that have children
    :return: child_sets => sets that have no child
    :rtype: 2 lists
    """
    if setList:
        current_sets = setList
    else:
        current_sets = list_non_default_set()
    # Get sets wich are parent of child
    parent_sets = []
    child_sets = []
    for s in current_sets:
        variation_set_content = cmds.ls(list_set_members(s), set=True)
        if variation_set_content:
            parent_sets.append(s)
        else:
            child_sets.append(s)
    return parent_sets, child_sets


# ________________________________________________________________________________________________________
##########################
# -------LIGHTING--------#
##########################

def list_lights():
    """
    List all lights whatever their shape is.
    Works well with maya lights, redshift lights, arnold lights
    :return: a list of all lights shape in scene
    :rtype: list
    """
    lights_in_scene = []
    lights_type_list = cmds.listNodeTypes("light")
    logging.info("Looking for: {}".format(lights_type_list))
    for light_type in lights_type_list:
        lights_from_type = cmds.ls(type=light_type)
        for light_found in lights_from_type:
            if light_found not in lights_in_scene:
                lights_in_scene += cmds.ls(type=light_type, long=True)

    logging.info("Lights found in scene: {}.".format(lights_in_scene))
    return lights_in_scene


# _________________________________________________________________________________________________________
# #########################
# ----------NURBS---------#
# #########################

def list_nurbs():
    """
    :return: a list of all nurbs shape in scene
    :rtype: list
    """
    return cmds.ls(type='nurbsCurve')


# _________________________________________________________________________________________________________
# #########################
# ----------OTHERS--------#
# #########################

def list_unknown_nodes():
    """
    :return: a list of all unknown nodes
    :rtype: list
    """
    return cmds.ls(type=['unknown', 'unknownDag', 'unknownTransform', 'aiStandIn', 'nodeGraphEditorInfo'])
