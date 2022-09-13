# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Utils for nodes updates
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         glob var problem in found_maya_scene. Unfound rendersetup
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging
import math
import re
from random import random

try:
    import maya.cmds as cmds
    import maya.mel as mel
except ImportError:
    pass

from ..reads import nodes as read_nodes
from ..reads import scene as read_scenes
from ..reads import shaders as read_shaders
from ..checks import nodes as check_nodes
from ..checks import shaders as check_shaders


# _________________________________________________________________________________________________________
# #########################
# ------MANAGE MESHES-----#
# #########################

# TODO: need to return what has been locked/unlocked
# TODO: rename: lock_transform_attr()
def lock_transform(transform_list=None, lock=False, logger=logging):
    """
    Unlock attr of transform_list, if None: unlock attr from current selection
    :param: transform_list => None by default
    :param: lock => False by default
    """
    if not transform_list:
        element_to_unlock_list = cmds.ls(sl=True, long=True)
    else:
        element_to_unlock_list = transform_list
    if element_to_unlock_list:
        attr_to_unlock_list = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ', 'visibility']

        for element_to_unlock in element_to_unlock_list:
            for attr_to_unlock in attr_to_unlock_list:
                if cmds.getAttr('{}.{}'.format(element_to_unlock, attr_to_unlock), lock=True) != lock:
                    cmds.setAttr('{}.{}'.format(element_to_unlock, attr_to_unlock), lock=lock)
        logging.debug('Selection has been set to : {}.'.format(lock))
    else:
        logging.debug('Nothing to unlock.')


# TODO: need to return what has been locked/unlocked
def lock_nodes(transform_list=None, lock=True, lock_attr=True, logger=logging):
    """
    Lock or unlock transform list
    :param: transform_list => None by default
    :param: lock => True by default
    :param: lock_attr => True by default
    """
    if not transform_list:
        transform_list = read_nodes.list_all_meshes()
        transform_list += read_nodes.list_all_groups()
    for node in transform_list:
        cmds.lockNode(node, lock=False)
        if lock_attr:
            lock_transform(transform_list=[node], lock=lock)
        if lock:
            cmds.lockNode(node, lock=lock)


# TODO: need to return what has been changed
def reverse_normals(mesh):
    """
    Reverse normales of given mesh
    :param: mesh
    """
    faces = read_nodes.get_nb_of_component_of_mesh(mesh, co_type="face")
    for f in range(faces):
        cmds.polyNormal(mesh + ".f[{}]".format(f), nm=0)


# TODO: need to return what has been changed
def unsmooth_meshes(meshes, state):
    """
    Disable or enable smooth mesh preview
    :param: meshes
    :param: state
    """
    for mesh in meshes:
        if cmds.objExists(mesh):
            attr = mesh + '.displaySmoothMesh'
            if cmds.attributeQuery('displaySmoothMesh', node=mesh, ex=True) is True:
                cmds.setAttr(attr, state)
    logging.info("Smooth: {} on {}".format(state, meshes))


# Unused
# TODO: snakecase
# TODO: need to return what has been changed
def activate_smooth_mesh(enable, level, renderLayer=None, shapeList=None):
    """
    Function to smooth or unsmooth mesh preview, with a given level on a given shapelist.
    It can be used in layer override.
    :param: enable => bool, Enable the smooth mesh preview
    :param: level => int, Level of smooth mesh preview;
    :param: shape list => list of shapes to do the operation
    """
    all_shapes = cmds.ls(exactType='mesh', dag=1, ni=1, long=True)
    if shapeList:
        all_shapes = shapeList
    for shape in all_shapes:
        if cmds.objExists(shape):
            attrDisplay = "displaySmoothMesh"
            attrLevel = "smoothLevel"
            display = '{}.{}'.format(shape, attrDisplay)
            level = '{}.{}'.format(shape, attrLevel)
            if cmds.attributeQuery(attrDisplay, node=shape, ex=True) is True:
                if enable:
                    if renderLayer:
                        cmds.editRenderLayerAdjustment(display, layer=renderLayer)
                    cmds.setAttr(display, 2)

                    if cmds.attributeQuery(attrLevel, node=shape, ex=True) is True:
                        if renderLayer:
                            cmds.editRenderLayerAdjustment(level, layer=renderLayer)
                        cmds.setAttr(level, level)
                else:
                    cmds.setAttr(display, 0)


# Unused
# TODO: Clean method
# TODO: need to return what has been changed
def calcultate_bbs_displacement(shape, override=False):
    """
    WIP: should check if shape has displace before
    Calculate bounding box scale for displacement
    :param: shape
    :param: override => False by default
    """
    DEFAULT_VALUE = 1.5
    disp_co_found = check_shaders.is_displacement(shape)
    if not disp_co_found:
        logging.warning('"{}" has no displacement: keep default value!'.format(shape))
    if not override:
        mel.eval('displacementToPoly -findBboxOnly {};'.format(shape))
        logging.info('"{}" bounding box scale has been set'.format(shape))
        return
    shape_values = read_nodes.get_bbs_displacement(shape)
    has_default_value = False
    for value in shape_values:
        if value == DEFAULT_VALUE:
            mel.eval('displacementToPoly -findBboxOnly {};'.format(shape))
            has_default_value = True
    if has_default_value:
        logging.info('"{}" bounding box scale has been set'.format(shape))
    else:
        logging.warning('"{}" Bounding Box Scale already set!'.format(shape))


# Used in hook create_out_task_modeling
def clean_shape_vertices(meshes_list=None):
    """
    Clean vertices coordinates if intermediate found
    Delete shape history
    :param: meshes_list => None by default
    :return: cleaned_shape_list => cleaned shapes
    :rtype: list
    """
    logging.info('Looking for vertices to clean.')
    cleaned_shape_list = []
    # Get all meshes if no meshes_list
    if meshes_list is None:
        meshes_list = read_nodes.list_all_meshes()
    # Get their shapes
    for mesh_found in meshes_list:
        shapes_list = cmds.listRelatives(mesh_found, s=True, f=True, ni=True, ad=True)
        for shape_found in shapes_list:
            intermediate = cmds.getAttr('{}.intermediateObject'.format(shape_found))
            if intermediate is False:
                cmds.polyMergeVertex('{}.vtx[0]'.format(shape_found), d=0.0001, am=1, ch=0)
                cleaned_shape_list.append(shape_found)
                logging.info('Clean shape vertices: "{}"'.format(shape_found))
            else:
                cmds.delete(shape_found, ch=True)
        return cleaned_shape_list


# _________________________________________________________________________________________________________
# #########################
# ------MANAGE SETS-------#
# #########################

# Unused
# TODO: snakecase
# TODO: need to return what has been added to set
def add_to_set(element_list, set_name):
    """
    Add a list of object to specified set
    """
    if not cmds.objExists(set_name):
        cmds.sets(n=set_name, em=True)
        logging.info('"{}" set has been created.'.format(set_name))
    if element_list:
        for element in element_list:
            cmds.sets(element, fe=set_name)
        logging.info('These nodes have been added to "{}": {}.'.format(set_name, element_list))


# TODO: should use add_to_set (Sophie's old comment)
# TODO: delete this method
def store_into_set(meshes, set_name):
    """
    Store the meshes in a selection set if it's more than a mesh
    :param: meshes
    :param: set_name
    """
    check_len = len(meshes)
    if check_len > 0:
        cmds.select(meshes, r=True)
        cmds.sets(n=set_name)
        cmds.select(cl=True)


# _________________________________________________________________________________________________________
# ########################
# ------- COMBINE -------#
# ########################

# TODO: snakecase
# TODO: need to return what has been done
def combineSeparate(mesh):  # sourcery skip: invert-any-all, use-any
    """
    Combine then separates the meshes.
    - Create a plane with one face
    - Separate mesh
    - Combine with plane
    - Delete history and recombine with others meshes of current mesh.
    - Reparent to mesh original parent
    :param: mesh
    """
    # Store the face number
    # Store name for renaming after separate
    name = str(cmds.ls(mesh, sn=True)[0]).split('|')[-1]
    if cmds.ls('PLANETEST'):
        mesh02 = cmds.ls('PLANETEST')[0]
    else:
        mesh02 = cmds.polyPlane(subdivisionsHeight=1, subdivisionsWidth=1, name="PLANETEST")
    # Store parent to reparent after separate
    parent01 = cmds.listRelatives(mesh, p=True, fullPath=True)[0]
    # Parent to worl to avoid parent destruction
    mesh = cmds.parent(mesh, world=True)
    # Combine
    cmds.polyUnite(mesh, mesh02, n="TMP")
    # Delete hist
    cmds.delete("TMP", constructionHistory=True)
    unite = cmds.ls(str("TMP"))
    # Separate
    cmds.polySeparate(unite)
    assemblage = cmds.ls('TMP', long=True)[0]
    # Result of separate
    assemblage = cmds.listRelatives(assemblage, c=True, fullPath=True)
    idx_ass = 0
    for mesh in assemblage:
        if cmds.objExists(mesh):
            # delete hist
            cmds.delete(mesh, constructionHistory=True)
        else:
            assemblage.pop(idx_ass)
        idx_ass += 1
    idx = 0
    for mesh in assemblage:
        # Check if current mesh is plane, check nb of face and if mesh is 0 0 0
        if read_nodes.get_nb_of_component_of_mesh(mesh, "face") == 1:
            center = cmds.objectCenter(mesh)
            centred = True
            for value in center:
                if value != 0:
                    centred = False
            if centred:
                logging.info('Plane found %s' % mesh)
                assemblage.pop(idx)
                cmds.delete(mesh)
        idx += 1
    assemblage = cmds.listRelatives(cmds.ls('TMP')[0], c=True, fullPath=True)
    if len(assemblage) > 1:
        mesh = cmds.polyUnite(assemblage, n=name)
        mesh = cmds.ls(name)[0]
    else:
        mesh = assemblage[0].split('|')[-1]
        mesh = cmds.rename(mesh, name)
    cmds.delete(mesh, constructionHistory=True)
    cmds.parent(mesh, parent01)
    if cmds.ls('TMP'):
        cmds.delete('TMP')
    logging.info('Combine done')


# _________________________________________________________________________________________________________
# #########################
# ---------RENAME---------#
# #########################

# TODO: return new name
def rename_top_node(task_name=None, logger=logging):
    """
    Rename top group with scene name.
    Eg: {ASSET_NAME}_MDL_Grp
    :param: task_name => None by default
    """
    top_grp = read_nodes.get_top_node()[0]
    logger.debug('Top node name {}'.format(top_grp))
    file_name = read_scenes.get_file_informations()[1]
    file_name = "_".join(file_name.split('_')[0:3])
    new_name_grp = file_name + "_Top"
    if task_name:
        new_name_grp = file_name.replace("_" + task_name, "") + "_Top"
    if top_grp != new_name_grp:
        rename_obj(obj=top_grp, new_name=new_name_grp)
        logger.info("*" * 10 + "TOP NODE HAS BEEN RENAMED: {}".format(new_name_grp))


# TODO: remove print, put logging
def increment_name(name, regex=None, fill_length=None):
    """
    Create a new name for clashing names and return it.
    Based on pattern: _ddd_'
    New regex pattern must be with r'mystring' !!
    :param: name => string, name of mesh who need to be checked.
    :param: regex => string, r'', custom regexpression
    :param: fill_length => int, how much for zfill string. Defaut: 3
    :return: final_name
    :rtype: string
    """
    final_name = str(name)
    digits = re.compile(r'_\d\d\d_')
    if regex:
        digits = re.compile(regex)
    if fill_length is None:
        fill_length = 3
    match = digits.search(final_name)
    if match is not None:
        match = str(match.group().replace('_', ''))
        int_match = 1
        final_name = final_name.replace(match, str(int_match).zfill(fill_length))
        new_name = final_name.replace(match, '{}')
        while cmds.objExists(new_name.format(str(int_match).zfill(fill_length))):
            int_match += 1
            final_name = new_name.format(str(int_match).zfill(fill_length))
            logging('final_name', final_name)
    return final_name


# TODO: need to return new name if ok or None if not
def rename_obj(obj, new_name):
    """
    Rename the object with increment if exists
    Must be SHORT NAME
    :param: obj
    :param: new_name
    """
    if cmds.objExists(new_name):
        # Increment name in case of clashing
        new_name = increment_name(new_name)
    try:
        cmds.rename(obj, new_name)
    except Exception as e:
        logging.warning('{} // Object has no proper new name {} // {}'.format(e, obj, new_name))


# _________________________________________________________________________________________________________
# #########################
# ------NOMENCLATURE------#
# #########################

# TODO rename to replace_suffix + all vars inside
def replace_suffixe(mesh, regexp=r'\d{1,}$'):
    """
    Replace the suffixe at the end of mesh.
    Replace: mesh23 by mesh
    :param: mesh
    :param: regexp => r'\d{1,}$' by default
    :return: final_name
    :rtype: string
    """
    final_name = str(mesh)
    suffixe_pattern = re.compile(regexp)
    match_suffixe = suffixe_pattern.search(mesh)
    if match_suffixe is not None:
        str_suffixe = str(match_suffixe.group())
        start = match_suffixe.start()
        end = match_suffixe.end()
        final_name = mesh
        final_name = final_name[0:start] + \
            final_name[start:end].replace(str_suffixe, "")
        # Increment the correct digits if exits
        if cmds.objExists(final_name):
            final_name = increment_name(final_name)
    return final_name


# TODO: rename to correct_camelcase() or fix_camelcase()
def correct_camelCase(mesh):
    """
    Correct camel case in upper
    :param: mesh
    :return: new_name
    :rtype: string
    """
    mesh = cmds.ls(mesh, sn=True)[0]
    if "|" in mesh:
        mesh = mesh.split('|')[-1]
    new_name = mesh
    split_name = mesh.split('_')
    for part in split_name:
        if part[0].isupper() is False and part.isdigit() is False:
            new_name = new_name.replace(part[0], part[0].upper())
    return new_name


# TODO: rename to correct_group_prefix() or fix_group_prefix() + vars inside
def correct_grp_prefix(grp):
    """
    Check childs prefix, determine what must be used
    And then check if grp prefix is correct
    :return new_grp_name  : SHORT NAME
    :rtype : str
    """
    grp_sn = cmds.ls(grp, sn=True)[0]
    if "|" in grp_sn:
        grp_sn = grp_sn.split('|')[-1]
    new_grp_name = str(grp_sn)
    all_pref_childs = read_nodes.get_children_prefix(grp)
    # Prefix grp
    prefix_grp = read_nodes.get_prefix(grp_sn)
    if check_nodes.check_grp_prefix(grp=grp) is False:
        # Determine what prefix must be used
        prefix = read_nodes.determine_prefix(all_pref_childs)
        # In case grp has no prefix
        if prefix is not None:
            if prefix_grp is None:
                new_grp_name = prefix + grp_sn
                logging.info(
                    "NO PREFIX IN GRP!! OLD GRP NAME // NEW GRP NAME\n{}\n {} \n\n ".format(grp_sn, new_grp_name))
                new_grp_name = increment_name(new_grp_name)
            # If prefix of grp doesnt match with its children
            elif prefix != prefix_grp:
                new_grp_name = grp_sn.replace(prefix_grp, prefix)

    return new_grp_name


# TODO: rename to correct/fix_object_nomenclature/naming()
# TODO: split into much smaller functions
# TODO: need to return something
def correct_obj_nom(mesh):
    """
    Corrects mesh nomenclature
    :param: mesh
    """
    orig_mesh = str(mesh)
    cat_prefix = ["C_", "U_", "L_", "R_"]
    mesh = cmds.ls(mesh, sn=True)[0].split('|')[-1]
    # Check full name
    if check_nodes.check_camelCase(mesh) is False:
        new_name = correct_camelCase(mesh)
        cmds.select(orig_mesh, r=True)
        mesh = cmds.rename(new_name)
        orig_mesh = cmds.ls(sl=True, long=True)[0]
    # For meshes
    if read_nodes.is_group(mesh) is False:
        prefix = read_nodes.get_prefix(mesh)
        if prefix not in cat_prefix:
            logging.error('The following mesh needs to be categorized :  %s \n \
                        Please launch detect sym tool.' % (mesh))
        # Prefix seems to be correct, launching suffixe
        else:
            new_name = str(mesh)
            # Checking if mesh follows nomenclature
            mesh_pattern = r'[C-U]_[A-Z][aA-zZ]{1,}\d\d_\d\d\d_Msh$'
            if check_nodes.check_valide_suffix(mesh=mesh, regexp=mesh_pattern) is False:
                # Check if its only about camel case modif
                mesh_pattern = r'[C-U]_[a-z][aA-zZ]{1,}\d\d_\d\d\d_Msh$'
                if check_nodes.check_valide_suffix(mesh=mesh, regexp=mesh_pattern):
                    # Get first letter
                    first_letter = mesh.split('_')[1][0]
                    new_name = mesh.replace(first_letter, first_letter.upper())
                # Check if its only missing 2 digit after name
                # mesh_pattern = r'[C-U]_[A-Z]\w{1,}_\d\d\d_Msh$'
                elif check_nodes.check_valide_suffix(mesh=mesh, regexp=r'[C-U]_[A-Z][aA-zZ]{1,}_\d\d\d_Msh$'):
                    new_name = mesh.split('_')[-3]
                    new_name = mesh.replace(new_name, new_name + '01')
                # Check if its only missing 3 digit
                # mesh_pattern = r'[C-U]_[A-Z]\w{1,}\d\d_Msh$'
                elif check_nodes.check_valide_suffix(mesh=mesh, regexp=r'[C-U]_[A-Z][aA-zZ]{1,}\d\d_Msh$'):
                    new_name = mesh.replace("_Msh", "_001_Msh")

                # Check if its only missing all digits after name
                # mesh_pattern = r'[C-U]_\w{1,}_Msh$'
                elif check_nodes.check_valide_suffix(mesh=mesh, regexp=r'[C-U]_[aA-zZ]{1,}_Msh$'):
                    new_name = mesh.replace('_Msh', "01_001_Msh")
                # If name already finishes with diggit
                # mesh_pattern = r'_\d\d\d$'
                elif check_nodes.check_valide_suffix(mesh=mesh, regexp=r'_\d\d\d$'):
                    new_name = mesh.replace(mesh, mesh + "_Msh")
                elif check_nodes.check_valide_suffix(mesh=mesh, regexp=r'_msh$'):
                    new_name = mesh.replace('_msh', "_Msh")
                elif check_nodes.check_valide_suffix(mesh=mesh, regexp=r'_Msh\d$'):
                    wrong_ending = mesh.split('_Msh')[-1]
                    new_name = mesh.replace('_Msh' + wrong_ending, "_Msh")
                    if cmds.objExists(new_name):
                        new_name = increment_name(new_name)
                if len(cmds.ls(new_name)) > 1:
                    new_name = increment_name(new_name)
                logging.info('Name / new name %s %s' % (mesh, new_name))
                cmds.select(orig_mesh, r=True)
                try:
                    cmds.rename(new_name)
                except Exception as e:
                    logging.info('Cannot rename, incrementing')
                    logging.info(e)
                    new_name = increment_name(mesh)
                    cmds.rename(new_name)
            logging.info('Mesh %s has been renamed' % (mesh))
    # Groups
    if read_nodes.is_group(mesh):
        grp = mesh
        new_name = str(grp)
        # Check prefix
        if check_nodes.check_grp_prefix(grp=grp) is False:
            new_grp_name = correct_grp_prefix(grp=grp)
            if new_grp_name != grp:
                cmds.rename(grp, new_grp_name)
                logging.info(
                    "OLD GRP NAME // NEW GRP NAME\n{}\n{} \n\n ".format(mesh, new_grp_name))
                grp = new_grp_name
        grp_pattern = r'[C-U]_[A-Z]\w{1,}\d\d_Grp$'
        if check_nodes.check_valide_suffix(mesh=grp, regexp=grp_pattern) is False:
            # Check if only missing upper first letter
            grp_pattern = r'[C-U]_[a-z]\w{1,}\d\d_Grp$'
            if check_nodes.check_valide_suffix(mesh=grp, regexp=grp_pattern):
                first_letter = grp.split('_')[1][0]
                new_grp_name = grp.replace(first_letter, first_letter.upper())
            # If only missing digits
            grp_pattern = r'[C-U]_[A-Z]\w{1,}_Grp$'
            if check_nodes.check_valide_suffix(mesh=grp, regexp=grp_pattern):
                new_grp_name = grp.split('_')[-2]
                new_grp_name = grp.replace(new_grp_name, new_grp_name + '01')
                if cmds.objExists(new_grp_name):
                    new_grp_name = increment_name(grp)
            # If ending is not right
            grp_pattern = r'_Grp$'
            if check_nodes.check_valide_suffix(mesh=grp, regexp=grp_pattern) is False:
                new_grp_name = replace_suffixe(
                    grp, regexp=r'_Grp.{1,}') + "_Grp"
            grp_pattern = r'[C-U]_[A-Z]\w{1,}\d\d_grp$'
            if check_nodes.check_valide_suffix(mesh=grp, regexp=grp_pattern):
                new_grp_name = grp.replace('_grp', '_Grp')
            if new_grp_name != grp:
                if cmds.objExists(new_name):
                    new_name = increment_name(new_name)
                cmds.select(orig_mesh, r=True)
                cmds.rename(new_grp_name)
                logging.info("OLD GRP NAME // NEW GRP NAME\n{}\n{} \n\n ".format(grp, new_grp_name))


# _________________________________________________________________________________________________________
# #########################
# -----MESH POSITION------#
# #########################

# Unused
# TODO: put in a try except and return if object has been recentered properly
def recenter_object(mesh):
    """
    Freeze transform, then center pivot, then move object to the center then FT
    :param: mesh
    """
    cmds.makeIdentity(mesh, apply=True)
    center_x = cmds.objectCenter(mesh)[0]
    center_y = cmds.objectCenter(mesh)[1]
    center_z = cmds.objectCenter(mesh)[2]
    cmds.xform(mesh, cp=True)
    cmds.move(-center_x, -center_y, -center_z, mesh)
    cmds.makeIdentity(mesh, apply=True)


# FIXME: Unused but there is an identical def inside detect_sym_auto
# TODO fix argument spelling: detailed
# EITHER MOVE OR DELET
def compare_pivots(mesh01, mesh02, detailled=False):
    """
    Compare center object positions.
    Detailled allows to return the values of center of both meshes.
    Threshold = 1
    :param: mesh01
    :param: mesh02
    :param: detailled => False by default
    :return: match => based on substraction ; threshold is 1
    :rtype: boolean
    :return: detailled => return detailled position of both centers
    :rtype: tuple
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
        match = True if result <= threshold else False
    # Detailled mode
    if detailled is True:
        return (pos_piv_mesh01, pos_piv_mesh02)
    else:
        return match


# _________________________________________________________________________________________________________
# #########################
# -----------UVS----------#
# #########################

# TODO: fix arguments + vars: use snakecase
# TODO: return new position? or None if too risky
def move_uv(mesh, udimSrc, udimDst):
    """
    Move udim from one udim to another
    :param: mesh
    :param: udimSrc
    :param: udimDst
    """
    uvsInUdim = read_nodes.return_uvs_from_udims(mesh=mesh, udim=udimSrc)
    cmds.select(uvsInUdim, r=True)
    udim_check = read_nodes.get_udims_list(mesh)
    if udimDst not in udim_check:
        uvsSrc = read_nodes.convert_udim(udim=udimSrc)
        uvsDst = read_nodes.convert_udim(udim=udimDst)
        deltaU = uvsDst[0] - uvsSrc[0]
        deltaV = uvsDst[-1] - uvsSrc[-1]
        for uv in uvsInUdim:
            cmds.select(uv, r=True)
            uPos, vPos = cmds.polyEditUV(uv, q=1)
            if deltaU >= 0:
                newUpos = uPos + deltaU
            else:
                newUpos = uPos - math.fabs(deltaU)
            if deltaV >= 0:
                newVpos = vPos + deltaV
            else:
                newVpos = vPos - math.fabs(deltaV)
            cmds.polyEditUV(relative=False, uValue=newUpos, vValue=newVpos)
        cmds.select(cl=True)
        logging.info('Udim has been moved from {} to {}'.format(udimSrc, udimDst))
    else:
        logging.error('Uv destination is risky because its overlapped')


# _________________________________________________________________________________________________________
# #########################
# ---------COLORS---------#
# #########################

# NOTE Before reading the code i would expect that rgba would be a hex or a tuple of 4 numbers or something
# Suggestion: either have r=, g=, b=, a= or a tuple, also add checks that they are within limits (0-1 for example)
# TODO: return attr that have been setted and their values
def color_meshes(mesh01, mesh02, rgba=None):
    """
    Color a pair of meshes with a random color
    :param: mesh01 and mesh02 => the two mesh to colorize
    :param: rgba => None by default / r, g, b / It will tint with the specified color
    """
    random_color = random(), random(), random()
    meshes = [mesh01, mesh02]
    # Override in rgba the random color
    # Its to tint mesh with the given axis color.
    if rgba is not None:
        if rgba == "r":
            random_color = 1, 0, 0
        if rgba == "g":
            random_color = 0, 1, 0
        if rgba == "b":
            random_color = 0, 0, 1
    for mesh in meshes:
        shapes = cmds.listRelatives(mesh, shapes=True)
        for shape in shapes:
            shape = cmds.ls(shape, long=True)[0]
            cmds.setAttr(shape + ".overrideEnabled", True)
            cmds.setAttr(shape + '.overrideRGBColors', 1)
            cmds.setAttr(shape + '.overrideColorRGB',
                         random_color[0], random_color[1], random_color[2], type="double3")


# TODO: set a default value of all_shapes => []
# TODO: return something
def clean_color_mesh(all_shapes):
    """
    Get rid of the wireframe tint
    :param: all_shapes
    """
    for short_shape in all_shapes:
        # Convert to long name
        shape = cmds.ls(short_shape, long=True)[0]
        if cmds.attributeQuery("overrideEnabled", node=shape, ex=True) is True:
            cmds.setAttr(shape + ".overrideColorRGB", 0, 0, 0, type="double3")
            cmds.setAttr(shape + ".overrideEnabled", False)


# _________________________________________________________________________________________________________
# #########################
# --------ATTRIBUTES------#
# #########################

# TODO fix arguments: use snakecase
# TODO Remove all the ifs, inverse the checks, see example
def isolate_object(myObject, visibility=False):
    """
    Hide/Unhide all obj except myObject.
    :param: myObject => maya object
    :param: visibility => False by default, False will isolate an object and True will unhide others
    """
    all_objects = cmds.ls(type="transform", long=True)
    all_objects.remove(myObject)
    attr = "visibility"
    for obj in all_objects:
        if obj is not None:
            if read_nodes.is_group(obj) is False:
                if cmds.attributeQuery(attr, node=obj, exists=True) is True:
                    if cmds.getAttr(obj + "." + attr) is not visibility:
                        if cmds.getAttr(obj + "." + attr, lock=True) is False:
                            try:
                                cmds.setAttr(obj + "." + attr, visibility)
                            except Exception as e:
                                logging.error('Cannot change visibility for : %s' % obj)
                                logging.error(e)
    # NOTE: example of inversing the checks in code (not tested)
    # for obj in all_objects:
    #     attr = "visibility"
    #     if obj is None or read_nodes.is_group(obj):
    #         return
    #     if not cmds.attributeQuery(attr, node=obj, exists=True):
    #         return
    #     if cmds.getAttr(obj + "." + attr) is visibility:
    #         return
    #     if not cmds.getAttr(obj+"."+attr, lock=True):
    #         try:
    #             cmds.setAttr(obj + "." + attr, visibility)
    #         except Exception as e:
    #             logging.error('Cannot change visibility for : %s' % obj)


# TODO: return old statement of attrs
def reinit_renderStats(mesh):
    """
    Reinit renderstats of mesh
    :param: mesh
    """
    attr_on = [
        "castsShadows",
        "receiveShadows",
        "motionBlur",
        "primaryVisibility",
        "smoothShading",
        "visibleInReflections",
        "visibleInRefractions",
    ]
    attr_off = [
        "holdOut"
    ]
    shape = read_nodes.get_shape_or_transform(mesh)
    for attr in attr_on:
        if cmds.getAttr(shape + "." + attr) is False:
            logging.info('Attribute of {} have been reinit {}'.format(mesh, attr))
            cmds.setAttr(shape + "." + attr, True)
    for attr in attr_off:
        if cmds.getAttr(shape + "." + attr) is True:
            logging.info('Attribute of {} have been reinit {}'.format(mesh, attr))
            cmds.setAttr(shape + "." + attr, False)


# TODO: fix arguments, use snakecase
# TODO: return the list of node that have been change
def change_visibility(meshList, state=True):
    """
    Change visibility for meshes
    :param: meshList
    :param: state => True by default
    """
    for node in meshList:
        try:
            cmds.setAttr(node + ".visibility", state)
        except Exception as e:
            logging.warning(e)


# TODO: return if attribute has been properly set or not
# TODO: snakecase
def add_custom_attr(node, attrName, content):
    """
    Add custom attr on node. Must be string
    :param: node
    :param: attrName
    :param: content
    """
    if cmds.objExists(node):
        if not cmds.attributeQuery(attrName, n=node, ex=True):
            cmds.addAttr(node, ln=attrName, sn=attrName, dt="string")
        # Unlock attr
        cmds.setAttr("%s.%s" % (node, attrName), l=False)
        cmds.setAttr("%s.%s" % (node, attrName), str(content), type="string")
        # Lock attr
        cmds.setAttr("%s.%s" % (node, attrName), l=True)
    else:
        logging.warning('Cannot create attribute, node doest exist!')


# TODO fix arguments + vars: use snakecase
def store_shaders_assign(topNode):
    """
    Store the shader assignation and attribute values in the top node notes.
    :param: topNode => string, the top node where to store data
    :return: assigned_shaders =>shader assignation and attribute values.
    :rtype: string
    """
    # Store the shader assignation inside the top node's notes.
    cmds.select(topNode, replace=True)
    topNode = cmds.ls(sl=True)
    assigned_shaders = read_shaders.get_shading_grp_assignations()
    attr_name = 'notes'
    if len(topNode) != 1:
        logging.error('More than one top node to store assigned shaders!!')
    else:
        topNode = topNode[0]
        add_custom_attr(node=topNode, attrName=attr_name, content=str(assigned_shaders))
    return assigned_shaders


# TODO: put others possible type of setAttr
def set_attr(name, value):
    """
    WIP
    Set attribute value depending on the value type.
    :param name: the name of the attribute ("object_name.attribute_name")
    :type name: str
    :param value: the value to set
    :type value: [list, ]
    """
    if isinstance(value, list) and len(value) == 3:
        cmds.setAttr(name, value[0], value[1], value[2], type='double3')
