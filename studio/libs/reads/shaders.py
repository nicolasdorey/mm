# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Utils for shaders queries
#
#   Update  1.0.0 :     We start here.
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

from . import nodes as read_nodes
from . import references as read_references


SHADERS_TYPE = [
    'lambert',
    'RedshiftMaterial',
    'RedshiftDisplacement',
    'RedshiftSubSurfaceScatter',
    'RedshiftMaterialBlender'
]


def get_bbs_displacement(shape):
    """
    :param: shape
    :return a list of Bounding Box Scale displacement of a shape
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


def list_shading_groups():
    """
    Get all shading groups / shading engine
    :return: list of non default shaders in scene
    :rtype: list
    """
    all_shading_groups = cmds.ls(et='shadingEngine')
    # et : Exact type ,List all objects of the specified type
    return read_nodes.non_default_nodes_only(all_shading_groups)


# TODO: snakecase
def get_shader_from_shape(myShape):
    """
    :param: myShape
    :return a list a the shader(s) connected to myShape
    :logging: if more than 1 shader found: logging.warning
    :rtype: list
    """
    materials_to_return = []
    shading_group_connection = cmds.listConnections(myShape, t='shadingEngine')
    for shading_group in shading_group_connection:
        sg_connections_list = cmds.listConnections(shading_group)
        for sg_co in sg_connections_list:
            if sg_co in list_materials():
                materials_to_return.append(sg_co)
    # if len(materials_to_return) > 1:
    #     logging.warning("There are {} connected to {}.".format(len(materials_to_return), myShape))
    return materials_to_return


# TODO: snakecase shapeSelection
def list_materials(shapeSelection=None):
    """
    This function lists all non default materials
    Or non default materials connected to shapeSelection
    :param: shapeSelection => can be a list or unique element, None by default
    :rtype: list
    """
    list_all_materials = cmds.ls(mat=True)
    # mat : materials [boolean] [] List materials or shading groups.
    materials_to_return = []
    if shapeSelection:
        # Is a list ?
        if 'list' in str(type(shapeSelection)):
            for element in shapeSelection:
                materials_to_return = get_shader_from_shape(element)
        # Is a unique element
        else:
            materials_to_return = get_shader_from_shape(shapeSelection)
    else:
        materials_to_return = list_all_materials
    return read_nodes.non_default_nodes_only(materials_to_return)


def get_assigned_materials():
    """
    Get assigned materials on mesh
    :return: materials
    :rtype: list
    """
    materials = []
    for shading_engine in cmds.ls(type='shadingEngine'):
        if cmds.sets(shading_engine, q=True):
            for material in cmds.ls(cmds.listConnections(shading_engine), materials=True):
                materials.append(material)
    return materials


def get_shading_group(shader):
    """
    Get shading group from shader
    Adapted from masternull
    :param: shader
    :return: sh_grp
    :rtype: string
    """
    if shader:
        if cmds.objExists(shader):
            sh_grp = cmds.listConnections(shader, d=True, et=True, t='shadingEngine')
            if sh_grp:
                return sh_grp[0]
            else:
                sh_grp = None
    return sh_grp


# TODO: snakecase args
def assign_shader(objList, shader, connectSurfaceMat=False):
    """
    Assign the shader to the object list
    :param: objList => list of objects
    :param: shader
    :param: connectSurfaceMat => False by default
    """
    shading_grp = get_shading_group(shader=shader)
    if objList:
        if shading_grp:
            cmds.sets(objList, e=True, forceElement=shading_grp)
            if connectSurfaceMat:
                if shader not in cmds.listConnections(shading_grp + ".surfaceShader"):
                    try:
                        cmds.connectAttr(shader + ".outColor", shading_grp + ".surfaceShader", f=True)
                    except Exception as e:
                        logging.warning('{} // Could connect attribute in shading grp ! {}'.format(e, shading_grp))
        else:
            logging.info('Could get a shading group')


# TODO: snakecase
def reassign_shaders(dict_shdr, shdrType):
    """
    Reassign shaders from dictionnary of assignations (stored in topnode)
    :param: dict_shdr
    :param: shdrType
    """
    rs_surface_shader = "rsSurfaceShader"
    for shading_grp, sg_dict in dict_shdr.items():
        if "transforms_names" in sg_dict.keys():
            transforms = sg_dict['transforms_names']
            cmds.sets(transforms, e=True, forceElement=shading_grp)
            if cmds.attributeQuery(rs_surface_shader, node=shading_grp, exists=True):
                shaders = cmds.listConnections(shading_grp + "." + rs_surface_shader)
                if shaders:
                    shader = shaders[0]
                    if shdrType in cmds.objectType(shader):
                        cmds.connectAttr(shader + ".outColor", shading_grp + ".surfaceShader", f=True)

        else:
            raise ValueError('Shading group dictionnary has not tranforms key!')


# TODO:snakecase
def get_file_texture_infos(shader=False, filesList=None):
    """
    Get the path of the file texture in scene or filesList
    Get the shaders connections if needed
    :param: shader => boolean, True: if you want the name of connected shaders
    :param: filesList => list of files nodes,
    :return: dict_to_return =>{u'myTextureNode': [u'myTexturePath/myTexture.tx', [u'myShader1, myShader2']]}
    if shader=False: {u'myTextureNode': [u'myTexturePath/myTexture.tx']}
    :rtype: dict
    """
    dict_to_return = {}
    if not filesList:
        file_texture_list = cmds.ls(et='file')
    else:
        file_texture_list = filesList
    for file_found in file_texture_list:
        current_shader = cmds.listConnections("{}.outColor".format(file_found))
        current_file = cmds.getAttr("{}.fileTextureName".format(file_found))
        if shader is True:
            dict_to_return[file_found] = [current_file, current_shader]
        else:
            dict_to_return[file_found] = [current_file]
    return dict_to_return


# FIXME: return nothing! Or delete if not used
def traverse_co(node, children):
    """
    List recursivly connections in shader
    Populate dict with all connections
    :param: node
    :param: children
    :rtype: dict
    """
    connections = cmds.listConnections(node, source=True, destination=False, skipConversionNodes=True) or {}
    for child in connections:
        children[child] = {}


# TODO: use different names for arg and return
def get_nodes_of_shdr(node, children):
    """
    Returns all connections of shader
    :param: node
    :param: children
    :return: children
    :rtype : dict (nested)
    """
    traverse_co(node, children)
    for child in children:
        get_nodes_of_shdr(child, children[child])
    return children


# TODO: snakecase
# TODO: use different names for arg and return
def populate_nodeType(nested_dict, nodeType, nodesFound):
    """
    Returns list of files in shader
    :param: nested_dict => dict with all values found of connections
    :param: nodeType
    :param: nodesFound => list of files found
    :return: nodesFound
    :rtype: list
    """
    for key, value in nested_dict.items():
        if type(value) is dict:
            populate_nodeType(value, nodeType=nodeType, nodesFound=nodesFound)
        # Populate list if actual node is a file
        if cmds.objectType(key) == nodeType:
            nodesFound.append(key)
    return nodesFound


# TODO:snakecase
def list_nodeType_of_shader(shader, nodeType):
    """
    Get list of type connected to shader
    :param: shader
    :param: nodeType
    :return: nodes_found
    :rtype: list
    """
    children = {}
    nodes = get_nodes_of_shdr(shader, children)
    nodes_found = populate_nodeType(nodes, nodeType=nodeType, nodesFound=[])
    nodes_found = list(set(nodes_found))
    return nodes_found


# TODO:snakecase
def get_mesh_shader(mesh, shdrType="Redshift"):
    """
    Get redshift shader of mesh
    :param: mesh
    :param: shdrType => specifies another type, for eg Lambert
    :return: rs_shd
    :rtype: string
    """
    shape = read_nodes.get_shape_or_transform(mesh)
    shdr = get_shader_from_shape(shape)
    rs_shd = ""
    for shd in shdr:
        if shd:
            if cmds.objectType(shd).startswith(shdrType):
                rs_shd = shd
    return rs_shd


def get_objects_of_shader(shader):
    """
    Get objects that have the shader assigned on them
    :param: shader
    :return: objects_assigned
    :rtype: list
    """
    shading_grp = get_shading_group(shader=shader)
    return cmds.sets(shading_grp, query=True)


# TODO: snakecase
# FIXME: unused shapes and shadingGrp! Clean this method!
def get_shaders_assignation(myShaders=None):
    """"
    Returns dict with assignations {shader1: [shape1,shape2]}
    Long name only
    :param: myShaders => None by default
    """
    # FIXME: unused shapes var!
    shapes = read_nodes.list_all_shapes()
    if myShaders:
        shaders = myShaders
    else:
        shaders = list_materials()
    shdr_ass = {}
    for sh in shaders:
        cmds.select(cl=True)
        # FIXME: unused shadingGrp var!
        shadingGrp = get_shading_group(shader=sh)
        objects = cmds.ls(get_objects_of_shader(shader=sh), long=True)
        if objects:
            # removing namespaces
            # TODO : improve
            if ":" in sh:
                sh = sh.split(":")[-1]
            idx = 0
            for obj in objects:
                if ":" in obj:
                    objects[idx] = obj.split(":")[-1]
                idx += 1
            shdr_ass[sh] = objects
        cmds.select(cl=True)
    return shdr_ass


def get_lambert_attr_values(lambert):
    """
    Return dict with attribute names and values.
    Ex: {'color': [0.16, 0.6, 0.11], 'transparency': [0.0, 0.0, 0.0]}
    :param: lambert => string, the name of the lambert to store attribute values
    :return: attribute names and values
    :rtype: dict
    """
    # For color and transparency, we round to 3 digits
    color = [round(col, 3) for col in cmds.getAttr(lambert + '.color')[0]]
    transparency = [round(col, 3) for col in cmds.getAttr(lambert + '.transparency')[0]]
    return {'color': color, 'transparency': transparency}


def get_attr_values(shader):
    """
    Return a dict with attribute names and values depending on the shader type.
    :param: shader => string, the name of the shader to store attribute names and values
    :return: attribute names and values
    :rtype: dict
    """
    if cmds.objectType(shader) == 'lambert':
        return get_lambert_attr_values(shader)
    else:
        return {}


# TODO:snakecase
def get_shading_grp_assignations(myShadingGrps=None):
    """
    Returns dict with shading group assignations and specific shader attribute values
    Ex: {
            {
                "Alga05_Classic_Alga_01_ShSG": {
                    "shaders": {
                        "Alga05_Classic_Classic_Alga_01_Vp": {
                            "color": [0.402, 0.06, 0.033],
                            "transparency": [0.0, 0.0, 0.0],
                        },
                        "Alga05_Classic_Classic_Alga_01_Sh": {},
                    },
                    "transforms_names": [
                        u"|Alga05_Classic_MDL_Top|U_Seaweed01_001_Msh",
                        u"|Alga05_Classic_MDL_Top|U_Seaweed01_002_Msh",
                    ],
                }
            }
        }
    :param: myShadingGrps => specific shading groups to process, defaults to None
    :type: list, optional
    :return: shading group assignations and shader attribute values
    :rtype: dict
    """
    # Get shading groups
    if myShadingGrps:
        all_shading_engines = myShadingGrps
    else:
        all_shading_engines = cmds.ls(type='shadingEngine')
    # Loop over shading engines
    my_dict = {}
    shading_engines = read_nodes.non_default_nodes_only(all_shading_engines)
    for shading_engine in shading_engines:
        shaders_dict = {}
        my_transform = []
        connections_tmp = cmds.listConnections(shading_engine)
        shading_engine_connections = cmds.ls(connections_tmp, long=True)
        # Loop over shading engine connections
        for sg_tmp in shading_engine_connections:
            object_type = cmds.objectType(sg_tmp)
            # If shader store shader attribute names and values
            if object_type in SHADERS_TYPE:
                shading_engine_connection = read_references.remove_ns_in_longname(sg_tmp)
                shaders_dict[shading_engine_connection] = get_attr_values(shading_engine_connection)
            # If transform store shading engine assignation
            if object_type == 'transform':
                shading_engine_connection = read_references.remove_ns_in_longname(sg_tmp)
                my_transform.append(shading_engine_connection)
        # Update dict
        my_dict[shading_engine] = {'shaders': shaders_dict, 'transforms_names': my_transform}
    return my_dict


# TODO:snakecase
def list_shader_type(shdrType, myShaders=None):
    """
    List shaders of given type
    :param: myShaders => list to filter
    :param: shdrType => type of shdr to get. For ex: lambert
    :return: matching_shd
    :rtype: list
    """
    shaders = list_materials()
    matching_shd = []
    if myShaders:
        shaders = myShaders
    for shd in shaders:
        current_shd_type = cmds.objectType(shd)
        if shdrType in current_shd_type:
            matching_shd.append(shd)
    return matching_shd


# TODO:snakecase
def get_shading_network(shadersList):
    """
    Get LIST of shading network of shaders, shading group included
    :param: shadersList => list of shaders maya
    :return: shadingNetwork => all nodes inside the shaders'
    :rtype : list
    """
    # Import module by using current engine to get tk-framework-common throw tk-multi-accessor
    try:
        current_engine = sgtk.platform.current_engine()
        fw_common = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-common')
        common_update_dicts = fw_common.import_module("studio.libs.dicts.updates")
    except ImportError:
        raise('Current engine not found!')
    shading_network = []
    # Get connections of shaders
    for sh in shadersList:
        # Get shading grp
        try:
            sh_grp = cmds.listConnections(sh, type="shadingEngine")
            shading_network += sh_grp
        except Exception as e:
            logging.error(e)
            pass
        try:
            # Get dict of shaders' connections
            shading_network_dict = get_nodes_of_shdr(node=sh, children={})
            # Convert to list
            converted_sh_ntw = common_update_dicts.convert_dict_to_flat_list(dictionary=shading_network_dict)
            shading_network += converted_sh_ntw
        except Exception as e:
            logging.error('Could not get nodes of shader: {}"'.format(e))
    return shading_network


def get_empty_files(shader):
    """
    :param: shader
    :return: empty_files
    :rtype: list
    """
    empty_files = []
    files_of_shader = list_nodeType_of_shader(shader=shader, nodeType='file')
    for file in files_of_shader:
        current_file = cmds.getAttr("{}.fileTextureName".format(file))
        if not current_file:
            empty_files.append(file)
    return empty_files


def get_sss_shaders(mtls):
    """
    Get shaders that have sss.
    :param: mtls => materials to look at
    :return: sss_shrs => shaders list which have SSS
    :rtype: list
    """
    sss_shrs = []
    for mtl in mtls:
        if cmds.objectType(mtl) == "RedshiftMaterial":
            # sss amount
            attr = mtl + ".ms_amount"
            ms = cmds.getAttr(attr)
            if ms > 0:
                sss_shrs.append(mtl)
    return sss_shrs
