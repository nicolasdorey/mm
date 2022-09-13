# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#                       Nicolas Dorey
#
#   DESCRIPTION :       Shaders checks lib
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging

try:
    import maya.cmds as cmds
except ImportError:
    pass

from ..reads import shaders as read_shaders
from ..reads import nodes as read_nodes


def check_materials(logger=logging):
    """
    Check if scene has non default mtl
    :return: mat
    :rtype: list
    """
    mat = read_shaders.list_materials()
    if len(mat) != 0:
        logger.error("Materials found: {}".format(mat))
    return mat


def is_displacement(shape):
    """
    Return True or False if displacementShader connected to shadingEngine
    It does not work with initialShadingGroup connection
    :param: shape
    :return: True or False
    :rtype: boolean
    """
    shading_engine_name = cmds.listConnections(shape, type="shadingEngine")
    if shading_engine_name:
        if len(shading_engine_name) > 1:
            logging.error('More than one Shading Engine found on shape "{}"'.format(shape))
        else:
            disp_co = cmds.listConnections('{}.displacementShader'.format(shading_engine_name[0]))
            if disp_co:
                return True
            else:
                return False


def check_face_assignation(mesh):
    """
    Check if mesh has face assignation
    :param: mesh
    :return: assigned_face_sg, True if mesh has face assignations
    :rtype: boolean
    """
    all_sg = cmds.ls(type='shadingEngine')
    faces = read_nodes.get_nb_of_component_of_mesh(mesh, co_type="face")
    assigned_face_sg = False
    for sg in all_sg:
        for f in range(faces):
            if cmds.sets(mesh + ".f[{}]".format(f), isMember=sg):
                assigned_face_sg = True

    return assigned_face_sg


def check_file_mode(file):
    """
    Check if file is in raw
    :param: file
    :return: check_color_space
    :rtype: boolean
    """
    check_color_space = True
    mode = cmds.getAttr("{}.colorSpace".format(file))
    if mode != "Raw":
        check_color_space = False
    return check_color_space


def check_negatives_udims(mesh):
    """
    True if mesh has negatives udim
    :parama: mesh
    :return: check_uv_pos
    :rtype: boolean
    """
    uvs = read_nodes.get_nb_of_component_of_mesh(mesh, co_type="uv")
    check_uv_pos = False
    if uvs:
        for u in range(uvs):
            uv_pos = cmds.polyEditUV("%s.map[%d]" % (mesh, u), q=1)
            uv_pos_u = int(uv_pos[0])
            uv_pos_v = int(uv_pos[1])
            if uv_pos_u < 0:
                check_uv_pos = True
            if uv_pos_v < 0:
                check_uv_pos = True
    return check_uv_pos


def check_upper_udims(mesh):
    """
    True if mesh has vertical udims
    :param: mesh
    :return: check_uv_pos
    :rtype: boolean
    """
    uvs = read_nodes.get_nb_of_component_of_mesh(mesh, co_type="uv")
    check_uv_pos = False
    if uvs:
        for u in range(uvs):
            uv_pos = cmds.polyEditUV("%s.map[%d]" % (mesh, u), q=1)
            uv_pos_v = int(uv_pos[1])
            if uv_pos_v > 1:
                check_uv_pos = True
    return check_uv_pos


# FIXME: Important! this will never work because it's not a method (it misses the `()`) and also no args passed
# => get_sss_shaders() funtion has been moved to "C:\Shotgun\tk-framework-maya\python\studio\libs\reads\shaders.py"
def check_sss_materials(logger=logging):
    """
    Warning if Redshift material has subsurface scattering
    """
    if get_sss_shaders:
        logger.warning("Shaders with SSS :{}".format(get_sss_shaders))


def check_unauth_sh_nodes(logger=logging):
    """
    True if scene has unauthorized shading nodes
    :return: True or False if there is a least one forbidden node
    :rtype: boolean
    """
    forbidden_nodes = [
        "RedshiftNormalMap",
        "RedshiftDisplacement",
        "RedshiftColorCorrection"
    ]
    return any(cmds.objectType(node) in forbidden_nodes for node in cmds.ls())


def check_ior_values(logger=logging):
    """
    True if fresnel have ior value checked
    :return: check_ior
    :rtype: boolean
    """
    check_ior = False
    fresnels = cmds.ls(type="RedshiftFresnel")
    if fresnels:
        for fr in fresnels:
            if cmds.getAttr("{}.fresnel_useior".format(fr)) == 1:
                logger.warning('Fresnel : {} has Use ior Checked!'.format(fr))
                check_ior = True
    return check_ior


def check_lambert_co(logger=logging):
    """
    True if Lambert1 has connections
    :return: check_lamn
    :rtype: boolean
    """
    check_lamb = False
    lambert = cmds.ls('lambert1')[0]
    conn = cmds.listConnections(lambert)
    defauts = read_nodes.list_default_nodes()
    for co in conn:
        if co not in defauts:
            logger.warning('Lambert1 has input connections!')
            check_lamb = True
    return check_lamb
