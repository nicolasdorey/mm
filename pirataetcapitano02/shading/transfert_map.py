# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       Transfert map tool.
#
#   Update  1.0.0 :     Interface build.
#
#   KnownBugs :         Not tested in batch.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import logging
import webbrowser
import subprocess

try:
    import maya.cmds as cmds
except ImportError:
    pass

from ....studio.libs.reads import nodes as read_nodes
from ....studio.libs.reads import shaders as read_shaders
from ....studio.libs.reads import references as read_references
from ....studio.libs.updates import nodes as update_nodes
from ....studio.libs.updates import references as update_references
# TODO: remove update_scene impors after removing format_log
from ....studio.libs.updates import scene as update_scene

from ..modeling import detect_sym_auto as dsa

# TODO: Change OUPUTPATH to ../photoshop/TransfertMap/

class TransfertMap(object):
    """
    Transfert map tool with interface.
    To use the tool in batch mode, use TransfertMap.launch_tm_on_pairs(self.excludList) => not tested.

    This tool allows to transfert map data into all elements of both source and destination.
    /!/ Source must be indicated with a prefix on Top node.

    - Find auto pairs (from detect sym auto tool)
    - Launch transfert map on pairs (remove excluded meshes)
    - For each pair {source} // {destination}:
        - Get shader (MUST BE redshift material) // files of shader (diffuse, bump etc)
        - Remove excluded maps
        - Create a lambert and connect actual file
        - Move current udim to 1001 to launch TM.

    So, for each file, for each udim, multiple files are created.
    Output : {file}.{udim_src}.{udim_dst}.exr
    """

    def __init__(self):
        self.BASE_PATH = "L:/Millimages/PirataEtCapitano/PirataEtCapitano02/ProjectFiles/assets"
        self.OUTPATH = str(self.BASE_PATH)
        self.size = 2048
        self.prefix = "SRC"
        self.excludedMap = "msk"

        for sel in cmds.ls(type="RedshiftMaterial"):
            self.fixShadingNodes(sel)

        for sel in cmds.ls(type="file"):
            self.fixShadingNodes(sel)

        mayaFileFullName = os.path.basename(cmds.file(sn=True, q=True))
        self.mayaFile = mayaFileFullName.split('.m')[0]

        self.log_file = r"{}\TM_{}.log"
        base_log = r"C:\Shotgun\mm_profiles\PirataEtCapitano02\logs"
        self.log_file = self.log_file.format(base_log, self.mayaFile)
        if os.path.exists(base_log) is False:
            os.mkdir(base_log)

        # TODO: use logger from tk-framework-common
        update_scene.format_log(log_file=self.log_file)

        namespaces = read_references.list_namespaces()
        if namespaces:
            update_references.remove_namespaces()

        all_meshes = read_nodes.list_all_meshes()
        update_nodes.unsmooth_meshes(meshes=all_meshes, state=0)

        ref = read_references.list_references()
        if ref:
            logging.error('Please remove reference')
        else:
            self.transfert_map_ui()

    def transfert_map_ui(self):
        """
        Ui functions
        """
        logging.info("...LAUNCHING WINDOW....")

        winName = "Transfert Map"
        if cmds.window(winName, exists=True):
            cmds.deleteUI(winName, window=True)

        w_width = 500
        w_height = 600
        btn_height = 30

        self.fenetre = cmds.window(
            title=winName, widthHeight=(w_width, w_height), menuBar=True)

        # menu bar
        self.menu = cmds.menu(label='Help', tearOff=True)
        cmds.menuItem(label='Help page', command=lambda x: self.launch_help())

        # ########### first part of UI ############
        cmds.scrollLayout('scrollLayout', h=w_height)
        cmds.text(label="")

        form = cmds.formLayout(numberOfDivisions=10, h=btn_height * 2 + 30, w=w_width)
        self.path_field = cmds.textFieldGrp(label="Current Path : ", text=self.OUTPATH)
        self.browse_btn = cmds.button(label="Browse", c=lambda x: self.browse_action())
        self.uvSetField = cmds.textFieldGrp(label='Current Uv Set :', text='map1', cc=lambda x: self.get_text_field(textField=self.uvSetField), w=250)
        self.size_field = cmds.textFieldGrp(label='Current size   :', text=str(self.size), w=250)
        self.src_prefix = cmds.textFieldGrp(label='Prefix of source group   :', statusBarMessage="Prefix of the source top node", text=self.prefix, w=190)
        self.excludedMap_field = cmds.textFieldGrp(label='Excluded maps   :', statusBarMessage="Map to exclude when readind the shader", text=self.excludedMap, w=250)

        # adding elements to form layout
        cmds.formLayout(form, edit=True, attachForm=[(self.path_field, 'top', 0), (self.browse_btn, 'top', 0), (self.uvSetField, "top", btn_height), (self.size_field, "top", btn_height),
                                                     (self.src_prefix, "top", btn_height * 2), (self.path_field, 'left', -60), (self.browse_btn, "left", 340), (self.uvSetField, "left", -60),
                                                     (self.size_field, "left", 140), (self.src_prefix, "left", -6), (self.excludedMap_field, "top", btn_height * 2),
                                                     (self.excludedMap_field, "left", 140)])

        # seperator
        cmds.setParent('..')
        cmds.text(label="")
        cmds.rowColumnLayout(numberOfColumns=2, columnAlign=(1, 'right'), columnAttach=(2, 'both', 0), columnWidth=(2, w_width))
        cmds.text(label="")
        cmds.separator(height=5, style='doubleDash')
        cmds.setParent('..')

        # custom pairs check box
        cmds.gridLayout(numberOfColumns=2, cellWidthHeight=(150, 20))
        cmds.text(label="Selection custom pairs  ")
        self.custom_cb = cmds.checkBox(label="", value=0, cc=lambda x: self.change_checkBox(inputCb=self.custom_cb))
        cmds.text(label="")
        cmds.setParent('..')

        # source and destination fields and buttons
        form = cmds.formLayout(numberOfDivisions=100, h=100)
        path_src_w = 250
        self.src_txt = cmds.textField(vis=False)
        self.src_field = cmds.textFieldGrp(self.src_txt, text="", editable=False, w=path_src_w, backgroundColor=[0.2, 0.2, 0.2])
        self.src_btn = cmds.button(label="Add Source", c=lambda x: self.add_custom_mesh(textField=self.src_field))

        self.dst_txt = cmds.textField(vis=False)
        self.dst_field = cmds.textFieldGrp(self.dst_txt, text="", editable=False, w=path_src_w, backgroundColor=[0.2, 0.2, 0.2])
        self.dst_btn = cmds.button(label="Add Destination", c=lambda x: self.add_custom_mesh(textField=self.dst_field))

        cmds.formLayout(form, edit=True, attachForm=[(self.src_field, 'top', 0), (self.src_btn, 'top', 0), (self.src_btn, "left", path_src_w + 10),
                        (self.dst_field, 'top', btn_height * 2 + 10), (self.dst_btn, 'top', btn_height * 2 + 10), (self.dst_btn, "left", path_src_w + 10)])

        # seperator
        cmds.setParent('..')
        cmds.rowColumnLayout(numberOfColumns=2, columnAlign=(1, 'right'), columnAttach=(2, 'both', 0), columnWidth=(2, w_width))
        cmds.text(label="")
        cmds.separator(height=5, style='doubleDash')
        cmds.setParent('..')

        # ########### 3 part of UI ############
        cmds.gridLayout(numberOfColumns=2, cellWidthHeight=(150, 50))
        # auto pairs with excluded list
        cmds.text(label="Selection auto pairs  ")
        self.auto_cb = cmds.checkBox(label="", value=1, cc=lambda x: self.change_checkBox(inputCb=self.auto_cb))
        cmds.setParent('..')

        form = cmds.formLayout(numberOfDivisions=100, h=180)
        cmds.text(label=" Exclude List :  ")
        scroll_w = 300
        scroll_h = 150
        self.scroll_list = cmds.textScrollList(w=scroll_w, h=scroll_h)

        self.add_exclud_btn = cmds.button(label="Add Excluded", c=lambda x: self.update_scroll())
        cmds.formLayout(form, edit=True, attachForm=[(self.scroll_list, 'top', 0), (self.add_exclud_btn, 'top', scroll_h / 2), (self.add_exclud_btn, 'left', scroll_w + 10)])

        # seperator
        cmds.setParent('..')
        cmds.rowColumnLayout(numberOfColumns=2, columnAlign=(1, 'right'), columnAttach=(2, 'both', 0), columnWidth=(2, w_width))
        cmds.separator(height=5, style='doubleDash')
        cmds.setParent('..')

        # ########### 4 part of UI ############
        form = cmds.formLayout(numberOfDivisions=10, h=50)
        # buttons launch and log
        self.launch_btn = cmds.button(label='Launch ! ', c=lambda x: self.launch_function())
        self.log_btn = cmds.button(label='Open log... ', c=lambda x: self.open_log())

        cmds.formLayout(form, edit=True, attachForm=[(self.launch_btn, 'top', 0), (self.log_btn, 'top', 0),
                                                     (self.launch_btn, 'left', 20), (self.log_btn, 'left', 150)])

        cmds.setParent('..')
        self.checkBoxes = [self.custom_cb, self.auto_cb]

        cmds.showWindow(self.fenetre)

    def browse_action(self):
        """
        Browse button to get a new path
        """
        self.browse_return = cmds.fileDialog2(fm=3, dialogStyle=1)
        self.browse_return = str(self.browse_return[0])
        logging.info("Folder selected : {} ".format(self.browse_return))
        self.update_text(textField=self.path_field, newField=self.browse_return)

    def update_text(self, textField, newField):
        """"
        Update text group with new field
        """
        cmds.textFieldGrp(textField, e=True, text=newField)

    def change_checkBox(self, inputCb):
        """"
        Configurations with check boxes.
        - If custom check box is checked : scroll list cb is not checked and scroll list is empty
        - If auto pairs check box is checked : fields of source and dest are empty and custom check box is not checked
        """
        for cb in self.checkBoxes:
            if cb != inputCb:
                cmds.checkBox(cb, edit=1, value=0)

            if cb == self.custom_cb:
                if cmds.checkBox(cb, value=True, q=True) is True:
                    cmds.textScrollList(self.scroll_list, edit=True, removeAll=True)

            elif cb == self.auto_cb:
                if cmds.checkBox(cb, value=True, q=True) is True:
                    cmds.textFieldGrp(self.src_field, edit=True, text="")
                    cmds.textFieldGrp(self.dst_field, edit=True, text="")

    def add_custom_mesh(self, textField):
        """
        Add a mesh name when button add pressed
        """
        ls = cmds.ls(sl=True, transforms=True, long=True)
        if len(ls) != 1:
            cmds.confirmDialog(title="Warning", message="Please select only One mesh")
        else:
            self.update_text(textField, ls[0])
        cmds.checkBox(self.custom_cb, edit=True, value=True)
        self.change_checkBox(self.custom_cb)

    def update_scroll(self):
        """
        Update scroll list with meshes selection
        """
        ls = cmds.ls(sl=True, transforms=True, long=True)
        cmds.textScrollList(self.scroll_list, edit=True, removeAll=True, append=ls)

    def get_text_field(self, textField, *args):
        """
        Get content of given field
        """
        label = cmds.textFieldGrp(textField, q=True, label=True)
        text = cmds.textFieldGrp(textField, q=True, text=True)
        logging.info("Current {} : {}".format(label, text))
        return text

    def open_log(self):
        """
        Open log file
        """
        logging.info("log path... {}".format(self.log_file))
        if os.path.isfile(self.log_file):
            subprocess.Popen(['notepad', self.log_file])
        else:
            cmds.confirmDialog(title="Warning", m="The log {} doesnt exists! Did you launch?".format(self.log_file))

    def launch_function(self):
        """
        Actions when button launch is pressed.
        - Get of all each fields
        - Launch transfert is custom pairs is checked
        - Launch transfert map on pairs if auto pairs is checked
        """
        logging.info('Lauching actions..')
        # get fields contents
        self.OUTPATH = self.get_text_field(textField=self.path_field)

        if self.OUTPATH == self.BASE_PATH:
            cmds.confirmDialog(title='Confirm', message='PLEASE CUSTOM YOUR PATH!', button=['Ok'], cancelButton='Ok', dismissString='Ok')
        else:
            if self.OUTPATH.endswith('/') is False:
                self.OUTPATH = self.OUTPATH + "/"

            self.uvSet = self.get_text_field(textField=self.uvSetField)
            self.size = int(self.get_text_field(textField=self.size_field))
            self.prefix = self.get_text_field(textField=self.src_prefix)
            self.excludedMap = self.get_text_field(textField=self.excludedMap_field)

            custom_state = cmds.checkBox(self.custom_cb, value=True, q=True)
            auto_state = cmds.checkBox(self.auto_cb, value=True, q=True)

            if not auto_state and not custom_state:
                cmds.confirmDialog(title="Warning", message="Please check at least one category!!")
                return

            if custom_state and not auto_state:
                logging.info('custom state : {}'.format(custom_state))
                self.src = self.get_text_field(textField=self.src_field)
                self.dst = self.get_text_field(textField=self.dst_field)
                if self.src == self.dst:
                    cmds.confirmDialog(title="Warning", message="Source and destination are identical!")
                    return
                else:
                    self.launch_transfert()
                    logging.info('**********************End of Transfer map on custom pairs******************')

            if auto_state and not custom_state:
                logging.info('auto state : {}'.format(auto_state))
                excludedList = cmds.textScrollList(self.scroll_list, allItems=True, q=True)
                if excludedList:
                    excludedList = [cmds.ls(mesh, long=True)[0] for mesh in excludedList if mesh is not None]
                self.launch_tm_on_pairs(excludList=excludedList)

    def connect_file_to_tm_lambert(self, lamb_name, mesh):
        """
        Create a lambert with file connected and assign to mesh
        """
        if cmds.objExists(lamb_name) is False:
            lamb = cmds.shadingNode("lambert", name=lamb_name, asShader=True)
        else:
            lamb = cmds.ls(lamb_name)[0]

        cmds.connectAttr(self.file + '.outColor', lamb + '.color', f=True)
        cmds.select(mesh, r=True)
        cmds.hyperShade(assign=lamb_name)

    def transfert_map(self, mapType="diffuseRGB"):
        """
        Maya command for transfert map
        """
        cmds.surfaceSampler(mapOutput=mapType, filename=self.fileName, fileFormat='exr', source=self.src, target=self.dst,
                            mh=self.size, mw=self.size, ignoreTransforms=True, uvSet=self.uvSet, mapSpace="tangent", searchCage="",
                            searchOffset=0, max=1, useGeometryNormals=True, searchMethod=0, shadows=1, superSampling=2,
                            filterType=0, filterSize=3, overscan=1, ignoreMirroredFaces=0, flipU=0, flipV=0)

    def launch_transfert(self):
        """
        Launch transfert map for a given src and a dst.
        -Get files of shader of source
        -For each file, plug into a lambert, assigned to src
        -Move udim (1001 to 1099), and current udim to 1001 for both src and dst
        -For each udim, launch transfert.
        :param src : must be mesh source.
        :param dst : must be destination mesh.
        :param excludedMap : if keyworkd of excludedMap is in map list, exclusion of map list.
        """
        logging.info('Launching transfert map for %s // %s' % (self.src, self.dst))
        self.shader = read_shaders.get_mesh_shader(self.src)
        if not self.shader:
            logging.info('No shader found on: {}'.format(self.src))
            return

        logging.info('Shader found: {}'.format(self.shader))
        filesOfShdr = read_shaders.list_nodeType_of_shader(shader=self.shader, nodeType="file")

        if type(self.excludedMap) == 'string':
            self.excludedMap = self.excludedMap.split(',')

        # removing excluded map
        for file in filesOfShdr:
            if self.excludedMap:
                fileLow = file.lower()
                if type(self.excludedMap) == list:
                    for excluded in self.excludedMap:
                        if excluded in fileLow:
                            logging.info('Removing excluded map of list {}'.format(excluded))
                            filesOfShdr.remove(file)
                else:
                    if self.excludedMap in fileLow:
                        logging.info('Removing excluded map  {}'.format(self.excludedMap))
                        filesOfShdr.remove(file)

        logging.info('Files of shaders found : {}'.format(filesOfShdr))

        for file in filesOfShdr:
            self.file = file
            if len(filesOfShdr) == 0:
                logging.error('No map found!')

            else:
                logging.info("Treating current file : {}".format(file))
                # get udims of src and dst
                udimSrc = read_nodes.get_udims_list(mesh=self.src)
                udimDst = read_nodes.get_udims_list(mesh=self.dst)
                # get uvmode of current file
                uvMode = cmds.getAttr('{}.uvTilingMode'.format(file))

                # connect file to lambert
                lamb_name = "TM_Lambert"
                self.connect_file_to_tm_lambert(lamb_name=lamb_name, mesh=self.src)

                for udimD in udimDst:
                    logging.info("Destination udim: {}".format(udimD))
                    # if current udim is not 1001, transfering 1001 to 1099
                    if udimD != 1001:
                        if 1001 in udimDst:
                            update_nodes.move_uv(mesh=self.dst, udimSrc=1001, udimDst=1099)
                            logging.info('Base udim 1001 has been moved')
                        # then transfering current udim to 1001
                        update_nodes.move_uv(mesh=self.dst, udimSrc=udimD, udimDst=1001)

                    for udim in udimSrc:
                        logging.info('Current source udim : {}'.format(udim))
                        shortNameDst = cmds.ls(self.dst, sn=True)[0].split('|')[-1]
                        self.fileName = self.OUTPATH + shortNameDst.replace('|', '_') + "_" + file + "." + str(udim) + "." + str(udimD)
                        logging.info('Ouput file name : {}'.format(self.fileName))

                        if uvMode == 3:  # uv mode mari
                            cmds.setAttr('{}.uvTilingMode'.format(file), 0)  # changing to No Udim

                        imageName = cmds.getAttr('{}.fileTextureName'.format(file))
                        udimToReplace = imageName.split('.')[-2]
                        newUdimCode = str(udim)
                        newimageName = imageName.replace(udimToReplace, newUdimCode)
                        logging.info('Changing file to current udim %s' % file)
                        cmds.setAttr('{}.fileTextureName'.format(file), newimageName, type="string")

                        # setter file avec udim en cours
                        if udim != 1001:
                            if 1001 in udimSrc:
                                # move udim in 1001 far far away
                                logging.info("Moving Uv of 1001 to 1101")
                                update_nodes.move_uv(mesh=self.src, udimSrc=1001, udimDst=1099)

                            # move current udim in 1001
                            logging.info("Moving uv %d to 1001" % udim)
                            update_nodes.move_uv(mesh=self.src, udimSrc=udim, udimDst=1001)

                        logging.info('Launching transfert map maya operation....')
                        self.transfert_map()

                        if udim != 1001:
                            logging.info("Moving uv %d back" % udim)
                            update_nodes.move_uv(mesh=self.src, udimSrc=1001, udimDst=udim)
                            if 1001 in udimDst:
                                logging.info("Moving uv %d back" % 1001)
                                update_nodes.move_uv(mesh=self.src, udimSrc=1099, udimDst=1001)

                    if udimD != 1001:
                        update_nodes.move_uv(mesh=self.dst, udimSrc=1001, udimDst=udimD)
                        update_nodes.move_uv(mesh=self.dst, udimSrc=1099, udimDst=1001)

    def launch_tm_on_pairs(self, excludList=[]):
        """
        Get pairs and launching on each source, dst
        """
        topNodes = read_nodes.get_top_node()
        logging.info('top nodes :{}'.format(topNodes))

        if len(topNodes) != 2:
            logging.error('Scene has more or less 2 top nodes!!!')
        else:
            # listing meshes of both top nodes
            meshOfTopNoes1 = cmds.select(topNodes[0], hi=True)
            meshOfTopNoes1 = read_nodes.list_all_meshes(nodeList=cmds.ls(sl=True, long=True))

            meshOfTopNoes2 = cmds.select(topNodes[1], hi=True)
            meshOfTopNoes2 = read_nodes.list_all_meshes(nodeList=cmds.ls(sl=True, long=True))

        dictOfPairs = {}
        logging.info("mesh of top nodes {} // {}".format(meshOfTopNoes1, meshOfTopNoes2))
        logging.info('Exclued list : {}'.format(excludList))
        if not excludList:
            excludList = []

        # populating dict of pairs.
        for mesh in meshOfTopNoes1:
            if mesh not in excludList:
                for next_mesh in meshOfTopNoes2:
                    if next_mesh not in excludList:
                        if mesh not in dictOfPairs:
                            if dsa.compare_two_meshes(mesh01=mesh, mesh02=next_mesh, centred=True) is True:
                                dictOfPairs[mesh] = next_mesh

        logging.info('dict of pairs: {}'.format(dictOfPairs))

        # launching tm of pairs found
        for mesh, next_mesh in dictOfPairs.items():
            if mesh is not None:
                if self.prefix in mesh:
                    self.src = mesh
                    self.dst = next_mesh
                else:
                    self.src = next_mesh
                    self.dst = mesh

                logging.info('src // dst : {} // {}'.format(self.src, self.dst))
                self.launch_transfert()

        logging.info('**********************End of Transfer map on pairs******************')

    def fixShadingNodes(self, inNode):
        """
        Fixing missing nodes in shading space
        """
        target = None
        nodeType = cmds.nodeType(inNode)
        if cmds.getClassification(nodeType, satisfies="shader"):
            target = 'defaultShaderList1.shaders'
        elif cmds.getClassification(nodeType, satisfies="texture"):
            target = 'defaultTextureList1.textures'
        elif cmds.getClassification(nodeType, satisfies="utility"):
            target = 'defaultRenderUtilityList1.utilities'
        if target:
            try:
                cmds.connectAttr(inNode + '.message', target, na=True, force=True)
            except Exception as e:
                logging.warning(e)
                pass

    def launch_help(self):
        """Launch hackmd page for documentation."""
        url = 'https://hackmd.io/MbWKRKoaRwqAWaD2iWfdnw'
        webbrowser.open_new(url)


if __name__ == "__main__":
    TransfertMap()
