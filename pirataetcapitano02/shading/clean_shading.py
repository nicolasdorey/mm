# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       Clean shading stuff
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import re
import logging

try:
    import maya.cmds as cmds
except ImportError:
    pass

from ....studio.libs.reads import nodes as read_nodes
from ....studio.libs.reads import shaders as read_shaders
from ....studio.libs.reads import references as read_references
from ....studio.libs.deletes import nodes as delete_nodes

# TODO: VERY IMPORTANT! Extract functions to the right libraries!
# TODO: remove RotatingFileHandler import after removing log_config
from logging.handlers import RotatingFileHandler


# TODO: delete this method, use logger in tk-framexork-common
def log_config():
    folder_log = r"C:\Shotgun\mm_profile\pirata2\{}.log"
    maya_file = cmds.file(sn=True, q=True)
    file_name = os.path.basename(maya_file).split('.')[0]

    formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
    logger = logging.getLogger()

    file_handler = RotatingFileHandler(folder_log.format(file_name), 'w', 1000000, 1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def get_sss_shaders(mtls):
    """
    Get shaders that have sss
    :param: mtls
    :return: sss_shrs
    :rtype: list
    """
    sss_shrs = []
    for mtl in mtls:
        if cmds.objectType(mtl) == "RedshiftMaterial":
            # sss amount
            attr = mtl + ".ms_amount"
            ms = cmds.getAttr(attr)
            if ms > 0:
                logging.info("Values of SSS found: {} // {}".format(mtl, ms))
                sss_shrs.append(mtl)
    logging.info("Nb of Shaders with SSS :{}".format(len(sss_shrs)))
    return sss_shrs


def reinit_sss(sss_mtls):
    """
    Reinit sss amount in RedShiftMaterial
    :param: sss_mtls
    """
    for mtl in sss_mtls:
        attr = mtl + ".ms_amount"
        cmds.setAttr(attr, 0)
    logging.info("All Shader's SSS have been reinit to 0! {}".format(sss_mtls))


# TODO: snakecase arg
def has_displacement(shadingEngines):
    """
    Return True or False if displacementShader connected to shadingEngine
    It does not work with initialShadingGroup connection
    :param: shadingEngines
    :return True or False
    :rtype: boolean
    """
    for shadingEngine in shadingEngines:
        disp_co = cmds.listConnections('{}.displacementShader'.format(shadingEngine))
        rs_disp = cmds.listConnections('{}.rsDisplacementShader'.format(shadingEngine))
        if disp_co:
            return True
        else:
            return False

        if rs_disp:
            return True
        else:
            return False


def get_active_disp_nodes(all_disp):
    """
    Get RedShiftDisp nodes
    :return: disp_nodes
    :rtype: list
    """
    disp_nodes = []
    for disp in all_disp:
        scale = disp + ".scale"
        value_scale = cmds.getAttr(scale)
        logging.info("Values of displace: {} // {}".format(disp, value_scale))
        disp_nodes.append(disp)
    logging.info("Nb of Disp nodes :{}".format(len(disp_nodes)))

    return disp_nodes


def remove_disp(disp_nodes):
    """
    Remove disp nodes and file
    :param: disp_nodes
    """
    logging.warning("DELETING DISP NODES AND UNUSED NODES : {}".format(disp_nodes))
    for disp in disp_nodes:
        if cmds.objExists(disp):
            try:
                cmds.delete(disp)
            except Exception as e:
                logging.warning("Cannot delete node: {}".format(disp))
                logging.warning(e)
    delete_nodes.delete_unused_nodes()


# TODO: snakecase args
def check_nomenclature(assetName, variationName):
    """
    :param: assetName, variationName
    """
    corresp = {
        "RedshiftAmbientOcclusion": "_RsAO",
        "RedshifAttributeLookup": "_RsAttL",
        "RedshiftBumpBlender": "_RsBmpBld",
        "RedshiftBumpMap": "_RsBmp",
        "RedshiftCameraMap": "_RsCM",
        "RedshiftColorCorrection": "_RsCC",
        "RedshiftColorLayer": "_RsCL",
        "RedshiftCurvature": "_RsCrv",
        "RedshiftDisplacement": "_RsDsp",
        "RedshiftDisplacementBlender": "_RsDspBld",
        "RedshiftFresnel": "_RsFr",
        "RedshiftHairPosition": "_RsHP",
        "RedshiftHairRandomColor": "_RsHRC",
        "RedshiftNoise": "_RsNse",
        "RedshiftNormalMap": "_RsNrmM",
        "RedshiftRaySwitch": "_RsRySw",
        "RedshiftRoundCorner": "_RsRC",
        "RedshiftShave": "_RsShv",
        "RedshiftMaterial": "_Sh",
        "RedshiftState": "_RsStt",
        "RedshiftStoreColorToAOV": "_RsSCTAOV",
        "RedshiftStoreIntegerToAOV": "_RsSITAOV",
        "RedshiftStoreScalarToAOV": "_RsSSTAOV",
        "RedshiftTriPlanar": "_RsTP",
        "RedshiftUserDataColor": "_RsUDC",
        "RedshiftUserDataInteger": "_RsUDI",
        "RedshiftUserDataScalar": "_RsUDS",
        "RedshiftUserDataVector": "_RsUDV",
        "RedshiftVertexColor": "_RsVC",
        "RedshiftWireframe": "_RsWf",
        "file": "_File",
        "lambert": "_Vp",
        "ramp": "_Ramp",
        "place2dTexture": "_P2DT",
        "remapHsv": "_RemapHsv"
    }

    text_types = ["_Dif", "_Spc", "_Bmp", "_Facial", "_Dsp"]
    all = cmds.ls()
    defaut = read_nodes.list_default_nodes()
    all = [obj for obj in all if obj not in defaut]

    for obj in all:
        name_match = True
        nom = "{AssetName}_{VariationName}_{ShaderName}_{ExtraName}_{Padding}_{Type}"
        obj_type = cmds.objectType(obj)
        if obj_type in corresp.keys():
            # suffixe = "_" + obj.split('_')[-1]
            right_suffixe = corresp[obj_type].replace('_', '')
            ideal_name = nom.format(AssetName=assetName, VariationName=variationName, ShaderName="ShaderName", ExtraName="ExtraName", Padding="01", Type=right_suffixe)

            if obj != ideal_name:
                name_match = False
                # check for extra pass name
                if len(obj.split('_')) > 6:
                    suffixe = "_" + obj.split('_')[-1]
                    for text_typ in text_types:
                        if text_typ == suffixe:
                            ideal_name = ideal_name + text_typ
                            if obj == ideal_name:
                                name_match = True

                # check for increement
                if name_match is False:
                    digits = re.compile(r'_\d\d_')
                    match = digits.search(obj)
                    if match is not None:
                        incre_name = match.group()
                        ideal_name = ideal_name.replace('_01_', incre_name)
                        if ideal_name == obj:
                            name_match = True

            if name_match is False:
                logging.info("ERROR! wrong naming: {}".format(obj))
                logging.info('IDEAL NAME         : {}'.format(ideal_name))

    logging.info("End of check")


def is_shading_node(obj):
    """
    Return True is obj is reshift shading node
    :param: obj
    :return: right_type
    :rtype: boolean

    """
    right_type = False
    corresp = [
        "RedshiftAmbientOcclusion", "RedshifAttributeLookup", "RedshiftBumpBlender", "RedshiftBumpMap",
        "RedshiftCameraMap", "RedshiftColorCorrection", "RedshiftColorLayer", "RedshiftCurvature", "RedshiftDisplacement",
        "RedshiftDisplacementBlender", "RedshiftFresnel", "RedshiftHairPosition", "RedshiftHairRandomColor", "RedshiftNoise",
        "RedshiftNormalMap", "RedshiftRaySwitch", "RedshiftRoundCorner", "RedshiftShave", "RedshiftMaterial",
        "RedshiftState", "RedshiftStoreColorToAOV", "RedshiftStoreIntegerToAOV", "RedshiftStoreScalarToAOV",
        "RedshiftTriPlanar", "RedshiftUserDataColor", "RedshiftUserDataInteger", "RedshiftUserDataScalar",
        "RedshiftUserDataVector", "RedshiftVertexColor", "RedshiftWireframe", "file", "lambert", "ramp", "place2dTexture"
    ]
    if cmds.objExists(obj):
        if cmds.objectType(obj) in corresp:
            right_type = True

    return right_type


# TODO: snakecase args
def rename_child(currentNode, lvl, assetName, variationName):
    """
    :param: currentNode, lvl, assetName, variationName
    """
    if is_shading_node(currentNode):
        print "current Node", currentNode, "level", lvl
        if currentNode.startswith('AssetName'):
            new_name = currentNode.replace('AssetName', assetName)
            new_name = new_name.replace('VariationName', variationName)
            # try:
            cmds.rename(currentNode, new_name)
            print "renaming ", currentNode, new_name
            currentNode = new_name

            # except:
            #     logging.info('cannot rename %s' % currentNode)

        childs = cmds.listConnections(currentNode, d=True)

        # print "child type", cmds.objectType(currentNode)
        if lvl <= 10:
            for child in childs:
                if cmds.objExists(child):
                    rename_child(currentNode=child, lvl=lvl + 1, assetName=assetName, variationName=variationName)


# TODO: remove hardcoded path if possible
def rename_shaders(reinit=False):
    """
    :param: reinit=False
    """
    scene_name = os.path.basename(cmds.file(sn=True, q=True))
    asset_name = scene_name.split('_')[0]
    variation_name = scene_name.split('_')[1]

    if reinit:
        cmds.file(new=True, f=True)
        MODULE = "P:/SHOTGUN/Pirata2/assets/SHADefault01/SHADefault01_Character/SHA/work/maya/SHADefault01_Character.ma"
        current_shaders = read_shaders.list_materials()

        mtl_importes = cmds.file(MODULE, i=True, uns=True, mergeNamespaceWithParent=False)
        import_shaders = list(set(read_shaders.list_materials()) - set(current_shaders))

    else:
        namesspaces = read_references.list_namespaces()
        for obj in cmds.ls():
            for ns in namesspaces:
                if obj.startswith(ns):
                    new_name = obj.replace(ns, "")
                    cmds.rename(obj, new_name)

        import_shaders = read_shaders.list_materials()

        for shdr in import_shaders:
            # if shdr.startswith('AssetName'):
            print "*" * 100
            print "SHADER", shdr
            childs = cmds.listConnections(shdr, d=True)
            if childs:
                for child in childs:
                    if is_shading_node(child):
                        rename_child(currentNode=child, lvl=1, assetName=asset_name, variationName=variation_name)
                        # check_nomenclature()



if __name__ == "__main__":
    log_config()
    # mtls = read_shaders.list_materials()
    # all_disp = cmds.ls(type="RedshiftDisplacement")
    # sss_mtls = get_sss_shaders(mtls)
    # reinit_sss(sss_mtls)
    # disp_nodes = get_active_disp_nodes(all_disp)
    # remove_disp(disp_nodes)
    rename_shaders()
    logging.shutdown()
