# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       Detect symetries in scene
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging
from decimal import getcontext
import math
import webbrowser

try:
    import maya.cmds as cmds
    import pymel.core as pm
except ImportError:
    pass

from ....studio.libs.reads import nodes as read_nodes
from ....studio.libs.reads import scene as read_scene
from ....studio.libs.updates import nodes as update_nodes
from ....studio.libs.deletes import nodes as delete_nodes

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

getcontext().prec = 12


def rename_grps():
    """
    Check what childs are in groups, and rename group.

    Rules :
    if only U       => U
    if only C       => C
    if only R OR L  => R or L

    if U + C + L + R => U
    if U + C         => U
    if U + L,R       => U
    if L + R         => C
    if C + L,R       => C
    """
    top_node = read_nodes.get_top_node()[0]
    transfr = cmds.ls(exactType="transform")
    grps = [cmds.ls(grp, long=True)[0]
            for grp in transfr if read_nodes.is_group(grp) and grp not in top_node]
    grps = [grp for grp in grps if grp not in top_node]

    # dict with grp: place in hi
    grp_place = {}

    # groupe to check the futur names / update
    grp_futures_name = {}

    for grp in grps:
        nb = grp.split('|')
        nb = len(nb) - 2
        grp_place[grp] = nb

    for grp in grps:
        grp_futures_name[grp] = grp

    list_grp_place = sorted(
        grp_place.items(), key=lambda x: x[0], reverse=True)

    while len(list_grp_place) > 0:
        for index, elmt in enumerate(list_grp_place):
            grp = elmt[0]
            # take new name
            grp = grp_futures_name[grp]

            try:
                grp_sn = cmds.ls(grp, sn=True)[0]
            except Exception as e:
                list_grp_place.remove(elmt)
                print(e)
                continue

            new_grp_name = update_nodes.correct_grp_prefix(grp_sn)
            if new_grp_name != grp_sn:
                logging.info(
                    "OLD GRP NAME // NEW GRP NAME\n{}\n{} \n\n ".format(grp_sn, new_grp_name))
                # rename grp
                update_nodes.rename_obj(obj=grp_sn, new_name=new_grp_name)

            new_grp_name = cmds.ls(new_grp_name, long=True)[0]
            grp_futures_name[grp] = new_grp_name
            list_grp_place.remove(elmt)

    logging.info('*' * 10 + "END OF GRP RENAME" + "*" * 10)



def rename_with_unique_name():
    """
    Check if after rename, name are dupplicated and correct it
    """
    wrong_names = read_nodes.list_wrong_mesh_names()

    for mesh in wrong_names:
        # get short name and split | in case Toto|Bidule_Msh is returned instead of Bidule_Msh
        mesh = cmds.ls(mesh, sn=True)[0].split('|')[-1]
        final_name = update_nodes.replace_suffixe(mesh)
        update_nodes.rename_obj(obj=mesh, new_name=final_name)

    logging.info('*' * 10 + "END OF UNIQUE RENAME" + "*" * 10)



def check_names_and_rename(meshes, category, *args):
    """
    Rename the meshes with given category, and if its paired if L/R.

    It will rename the meshes with of one of the followed category:
    C : symetrimal meshes to themselves
    LR : two meshes, one left, one right.
    U : unique mesh.

    :param name_meshes : list of all meshes
    :type : name_meshes : maya meshes
    :param category : category of renaming; c, lr, or u
    :param category : string
    :param dict_of_pairs : dict of pairs {mesh01: mesh02} are pairs.
    :param dict_of_pairs : dict
    """
    global dict_of_pairs

    cat_prefix = {"c": "C_", "u": "U_"}
    cat_lr_prefix = {"right": "R_", "left": "L_"}

    if category != "lr":
        good_prefix = cat_prefix[category]
        # for u and c categories
        rename = True
        for mesh in meshes:
            mesh = cmds.ls(str(mesh), sn=True)[0].split('|')[-1]
            prefix = read_nodes.get_prefix(mesh)
            # if there is no prefix
            if prefix is None:
                rename = True
                new_name = mesh.replace(mesh, good_prefix + mesh)
            # if the prefix is wrong
            elif prefix != good_prefix:
                rename = True
                new_name = mesh.replace(prefix, good_prefix)
            # if prefix is correct
            else:
                new_name = mesh
                rename = False
            # at the end, rename only the meshes
            if rename is True:
                update_nodes.rename_obj(obj=mesh, new_name=new_name)

    # for L/R category
    else:
        for mesh, next_mesh in dict_of_pairs.items():
            long_mesh = str(mesh)
            long_next_mesh = str(next_mesh)
            if cmds.objExists(mesh) is False:
                continue
            if cmds.objExists(next_mesh) is False:
                continue
            # get short name
            mesh = cmds.ls(str(mesh), sn=True)[0].split('|')[-1]
            next_mesh = cmds.ls(str(next_mesh), sn=True)[0].split('|')[-1]
            # determine if objects are left or right pos
            if read_nodes.get_right_or_left(long_mesh) == "right":
                right_mesh = mesh
                left_mesh = next_mesh
                long_right = long_mesh
                long_left = long_next_mesh

            else:
                left_mesh = mesh
                right_mesh = next_mesh
                long_right = long_next_mesh
                long_left = long_mesh

            rename_right = True
            rename_left = True

            # check the prefix
            ideal_right_prefix = cat_lr_prefix["right"]
            ideal_left_prefix = cat_lr_prefix["left"]

            right_mesh_prefix = read_nodes.get_prefix(right_mesh)
            left_mesh_prefix = read_nodes.get_prefix(left_mesh)

            # check the letter and replace it for right mesh
            if right_mesh_prefix is not None:
                if right_mesh_prefix != ideal_right_prefix:
                    new_name_right = right_mesh.replace(right_mesh_prefix, ideal_right_prefix)

                # if first letter is right, no changes
                else:
                    new_name_right = right_mesh
                    rename_right = False

            # else add a correct prefix
            else:
                new_name_right = right_mesh.replace(right_mesh, "R_" + right_mesh)

            if left_mesh_prefix is not None:
                if left_mesh_prefix != ideal_left_prefix:
                    new_name_left = left_mesh.replace(left_mesh_prefix, ideal_left_prefix)
                    # prevent conflit names
                # if first letter is right, no changes
                else:
                    new_name_left = left_mesh
                    rename_left = False
            # else add a correct prefix
            else:
                new_name_left = left_mesh.replace(left_mesh, "L_" + left_mesh)

            # rename
            try:
                if rename_right is True:
                    if cmds.objExists(new_name_right):
                        new_name_right = update_nodes.increment_name(new_name_right)
                    pm.rename(long_right, new_name_right)
                if rename_left is True:
                    if cmds.objExists(new_name_left):
                        new_name_left = update_nodes.increment_name(new_name_left)
                    pm.rename(long_left, new_name_left)

            except Exception as e:
                logging.error(e)
                raise ValueError('PROBLEME RENAME WITH {} /{}//{} _ {}//'.format(right_mesh, new_name_right, left_mesh, new_name_left))

    logging.info("*" * 10 + "END OF RENAMING CATEGORY: {}".format(category) + "*" * 10)


def create_dict_of_vtx(mesh, axis):
    """
    Create a dict of vtx number and pos of given axis.
    Ex: {vtx01: 125} where 125 is the pos of for ex x axis.
    :param mesh
    :param axis : given axis.
    :type : int
    :return : distance_of_vertex
    :rtype : dict
    """
    # dict with :
    # {index of vertex : distance from origin}
    distance_of_vertex = {}
    vertices = cmds.polyEvaluate(mesh, v=True)
    # create a dict with each vertex from world 0,0,0
    i = 0
    while i < vertices:
        vertex_pos = cmds.pointPosition(
            mesh + '.pt[{index}]'.format(index=i), w=True)

        vertex_pos_axis = list(vertex_pos)
        vertex_pos_axis = vertex_pos_axis[axis]
        distance_of_vertex[i] = vertex_pos_axis
        i += 1
    return distance_of_vertex


def compare_angles(dict_vtx1, dict_vtx2, dict_axis1, dict_axis2):
    """
    Compare values of 2 dict with vertexes and return percentage of match.
    Function works for one mesh.
    :param dict vtx 1 : (88, 103) where 88 is the vtx number and 103 is the pos in given axis but positive in world.
    :param dict vtx 2 : values of vtx in given axis but negative in world.
    :param dict_axis1 : param of all vtx on other axis number 1
    :param dict_axis2 : param of all vtx on other axis number 2
    :return : percentage
    :rtype : float
    """
    # threshold of substraction between axis
    seuil_symetry = 0.1
    # 5 degrees of threshold
    seuil_angle = 20

    idx_vtx = 0
    comparaison = 0
    # lenght = 0

    lenght = len(dict_vtx1)

    # each vertex, check the vertex of the left list
    while idx_vtx < lenght:
        idx_right = dict_vtx1[idx_vtx][0]
        pos_right = dict_vtx1[idx_vtx][1]

        # index in other dict
        index_neg = 0
        lenght_max = len(dict_vtx2)

        # others values of current vtx (on other axis)
        axis11 = dict_axis1[idx_right]
        axis12 = dict_axis2[idx_right]
        # calcul of angle of current vtx
        angle1 = math.atan2(axis11, axis12) / math.pi * 180

        while index_neg < lenght_max:
            # check the angle difference between current vtx and next
            idx_left = dict_vtx2[index_neg][0]
            pos_left = dict_vtx2[index_neg][1]

            if pos_right > pos_left:
                diff = math.fabs(pos_right + pos_left)
            else:
                diff = math.fabs(pos_left + pos_right)

            # others values of next vtx (on other axis)
            axis21 = dict_axis1[idx_left]
            axis22 = dict_axis2[idx_left]
            # calcul of angle of next vtx
            angle2 = math.atan2(axis21, axis22) / math.pi * 180

            # delta of angle between current and next vtx
            delta_angle = math.fabs(angle1 - angle2)

            # check if values of first axis are matching
            # then check if the delta angle is under the threshold (5 degrees)
            if diff < seuil_symetry:
                # logging.debug('DIFF : {}'.format(diff))
                if delta_angle < seuil_angle:
                    # logging.debug('DELTA ANGLE : {}'.format(delta_angle))
                    # logging.debug('ANGLE 1 et 2 : {} // {}'.format(angle1, angle2))
                    comparaison += 1
                    dict_vtx2.remove(dict_vtx2[index_neg])
                    # refresh lengh of dict
                    lenght_max = len(dict_vtx2)

            index_neg += 1
        idx_vtx += 1

    if len(dict_vtx1) != 0:
        corresp = float((float(100) * float(comparaison)) / len(dict_vtx1))
    else:
        corresp = 0

    # logging.debug('COMPARAISON {}'.format(comparaison))
    # logging.debug('LEN DICT POSTIV {}'.format(len(dict_vtx1)))
    # logging.debug('CORRESPONDANCE ANGLES {}'.format(corresp))
    return corresp


def compare_angles_two_meshes(dict_axis0_msh1, dict_axis0_msh2,
                              dict_axis1_msh1, dict_axis1_msh2,
                              dict_axis2_msh1, dict_axis2_msh2):
    """
    Compare values of 2 dict with vertexes and return percentage of match.

    Function works for TWO meshes. Almost the same as funct compare angles.
    :param dict_axis0_msh1 /dict_axis0_msh2: (88, 103) where 88 is the vtx number
    and 103 is the pos in given axis but positive in world.

    :param dict vtx 2 : values of vtx in given axis but negative in world.
    :param dict_axis1_msh*: param of all vtx on other axis number 1 for mesh01 AND MESH02
    :param dict_axis2_msh* : param of all vtx on other axis number 2 for mesh01 AND MESH02
    :return corresp : percentage of matching.
    :rtype : float
    """
    # threshold of substraction between axis
    seuil_symetry = 0.1
    # 5 degrees of threshold
    seuil_angle = 5

    idx_vtx = 0
    comparaison = 0
    lenght = 0

    lenght = len(dict_axis0_msh1)

    # each vertex, check the vertex of the left list
    while idx_vtx < lenght:
        idx_right = dict_axis0_msh1[idx_vtx][0]
        pos_right = dict_axis0_msh1[idx_vtx][1]

        # index in other dict
        index_neg = 0
        lenght_max = len(dict_axis0_msh2)

        # others values of current vtx (on other axis)
        axis11 = dict_axis1_msh1[idx_right]
        axis12 = dict_axis2_msh1[idx_right]
        # calcul of angle of current vtx
        angle1 = math.atan2(axis11, axis12) / math.pi * 180

        while index_neg < lenght_max:
            # check the angle difference between current vtx and next
            idx_left = dict_axis0_msh2[index_neg][0]
            pos_left = dict_axis0_msh2[index_neg][1]

            if pos_right > pos_left:
                diff = math.fabs(pos_right + pos_left)
            else:
                diff = math.fabs(pos_left + pos_right)

            # others values of next vtx (on other axis)
            axis21 = dict_axis1_msh2[idx_left]
            axis22 = dict_axis2_msh2[idx_left]
            # calcul of angle of next vtx
            angle2 = math.atan2(axis21, axis22) / math.pi * 180

            # delta of angle between current and next vtx
            delta_angle = math.fabs(angle1 - angle2)

            # check if values of first axis are matching
            # then check if the delta angle is under the threshold (5 degrees)
            if diff < seuil_symetry:
                if delta_angle < seuil_angle:
                    # logging.debug('DELTA ANGLE : {}'.format(delta_angle))
                    # logging.debug('ANGLE 1 et 2 : {} // {}'.format(angle1, angle2))
                    comparaison += 1
                    dict_axis0_msh2.remove(dict_axis0_msh2[index_neg])
                    # refresh lengh of dict
                    lenght_max = len(dict_axis0_msh2)

            index_neg += 1
        idx_vtx += 1

    if len(dict_axis0_msh1) != 0:
        corresp = float((float(100) * float(comparaison)) / len(dict_axis0_msh1))
    else:
        corresp = 0

    # logging.debug('COMPARAISON {}'.format(comparaison))
    # logging.debug('LEN DICT POSTIV {}'.format(len(dict_axis0_msh1)))
    # logging.debug('CORRESPONDANCE ANGLES {}'.format(corresp))
    return corresp


def check_sym_along_axis(axis, mesh01, mesh02=None, piv=0, self_check=False):
    """
    Check the symetry on an axis based on vertex pos. Can be with two meshes,
    or along one.
    :param : axis : given axis; x, y or z.
    :type : axis : string
    :param : mesh 01, mesh02
    :param piv = 0 BY DEFAULT / Or center of object on X
    It will check the object on itself but not centred.
    :param : self check ; value to know if the check is on current mesh (based on mesh01).
    :type : self check : Boolean
    :return : corresp in percentage of match.
    :rtype : float
    """
    idx_axis = {"x": 0, "y": 1, "z": 2}
    axis_select = idx_axis[axis]

    if axis_select == 0:
        axis1 = 1
        axis2 = 2
    elif axis_select == 1:
        axis1 = 2
        axis2 = 0
    elif axis_select == 2:
        axis1 = 0
        axis2 = 1

    # check on mesh01 itself:
    if self_check is True:
        # compare vertex inside one object
        vtx_postv = []
        vtx_neg = []

        # all vtx coordonate of mesh01 in given axis
        all_vtx_axis0 = create_dict_of_vtx(mesh=mesh01, axis=axis_select)
        all_vtx_axis1 = create_dict_of_vtx(mesh=mesh01, axis=axis1)
        all_vtx_axis2 = create_dict_of_vtx(mesh=mesh01, axis=axis2)

        # OBJECT CENTER// OLD
        # piv_center_object = cmds.objectCenter(mesh01)[axis_select]
        # piv = cmds.objectCenter(mesh01)[axis_select]
        # world 0
        # piv = 0

        # take values of bounding box in given axis
        bbox = cmds.polyEvaluate(mesh01, b=True)[axis_select]
        bb_min = bbox[0]
        bb_max = bbox[1]
        if bb_min < bb_max:
            dist = bb_max - bb_min
        else:
            dist = bb_min - bb_max
        length = math.sqrt(math.pow(dist, 2))

        # threshold = un per cent of bouding box
        threshold = length / 100

        # sort all vtx and create a list instead a dict.
        # form : [(88, 68)] where 88 is the vtx number and 68 is the pos in given axis.
        all_vtx = sorted(all_vtx_axis0.items(), key=lambda x: x[1])

        # COMPARAISON ENTRE UN SEUL AXE donne
        for vertex in all_vtx:
            vtx_num = vertex[0]
            vtx_pos = vertex[1]

            # difference between vertex and pivot's axis
            diff = vtx_pos - piv

            # threshold of diff  to remove small vertex in the middle
            if math.fabs(diff) > threshold:
                if vtx_pos > piv:
                    vtx_postv.append((vtx_num, diff))

                elif vtx_pos < piv:
                    vtx_neg.append((vtx_num, diff))

        vtx_postv = sorted(vtx_postv, key=lambda tup: tup[1])
        vtx_neg = sorted(vtx_neg, key=lambda tup: tup[1], reverse=True)

        # if the mesh has not the same nb of vtx on each side.
        if len(vtx_postv) != len(vtx_neg):
            # logging.debug("NOT THE SAME LENGHT OF DICT : {}".format(diff))
            comparaison = 0
        else:
            comparaison = compare_angles(
                dict_vtx1=vtx_postv, dict_vtx2=vtx_neg, dict_axis1=all_vtx_axis1, dict_axis2=all_vtx_axis2)

    # compare between to meshes
    else:
        # logging.debug("MESH 01// 02 {} // {}".format(mesh01, mesh02))
        # compare pivots of meshes. Result:
        # ([piv mesh01], [piv mesh02])
        points_pivots = compare_pivots(mesh01, mesh02, detailled=True)
        piv_mesh01 = points_pivots[0]
        # only on x axis
        piv_mesh01 = piv_mesh01[axis_select]
        piv_mesh02 = points_pivots[-1]
        piv_mesh02 = piv_mesh02[axis_select]

        # check with pivot if mesh01/mesh02 are right or left
        if piv_mesh01 > piv_mesh02:
            right_mesh = mesh01
            left_mesh = mesh02
        else:
            right_mesh = mesh02
            left_mesh = mesh01

        # get the vtx in X of the 2 meshes
        vtx_mesh_right = create_dict_of_vtx(mesh=right_mesh, axis=axis_select)
        vtx_mesh_left = create_dict_of_vtx(mesh=left_mesh, axis=axis_select)
        vtx_mesh_right = sorted(vtx_mesh_right.items(), key=lambda x: x[1])
        vtx_mesh_left = sorted(vtx_mesh_left.items(),
                               key=lambda x: x[1], reverse=True)

        # get the vtx in 2 other axis of the 2 meshes
        dict_axis1_msh1 = create_dict_of_vtx(mesh=mesh01, axis=axis1)
        dict_axis2_msh1 = create_dict_of_vtx(mesh=mesh01, axis=axis2)
        dict_axis1_msh2 = create_dict_of_vtx(mesh=mesh02, axis=axis1)
        dict_axis2_msh2 = create_dict_of_vtx(mesh=mesh02, axis=axis2)

        # compare vtx only in multiple axis
        comparaison = compare_angles_two_meshes(
            dict_axis0_msh1=vtx_mesh_right, dict_axis0_msh2=vtx_mesh_left, dict_axis1_msh1=dict_axis1_msh1,
            dict_axis1_msh2=dict_axis1_msh2, dict_axis2_msh1=dict_axis2_msh1, dict_axis2_msh2=dict_axis2_msh2)
        # logging.debug("RESULT COMPARAISON {}".format(comparaison))

    return comparaison


def check_sym_of_all_obj(meshes, colorMeshes):
    """
    Check the self symetry on X axis on all meshes.
    Returns a list with mesh wich are potential symetrical.
    :param : meshes
    :return sym_meshes : list of meshes symetrical of 65 percent
    :rtype : list
    """
    sym_meshes = []
    potential_sym = []

    for mesh in meshes:
        CENTERX = cmds.objectCenter(mesh)[0]
        # check if mesh is really near to world
        if math.fabs(CENTERX) < 0.0001:
            result_x = check_sym_along_axis(
                axis="x", mesh01=mesh, self_check=True)
            results = result_x
            if results > 95:
                sym_meshes.append(mesh)
                if colorMeshes:
                    update_nodes.color_meshes(mesh01=mesh, mesh02=mesh, rgba="r")

        # check if mesh is not aligned but near to world
        elif 0.0001 <= math.fabs(CENTERX) <= 0.3:
            result_poten = check_sym_along_axis(
                axis="x", mesh01=mesh, piv=CENTERX, self_check=True)
            if result_poten > 95:
                potential_sym.append(mesh)

    logging.info("*" * 10 + "SYMETRICAL MESHES : {}".format(sym_meshes))
    logging.info("*" * 10 + "POTENTIAL SYMETRICAL : {}".format(potential_sym))
    store_into_set(meshes=potential_sym, set_name="CTRL_POTENTIAL_SELFSYM")
    return (sym_meshes, potential_sym)


def compare_areas_of_two_meshes(mesh01, mesh02):
    """
    Compare two meshes, the values of area.
    :param mesh01: mesh 1
    :param mesh02: mesh 2
    :type mesh01 / mesh02 : meshes maya
    :return corresp : True of False matching based on area
    :rtype : Boolean
    """
    area_match = False
    area_mesh01 = cmds.polyEvaluate(mesh01, wa=True)
    area_mesh02 = cmds.polyEvaluate(mesh02, wa=True)
    # coeff multiplicator for difference propertion of mesh area
    percent = area_mesh01 * 0.001
    difference = math.fabs(area_mesh01 - area_mesh02)
    if difference < percent:
        area_match = True

    return area_match


def compare_pivots(mesh01, mesh02, detailled=False):
    """
    Compare center object positions.
    Detailled allows to return the values of center of both meshes.
    Threshold = 1
    :return match based on substraction ; threshold is 1
    :rtype : Boolean
    """
    threshold = 1

    pos_piv_mesh01 = cmds.objectCenter(mesh01)
    pos_piv_mesh02 = cmds.objectCenter(mesh02)

    result_both = []
    match = False

    # pos_piv_mesh01 results - pos_piv_mesh02 results
    for index, i in enumerate(pos_piv_mesh01):
        current_value = pos_piv_mesh01[index]
        current_value_next_mesh = pos_piv_mesh02[index]
        if math.fabs(current_value) > math.fabs(current_value_next_mesh):
            result_both.append(math.fabs(current_value) -
                               math.fabs(current_value_next_mesh))
        else:
            result_both.append(
                math.fabs(current_value_next_mesh) - math.fabs(current_value))

    for result in result_both:
        if result <= threshold:
            match = True
        else:
            match = False

    # detailled mode
    if detailled is True:
        return (pos_piv_mesh01, pos_piv_mesh02)
    else:
        return match


# Utils
def store_into_set(meshes, set_name):
    """
    Store the meshes in a selection set if it's more than a mesh
    """
    check_len = len(meshes)
    if check_len > 0:
        cmds.select(meshes, r=True)
        cmds.sets(n=set_name)
        cmds.select(cl=True)


def compare_two_meshes(mesh01, mesh02, centred=True):
    """
    Compare two meshes.
    Compare:
    -Nb of components (must be identical)
    -Areas result
    -Center of object result
    -Result of vtx comparaison
    :param centred :if meshes are not in 0 in X.
    :type : float
    :rtype : Bool
    """
    match = False
    mesh = mesh01
    next_mesh = mesh02

    nb_face = read_nodes.get_nb_of_component_of_mesh(meshElement=mesh01, co_type="face")
    nb_edge = read_nodes.get_nb_of_component_of_mesh(meshElement=mesh01, co_type="edge")
    nb_vtx = read_nodes.get_nb_of_component_of_mesh(meshElement=mesh, co_type="vtx")
    next_nb_face = read_nodes.get_nb_of_component_of_mesh(meshElement=next_mesh, co_type="face")
    next_nb_edges = read_nodes.get_nb_of_component_of_mesh(meshElement=next_mesh, co_type="edge")
    next_nb_vtx = read_nodes.get_nb_of_component_of_mesh(meshElement=next_mesh, co_type="vtx")
    mesh_center = math.fabs(cmds.objectCenter(mesh)[0])
    next_mesh_center = math.fabs(cmds.objectCenter(next_mesh)[0])

    # if a mesh have the same nb of components
    if nb_face == next_nb_face and nb_edge == next_nb_edges and nb_vtx == next_nb_vtx:
        result_areas = compare_areas_of_two_meshes(
            mesh01=mesh, mesh02=next_mesh)

        # if the area is the same, compare pivots
        if result_areas is True:
            result_pivot = compare_pivots(mesh01=mesh, mesh02=next_mesh)

            # if pivot are the same, check vertex
            if result_pivot is True:
                result_sym_x = check_sym_along_axis(
                    axis="x", mesh01=mesh, mesh02=next_mesh, self_check=False)
                # if we dont want the meshes to be aligned
                if centred is False:
                    # check if the meshes are not centered in X
                    if mesh_center > 0.0001 and next_mesh_center > 0.0001:
                        if result_sym_x > 60:
                            match = True
                else:
                    match = True

    return match


def compare_all_meshes(colorMeshes=True, createSets=True, *args):
    """
    Compare all meshes based on nb of component, and area.
    Check if vertex number, face number, edge number are identical,
    Then, store them in pairs_found list.
    If mesh is in pair list, it compares the two meshes based on area.
    And check the values of vertex in one axis.
    If positive, store the result in the list detailled_pairs (mesh01, mesh02, result)
    And store the meshes in the right list.

    :return dict_pairs : dict of {mesh01:mesh02} as pair.
    :rtype : dict
    """
    global dict_of_pairs

    name_meshes = read_nodes.list_all_meshes()
    logging.debug("*" * 10 + "COMPARING MESHES" + "*" * 10)
    logging.debug(str(name_meshes))

    dict_of_pairs = {}

    # get nb of face, edges and vtx
    face_nb = read_nodes.get_nb_of_component(
        meshesList=name_meshes, co_type="face")
    face_nb = sorted(face_nb.items(), key=lambda x: x[1])
    len_dico_face = len(face_nb)


    idx_mesh = 0
    match_symetry = []
    detailled_pairs = []

    for mesh, nb_face in face_nb:
        idx_next_mesh = idx_mesh + 1
        # check with others meshes
        while idx_next_mesh < len_dico_face:
            next_mesh = face_nb[idx_next_mesh][0]
            # compare two meshes
            result = compare_two_meshes(mesh01=mesh, mesh02=next_mesh, centred=False)
            if result is True:
                result_areas = compare_areas_of_two_meshes(mesh01=mesh, mesh02=next_mesh)
                # on rajoute le result dans match sym et dict of pairs
                detailled_pairs.append(
                    (mesh, next_mesh, result_areas))
                dict_of_pairs[mesh] = next_mesh
                match_symetry.append(mesh)
                match_symetry.append(next_mesh)
                # color both meshes
                if colorMeshes:
                    update_nodes.color_meshes(mesh01=mesh, mesh02=next_mesh)

            idx_next_mesh += 1
        idx_mesh += 1


    unique = list(set(name_meshes).difference(set(match_symetry)))
    logging.debug("UNIQUE {}".format(unique))
    if createSets:
        store_into_set(meshes=unique, set_name="CTRL_UNIQUE")
        store_into_set(meshes=match_symetry, set_name="CTRL_MATCH_SYMETRY")

    logging.debug('DICT PAIRS : {}'.format(dict_of_pairs))

    return dict_of_pairs


def check_u_sym(*args):
    """
    Launch the symetrical check for meshes if they are not already in sym with another mesh.
    Store the result into sets.
    Clean the sets after. (remove the C object from unique set).
    :return potentential_sym : list of mesh almost centered.
    :rtype : list
    """
    obj_in_ctrl_sym = read_nodes.list_set_members(sel_set="CTRL_MATCH_SYMETRY")
    all_meshes = read_nodes.list_all_meshes()
    # remove meshes of symetry already found
    mesh_to_check_sym = [
        mesh for mesh in all_meshes if mesh not in obj_in_ctrl_sym]

    # check symetry on c and create the set CTRL C
    all_sym_objects = check_sym_of_all_obj(meshes=mesh_to_check_sym, colorMeshes=True)
    all_sym_obj = all_sym_objects[0]
    potential_sym = all_sym_objects[1]
    store_into_set(meshes=all_sym_obj, set_name="CTRL_C")

    obj_in_ctrl_c = read_nodes.list_set_members(sel_set="CTRL_C")

    # clean sets with long names
    if cmds.objExists("CTRL_UNIQUE"):
        # remove the object from CTRL C
        obj_in_ctrl_u = read_nodes.list_set_members(sel_set="CTRL_UNIQUE")
        for obj in obj_in_ctrl_u:
            obj = cmds.ls(obj, long=True)[0]
            if obj in obj_in_ctrl_c:
                # logging.debug(
                #     'OBJET HAVE BEEN DELETE FROM UNIQUE SET {}'.format(obj))
                cmds.sets(obj, rm="CTRL_UNIQUE")

    logging.info('*' * 10 + "END OF SELF SYM" + "*" * 10)
    return potential_sym


def launch_renaming(*args):
    """
    Change names based on selection sets.
    Check if set is not empty, then rename obj or delate set.
    Launch rename_with_unique_name : to avoid m_Msh1 ... _Msh2...
    Launch rename_grps : recursive check of grp names with it content.
    """
    # clean empty select sets of match sym and launch renaming
    obj_in_ctrl_sym = read_nodes.list_set_members('CTRL_MATCH_SYMETRY')
    if len(obj_in_ctrl_sym) > 0:
        check_names_and_rename(meshes=obj_in_ctrl_sym, category="lr")
    else:
        if cmds.objExists('CTRL_MATCH_SYMETRY'):
            cmds.delete('CTRL_MATCH_SYMETRY')

    obj_in_ctrl_c = read_nodes.list_set_members(sel_set="CTRL_C")
    if len(obj_in_ctrl_c) > 0:
        check_names_and_rename(meshes=obj_in_ctrl_c, category="c")
    else:
        if cmds.objExists('CTRL_C'):
            cmds.delete('CTRL_C')

    obj_in_ctrl_u = read_nodes.list_set_members(sel_set='CTRL_UNIQUE')
    if len(obj_in_ctrl_u) > 0:
        check_names_and_rename(meshes=obj_in_ctrl_u, category="u")
    else:
        if cmds.objExists('CTRL_UNIQUE'):
            cmds.delete('CTRL_UNIQUE')

    # rename top node
    update_nodes.rename_top_node()
    # check and rename group names
    rename_grps()
    # check unique names
    rename_with_unique_name()


    logging.info('*' * 30 + "END" + "*" * 30)


def format_datas(dict_of_pairs):
    """"
    Format datas to store for each mesh
    Creates a dict with the type of sym.
    Ex : {'mesh' : {'U' : True}}
    :return datas
    :rtype : dict
    """
    datas = {}
    u_meshes = read_nodes.list_set_members(sel_set="CTRL_UNIQUE")
    c_mshes = read_nodes.list_set_members(sel_set="CTRL_C")
    sym_mshes = read_nodes.list_set_members(sel_set="CTRL_MATCH_SYM")
    pot_sym_mshes = read_nodes.list_set_members(sel_set="CTRL_POTENTIAL_SELFSYM")
    meshes = read_nodes.list_all_meshes()
    for mesh in meshes:
        if mesh in pot_sym_mshes:
            shape = cmds.listRelatives(mesh, c=True, fullPath=True)[0]
            datas[shape] = {"POTENTIAL SYM": True}
        if mesh in c_mshes:
            datas[mesh] = {"C": True}
        if mesh in sym_mshes:
            datas[mesh] = {"PAIRS": dict_of_pairs[mesh]}
        if mesh in u_meshes and mesh not in pot_sym_mshes:
            datas[mesh] = {"U": True}

    return datas


def launch_help():
    """
    Launch hackmd page for documentation
    """
    url = 'https://hackmd.io/MK533M9MQRuiHnwvHJUcpg?view'
    webbrowser.open_new(url)


def all_actions(batch=False, *args):
    """
    Launch all sym, renaming functions.
    Returns the potential sym.
    :return potential_sym
    :rtype : dict
    """
    logging.info('*' * 30 + "START OF ALL ACTIONS" + "*" * 30)
    init_scene()
    dict_of_pairs = compare_all_meshes(createSets=True, colorMeshes=True)
    check_u_sym()
    launch_renaming()
    if batch is True:
        datas = format_datas(dict_of_pairs)
        init_scene()
        return datas

    logging.info('*' * 30 + "END OF ALL ACTIONS" + "*" * 30)


def init_scene(*args):
    """
    Reinit the scene.
    Clean colors of shapes, unsmooth meshes, clear select sets, reset pivots.
    """
    all_shapes = read_nodes.list_all_shapes()
    update_nodes.clean_color_mesh(all_shapes=all_shapes)
    update_nodes.unsmooth_meshes(meshes=all_shapes, state=0)
    delete_nodes.delete_sets()
    logging.info("___SCENE HAS BEEN REINIT___")


def detect_sym_auto_ui(*args):
    """
    Init scene, list all meshes/shapes and then check sym options.
    Buttons:
    -Init scene
    -Get detailled pairs and check of compare_all_meshes; it store into sets
    the meshes that seems to be identical or unique.
    -Check self symetry on x
    -Rename meshes based on nomenclature of sets.
    """
    logging.info("...LAUNCHING WINDOW....")

    # init_scene_ = partial(init_scene)
    # compare_meshes_ = partial(compare_all_meshes(colorMeshes=True, createSets=True))
    # check_u_sym_ = partial(check_u_sym)
    # rename_meshes_ = partial(launch_renaming)
    # all_actions_ = partial(all_actions)

    winName = "CHECK SYM"
    if cmds.window(winName, exists=True):
        cmds.deleteUI(winName, window=True)

    fenetre = cmds.window(
        title=winName, iconName='Check sym', widthHeight=(210, 300), menuBar=True)

    cmds.menu(label='Help', tearOff=True)
    cmds.menuItem(label='Help page', command=lambda x: launch_help())

    cmds.columnLayout(adjustableColumn=True)
    cmds.text(label="")
    cmds.button(label='Renit scene', c=lambda x: init_scene())
    cmds.text(label="")
    cmds.button(label='ALL FUNCTIONS', c=lambda x: all_actions())
    cmds.text(label=" ")
    cmds.text(label="____________________")
    cmds.text(label=" ")
    cmds.button(label='Find pairs', c=lambda x: compare_all_meshes(colorMeshes=True, createSets=True))
    cmds.text(label="")
    cmds.button(label='Find self sym', c=lambda x: check_u_sym())
    cmds.text(label="")
    cmds.button(label='Rename meshes', c=lambda x: launch_renaming())
    cmds.text(label="")

    cmds.button(label='Close', command=(
        'cmds.deleteUI(\"' + fenetre + '\", window=True)'))

    cmds.showWindow(fenetre)


def detect_sym_auto():
    """
    Launch window UI
    """

    logging.info('*' * 30 + "START" + "*" * 30)
    logging.info("ASSET : {}".format(read_scene.get_file_informations()[1]))

    all_win = cmds.lsUI(windows=True)
    for win in all_win:
        if win != "MayaWindow":
            cmds.deleteUI(win, window=True)

    detect_sym_auto_ui()
    logging.info('*' * 30 + "END" + "*" * 30)
