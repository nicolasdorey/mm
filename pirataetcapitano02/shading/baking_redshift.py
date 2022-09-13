# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       Baking redshift
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         Some problem of baking, output grey weird.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import logging
import shutil
import subprocess
import webbrowser

try:
    import maya.cmds as cmds
except ImportError:
    pass

from ....studio.libs.reads import nodes as read_nodes
from ....studio.libs.reads import shaders as read_shaders
from ....studio.libs.reads import references as read_references
from ....studio.libs.reads import scene as read_scene
from ....studio.libs.updates import nodes as update_nodes
from ....studio.libs.updates import references as update_references
from ....studio.libs.updates import scene as update_scene
from ....studio.libs.deletes import scene as delete_scene


class BakingRedshift(object):
    """
    Baking redshift tool with interface.
    Output : {file}.{udim_src}..exr
    """

    def __init__(self):
        """
        Setup dirs, bake size, load redshift, set color management to linear,
        unsmooth meshes and unhide groups
        """
        self.size = 2048
        # TODO: check via shotgun the lastest publish of arbo
        utility_path = "L:/Millimages/PirataEtCapitano/PirataEtCapitano02/ProjectFiles/assets/SHAUtilities01/SHAUtilities01_Fresnel/SHA/publish/maya"
        self.ARBO = read_scene.get_lastest_version_digit(path=utility_path, extention="ma")
        self.BASE_PATH = "L:/Millimages/PirataEtCapitano/PirataEtCapitano02/ProjectFiles/assets"
        self.OUTPATH = str(self.BASE_PATH)

        self.mayaFileFullName = os.path.basename(cmds.file(sn=True, q=True))
        self.mayaFile = self.mayaFileFullName.split('.m')[0]

        self.assetName = self.mayaFile.split('_')[0]
        self.variationName = self.mayaFile.split('_')[1]

        self.log_file = r"{}\BAKE_{}.log"
        base_log = "C:\Shotgun\mm_profiles\PirataEtCapitano02\logs"
        self.log_file = self.log_file.format(base_log, self.mayaFile)
        if os.path.exists(base_log) is False:
            os.mkdir(base_log)

        # TODO: delete this method, use logger in tk-framexork-common
        update_scene.format_log(log_file=self.log_file)

        # load redshift and change color management to linear
        update_scene.load_plugin('redshift4maya')
        update_scene.setup_color_management()

        namespaces = read_references.list_namespaces()
        if namespaces:
            update_references.remove_namespaces()

        all_meshes = read_nodes.list_all_meshes()
        update_nodes.unsmooth_meshes(meshes=all_meshes, state=0)
        # force loading and setup redshift
        update_scene.load_plugin('redshift4maya')
        update_scene.set_renderer('redshift')

        # self.fix_grp_visibility()
        update_nodes.change_visibility(meshList=read_nodes.list_all_groups(), state=True)

        ref = read_references.list_references()
        if ref:
            logging.error('Please remove reference')
        else:
            self.baking_redshift_ui()

    def baking_redshift_ui(self):
        """
        Ui functions
        """
        logging.info("...LAUNCHING WINDOW....")

        winName = "Baking Redshift"
        if cmds.window(winName, exists=True):
            cmds.deleteUI(winName, window=True)

        w_width = 450
        w_height = 500
        btn_height = 30

        self.fenetre = cmds.window(title=winName, widthHeight=(w_width, w_height), menuBar=True)

        # menu bar
        self.menu = cmds.menu(label='Help', tearOff=True)
        cmds.menuItem(label='Help page', command=lambda x: self.launch_help())

        # ########### first part of UI ############
        cmds.scrollLayout('scrollLayout', h=w_height)
        cmds.text(label="")

        form = cmds.formLayout(numberOfDivisions=10, h=btn_height * 2 + 30, w=w_width)
        self.path_field = cmds.textFieldGrp(label="Current Path : ", text=self.OUTPATH)
        self.browse_btn = cmds.button(label="Browse", c=lambda x: self.browse_action())
        # self.uvSetField = cmds.textFieldGrp(label='Current Uv Set :', text='map1' , cc=lambda x: self.get_text_field(textField=self.uvSetField), w=250)
        self.size_field = cmds.textFieldGrp(label='Current size   :', text=str(self.size), w=250)

        # adding elements to form layout
        cmds.formLayout(form, edit=True, attachForm=[(self.path_field, 'top', 0), (self.browse_btn, 'top', 0), (self.size_field, "top", btn_height),
                                                     (self.path_field, 'left', -60), (self.browse_btn, "left", 340),
                                                     (self.size_field, "left", -60)])

        cmds.setParent('..')
        form = cmds.formLayout(numberOfDivisions=100, h=150)
        text_bake = cmds.text(label=" Bake only on meshes list :  ")
        scroll_w = 300
        scroll_h = 150
        self.scroll_list = cmds.textScrollList(w=scroll_w, h=scroll_h)

        self.add_exclud_btn = cmds.button(label="Add Meshes", c=lambda x: self.update_scroll())
        cmds.formLayout(form, edit=True, attachForm=[(text_bake, "top", 0), (self.scroll_list, 'top', 20), (self.add_exclud_btn, 'top', scroll_h / 2),
                                                     (self.add_exclud_btn, 'left', scroll_w + 10)])

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
        """
        Update text group with new field
        """
        cmds.textFieldGrp(textField, e=True, text=newField)

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

    def create_dir(self, myPath):
        """
        Creates a dir
        """
        if not os.path.exists(myPath):
            try:
                os.mkdir(myPath)
                logging.info("Path have been created. %s" % myPath)
            except Exception as e:
                logging.info(e)

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
            cmds.confirmDialog(m="PLEASE CUSTOM YOUR PATH!!")
            return
        else:
            if self.OUTPATH.endswith('/') is False:
                self.OUTPATH = self.OUTPATH + "/"
            self.TMP_BAKE = self.OUTPATH + "TMP_BAKE/"
            self.OUT_BAKE = self.OUTPATH + "OUT_BAKE/"
            self.OUTPATH_BAKE = self.OUT_BAKE + self.mayaFile + "/"

            self.size = int(self.get_text_field(textField=self.size_field))
            self.meshList = cmds.textScrollList(self.scroll_list, allItems=True, q=True)
            self.setup_scene()

    def create_white_lambert(self):
        """
        Create a lambert with white ramp
        """
        # lamb = cmds.createNode('lambert', name="Mask_Shd")
        lamb = cmds.shadingNode("lambert", name="Mask_Shd", asShader=True)
        ramp = cmds.shadingNode('ramp', name="Mask_Ramp", asTexture=True)
        cmds.setAttr(ramp + ".colorEntryList[0].color", 1, 1, 1, typ="double3")
        cmds.connectAttr(ramp + '.outColor', lamb + '.color', f=True)

    def delete_old_files(self):
        """
        Clean folder after baking
        """
        dirCont = os.listdir(self.TMP_BAKE)
        logging.info('About to remove file inside folder %s' % self.TMP_BAKE)
        if dirCont:
            for img in dirCont:
                logging.info('Deleting this file : {}'.format(img))
                try:
                    os.remove(self.TMP_BAKE + "/" + img)
                except Exception as e:
                    logging.error('{} ! Cant remove file : {}'.format(e, img))

    def mayaCustomBake(self, mesh, node, udim, size, fileFormat, outputFileName):
        """
        Custom bake of maya texture. Must be lambert
        """
        logging.info('Udim en cours {}'.format(udim))
        u = int(str(udim)[-1])
        v = int(str(udim)[-2])
        if u == 0:
            u = 10

        if u <= 9:
            v += 1

        if v == 0:
            v = 1
        if udim > 1100:
            logging.error('Udim are too far !')

        uvRange = [u - 1, u, v - 1, v]
        logging.info('Uv range {}'.format(uvRange))
        cmds.convertSolidTx(node, mesh, rx=size, ry=size, uvRange=uvRange, aa=True, f=True, fileFormat=fileFormat, fileImageName=outputFileName)
        logging.info('Maya Custom Bake is finished for udim %s.' % udim)

    def move_files_from_tmp(self, mesh, udims, renderPass):
        """
        Moves file from TMP folder to OUTPATH folder if they are good
        """
        dirCont = os.listdir(self.TMP_BAKE)
        logging.info('Dir content inside move files {}'.format(dirCont))
        movedFiles = []
        toMove = []
        for fileN in dirCont:
            if mesh in fileN:
                if renderPass.replace(" ", "") in fileN:
                    logging.info('Render pass in file %s %s' % (renderPass.replace(" ", ""), fileN))
                    if udims:
                        for udim in udims:
                            if str(udim) in fileN:
                                toMove.append(fileN)

                    else:
                        toMove.append(fileN)

        logging.info('file about to move {}'.format(toMove))

        if toMove:
            for fileN in toMove:
                udim = fileN.split('.')[-2]
                logging.info('udim %s' % udim)
                src = self.TMP_BAKE + fileN
                dir_dst = self.OUTPATH_BAKE + "/" + udim + "/"
                self.create_dir(dir_dst)
                dst = dir_dst + fileN
                src = (src.replace('/', '\\').replace('\\\\', '\\'))
                src = r"{}".format(src)
                dst = dst.replace('/', "\\")
                dst = (dst.replace('/', '\\').replace('\\\\', '\\'))
                dst = r"{}".format(dst)
                logging.info('SRC %s' % src)
                logging.info('DST %s' % dst)

                shutil.copy2("\\\\?\\" + src, "\\\\?\\" + dst)

                if os.path.isfile(dst):
                    logging.info('File has been moved from %s to %s.' % (src, dst))
                    movedFiles.append(dst)

                else:
                    logging.error('File has not been copied from %s to %s.' % (src, dst))

        return movedFiles

    def reinit_fresnel(self, shader):
        """
        Set perpendicular color to black in fresnel of shader
        """
        fresnels = read_shaders.list_nodeType_of_shader(shader=shader, nodeType="RedshiftFresnel")
        if fresnels:
            for fresnel in fresnels:
                cmds.setAttr('{}.{}'.format(fresnel, "perp_color"), lock=0)
                cmds.setAttr(fresnel + ".perp_color", 0, 0, 0, type="double3")
            logging.info('Fresnels nodes have been reinit to black')

    def dupplicate_shader(self, shader, mesh, meshNameClean):
        """
        Dupplicat shader and assign it to mesh
        """
        duppName = "BAKE_" + meshNameClean + "_" + shader
        # authShdrs = ["RedshiftMaterialBlender", "RedshiftSubSurfaceScatter", "RedshiftMaterial"]
        authShdrs = ["RedshiftSubSurfaceScatter", "RedshiftMaterial"]

        cmds.select(mesh, r=True)
        # if current shader is in authorized
        if cmds.objExists(duppName) is False:
            if cmds.objectType(shader) in authShdrs:
                cmds.duplicate(shader, n=duppName)
                cmds.hyperShade(assign=duppName)
                logging.info('Shader %s has been duplicated' % shader)

            else:
                cmds.shadingNode("RedshiftMaterial", n=duppName, asShader=True)
                # enleve la reflection
                cmds.setAttr(duppName + ".refl_weight", 0)
                cmds.select(mesh, r=True)
                cmds.hyperShade(assign=duppName)
                logging.info('Shader %s has been recreated from scratch' % shader)

        else:
            cmds.hyperShade(assign=duppName)

        cmds.select(clear=1)
        return duppName

    def setup_new_shNewtwork(self, shader, mesh, txtFile, renderPass):
        # FIXME: corresp dict is not used!
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
        # FIXME: format issues!
        baseName = "ExtraName_001_".format(assetName=self.assetName, variationName=self.variationName, shader=shader, Pass=renderPass)

        fileName = baseName + "File_" + "Dif"
        newFile = cmds.shadingNode("file", n=fileName, asTexture=True)
        pl2dTx = cmds.shadingNode("place2dTexture", n=baseName + "P2DT_" + "Dif", asUtility=True)

        attrb = [
            'uvCoord', 'vertexUvOne', 'vertexUvTwo', 'vertexUvThree', 'vertexCameraOne', 'coverage', 'translateFrame',
            'rotateFrame', 'mirrorU', 'mirrorV', 'stagger', 'wrapU', 'wrapV', 'repeatUV', 'offset', - 'rotateUV', 'outUVu',
            'outUVv', 'outUvFilterSize'
        ]
        for att in attrb:
            try:
                cmds.connectAttr(pl2dTx + "." + att, newFile + "." + att)
            except Exception as e:
                logging.info('{} // Cannot connect {} attr {} to {} '.format(str(e), pl2dTx, att, newFile))

        cmds.setAttr("{}.fileTextureName".format(newFile), txtFile, type="string")
        cmds.setAttr("{}.colorSpace".format(newFile), "Raw", type='string')

        if "UDIM" in txtFile:
            cmds.setAttr("{}.uvTilingMode".format(newFile), 3)

        logging.info("New file created {}".format(newFile))

        try:
            new_shN = cmds.file(self.ARBO, i=True, uns=False, returnNewNodes=True)
        except Exception as e:
            logging.error("Error wile importing arborescence!!  {}".format(self.ARBO))

        logging.info("New arborescence imported {}".format(new_shN))

        if cmds.objectType(shader) == "RedshiftMaterialBlender":
            outAttr = "baseColor"
            logging.warning('Warning!! A blend color is found. Please correct it later to find the right shader to assign!')

        elif cmds.objectType(shader) == "RedshiftSubSurfaceScatter":
            outAttr = "sub_surface_color"

        else:
            outAttr = "diffuse_color"

        logging.info('Shader : %s Out Attr %s' % (shader, outAttr))
        logging.info('new shader %s' % new_shN)

        for node in new_shN:
            nodeType = cmds.objectType(node)
            if nodeType == "RedshiftFresnel":
                logging.info('NODE : %s' % node)
                try:
                    cmds.connectAttr(fileName + ".outColor", node + ".facing_color")

                except Exception as e:
                    logging.warning("Cannot connect file name! to %s %s" % (fileName + ".outColor", node + ".facing_color"))

                try:
                    cmds.connectAttr(node + ".outColor", shader + ".%s" % outAttr)

                except Exception as e:
                    logging.warning("Cannot connect %s outcolor to %s %s" % (node, shader, outAttr))

            elif nodeType == "remapHsv":
                try:
                    cmds.connectAttr(fileName + ".outColor", node + ".color")

                except Exception as e:
                    logging.warning('Cannot connect Remap HSV %s to %s . color' % (fileName, node))

            # if nodeType in corresp:
            #     typeNom = corresp[nodeType]
            #     try:
            #         cmds.rename(node, baseName + typeNom)
            #     except Exception as e:
            #         logging.warning('Cannot rename %s to %s ' % (node, baseName + typeNom))

            # else:
            #     try:
            #         cmds.rename(node, baseName + "_" + nodeType)

            #     except Exception as e:
            #         logging.warning('Cannot rename %s to %s ' % (node, baseName + "_" + nodeType))

        logging.info("Importing new shading and connecting to %s done" % shader)

    def launch_baking(self, mesh, shader, renderPass):
        """
        Launch bake on mesh
        """
        cmds.select(cl=True)
        cmds.select(mesh, r=True)

        # get rid of fresnel
        logging.info('Reinit fresnel')
        self.reinit_fresnel(shader=shader)

        meshNameClean = mesh.replace('|', '_')

        filesOfShdr = read_shaders.list_nodeType_of_shader(shader=shader, nodeType="file")
        passType = "Col"
        correctPass = []
        if filesOfShdr:
            for fileName in filesOfShdr:
                if passType.lower() in fileName.lower():
                    correctPass.append(fileName)
        else:
            logging.error('No color map found!')

        if len(correctPass) == 0:
            logging.error('No correct pass found {}'.format(filesOfShdr))

        elif len(correctPass) > 1:
            logging.warning('More than one file of %s' % passType)

        elif len(correctPass) < 1:
            correctPass = correctPass[0]

        logging.info('File found : %s' % str(correctPass))

        udims = read_nodes.get_udims_list(mesh)
        logging.info('Udim found : %s' % str(udims))

        # setup names
        baseFileName = self.TMP_BAKE + "{Object}_{Padding}_{File}"
        outFileName = baseFileName.format(assetName=self.assetName, variationName=self.variationName, ShaderName=shader,
                                          Object=meshNameClean, Padding="001", File="File")

        logging.info('File output : %s' % str(outFileName))

        # clean existing aovs et create diffuse
        delete_scene.clean_aovs()
        update_scene.setup_render_settings(fileName=outFileName, aovList=[renderPass], fileFormat="png")

        # MAYA BAKE FOR MASK
        cmds.select(mesh, r=True)

        for udim in udims:
            OUTPATH_BAKE_MASK = self.OUTPATH_BAKE + str(udim) + "/"
            logging.info('Outpath maya %s' % OUTPATH_BAKE_MASK)
            self.create_dir(OUTPATH_BAKE_MASK)
            baseFileName = OUTPATH_BAKE_MASK + "{Object}_{Padding}_{File}"
            fileFormat = "png"
            outputMask = baseFileName.format(assetName=self.assetName, variationName=self.variationName, ShaderName=shader,
                                             Object=meshNameClean, Padding="001", File="Mask") + "_" + str(udim) + "." + fileFormat
            logging.info("Output mask : %s" % outputMask)
            cmds.hyperShade(assign="Mask_Shd")
            logging.info('Launching maya baking..')
            self.mayaCustomBake(mesh=mesh, node="Mask_Ramp", udim=udim, size=self.size, fileFormat=fileFormat, outputFileName=outputMask)

        cmds.select(mesh, r=True)
        cmds.hyperShade(assign=shader)

        # REFSHIFT BAKE
        cmds.select(cl=True)
        cmds.select(mesh, r=True)
        logging.info('Launching bake inside launch...')
        update_scene.redshiftCustomBake(w=self.size, h=self.size, launchBake=True)

        cmds.select(cl=True)

        # remove inside the folder the residual
        movedFiles = self.move_files_from_tmp(meshNameClean, udims, renderPass)
        logging.info('Moved files : {}'.format(movedFiles))

        if len(movedFiles) >= 1:
            movedFiles = movedFiles[0]

        elif len(movedFiles) == 0:
            logging.error('No files baked found')

        logging.info('File is %s' % movedFiles)

        duppShader = self.dupplicate_shader(shader=shader, mesh=mesh, meshNameClean=meshNameClean)
        logging.info("Importing new shading and connecting to %s " % duppShader)

        self.setup_new_shNewtwork(shader=duppShader, mesh=mesh, txtFile=movedFiles, renderPass="Dif")

        logging.info('Clean done.')

    def setup_scene(self):
        """
        Setup scene to bake and remove files.
        List all meshes, launch bake and delete temp files of bake.
        """
        self.create_dir(self.TMP_BAKE)
        self.create_dir(self.OUT_BAKE)
        self.create_dir(self.OUTPATH_BAKE)

        renderPass = "Diffuse Filter"
        if not self.meshList:
            all_meshes = read_nodes.list_all_meshes()
        else:
            all_meshes = self.meshList

        logging.info("all meshes {}".format(all_meshes))

        # create white lambert for baking mask
        self.create_white_lambert()

        # launch bake
        for mesh in all_meshes:
            if cmds.objExists(mesh):
                longnameMsh = mesh
                # combine and separate
                logging.info("Launching procedure for Mesh %s" % mesh)
                update_nodes.combineSeparate(mesh)

                shader = read_shaders.get_mesh_shader(longnameMsh)

                # isolate mesh
                update_nodes.isolate_object(myObject=longnameMsh, visibility=False)
                mesh = cmds.ls(mesh, sn=True)[0]

                # baking
                logging.info('Launching bake for: %s' % mesh)

                if shader:
                    self.launch_baking(mesh=mesh, shader=shader, renderPass=renderPass)
                else:
                    logging.error('No shader found on mesh ! %s' % mesh)

                logging.info('Bake for: %s finished' % mesh)
                update_nodes.isolate_object(myObject=longnameMsh, visibility=True)

            else:
                logging.info('The mesh %s dosnt exist' % mesh)

        update_nodes.isolate_object(myObject=longnameMsh, visibility=True)
        self.delete_old_files()
        cmds.delete(['Mask_Shd', "Mask_Ramp"])

        logging.info('*' * 30 + "BAKING DONE FOR ALL MESHES" + "*" * 30)

    def open_log(self):
        """
        Open log file
        """
        logging.info("log path... {}".format(self.log_file))
        if os.path.isfile(self.log_file):
            subprocess.Popen(['notepad', self.log_file])
        else:
            cmds.confirmDialog(title="Warning", m="The log {} doesnt exists! Did you launch?".format(self.log_file))

    def launch_help(self):
        """
        Launch hackmd page for documentation
        """
        url = 'https://hackmd.io/8i-L_K2SRVq65z1z5MFOJw?view'
        webbrowser.open_new(url)


if __name__ == "__main__":
    BakingRedshift()
    logging.shutdown()
